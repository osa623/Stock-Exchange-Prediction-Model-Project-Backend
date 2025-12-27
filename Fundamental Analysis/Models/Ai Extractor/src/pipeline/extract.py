"""Main extraction pipeline module - processes entire PDF for all fields."""

from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from src.pdf.loader import PDFLoader
from src.pdf.ocr import OCRProcessor
from src.extraction.currency_detector import detect_currency_and_unit
from src.extraction.period_detector import detect_period
from src.extraction.key_value import KeyValueExtractor
from src.extraction.normalizer import ValueNormalizer
from src.validation.accounting_rules import AccountingValidator
from src.validation.confidence_score import ConfidenceScorer
from src.storage.save_json import save_extraction_result
from config.target_schema_bank import TARGET_FIELDS
from src.utils.logger import get_logger
from src.utils.helpers import load_config

logger = get_logger(__name__)


class ExtractionPipeline:
    """Main extraction pipeline - processes entire PDF for all schema fields."""
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        """
        Initialize extraction pipeline.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = load_config(config_path)
        
        # Initialize components
        self.ocr_processor = OCRProcessor()
        
        logger.info("Extraction pipeline initialized")
        logger.info(f"Will extract ALL fields from target_schema_bank.py")
    
    def extract_from_pdf(
        self, 
        pdf_path: str, 
        company_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract ALL financial data from entire PDF.
        
        Args:
            pdf_path: Path to PDF file
            company_name: Company name (optional)
        
        Returns:
            Extracted data dictionary with all fields
        """
        logger.info(f"Starting extraction for: {pdf_path}")
        logger.info(f"Processing ENTIRE PDF to find all {sum(len(fields) for fields in TARGET_FIELDS.values())} schema fields")
        
        try:
            # Step 1: Load PDF
            pdf_loader = PDFLoader(pdf_path)
            pdf_info = pdf_loader.get_pdf_info()
            
            if not company_name:
                company_name = Path(pdf_path).stem
            
            logger.info(f"Loaded PDF: {pdf_info['total_pages']} pages")
            
            # Step 2: Extract ALL text from all pages
            pages_text_dict = pdf_loader.extract_pages_text(0, None)
            text = [pages_text_dict[i] for i in sorted(pages_text_dict.keys())]
            
            logger.info(f"Extracted text from {len(text)} pages")
            
            # Step 2: Check if OCR is needed
            needs_ocr = self.ocr_processor.is_image_based_pdf(pdf_path)
            if needs_ocr:
                logger.warning("PDF appears to be image-based - OCR may be needed for better extraction")
            
            # Step 3: Extract ALL text from PDF (process entire document)
            logger.info("Processing entire PDF to extract all financial data")
            full_text = "\n\n--- PAGE BREAK ---\n\n".join(text)
            
            # Step 4: Extract metadata (currency, period, etc.)
            # Get text from first few pages for metadata
            sample_text = ""
            for i in range(min(5, len(text))):
                sample_text += text[i] + "\n"
            
            currency, unit = detect_currency_and_unit(sample_text)
            period_info = detect_period(sample_text)
            
            # Create currency info dict
            currency_info = {
                'currency': currency or 'LKR',
                'unit': unit or 'thousands'
            }
            
            # Create periods list
            periods = []
            if period_info:
                periods.append(period_info)
            
            metadata = {
                'entity_name': company_name,
                'entity_type': self.config.get('entity', {}).get('type', 'bank'),
                'currency': currency_info,
                'periods': periods,
                'extraction_date': datetime.now().isoformat(),
                'total_pages': len(text),
                'source_file': Path(pdf_path).name
            }
            
            logger.info(f"Metadata: Currency={currency_info['currency']}, "
                       f"Unit={currency_info['unit']}, Periods={len(periods)}, Pages={len(text)}")
            
            # Step 5: Extract ALL fields from target_schema_bank across entire PDF
            logger.info("="*80)
            logger.info("EXTRACTING ALL FIELDS FROM ENTIRE PDF")
            logger.info("="*80)
            
            results = {}
            key_value_extractor = KeyValueExtractor(self.config)
            
            total_fields = 0
            # Process each section's fields against the entire PDF text
            for section_name, target_fields in TARGET_FIELDS.items():
                if not target_fields:
                    logger.warning(f"No target fields defined for {section_name}")
                    continue
                
                total_fields += len(target_fields)
                logger.info(f"\n📋 Extracting {len(target_fields)} fields for: {section_name}")
                
                # Extract values from entire PDF (pass section_name as statement_type)
                extracted_values = key_value_extractor.extract(
                    full_text,
                    section_name,  # statement_type
                    None  # period
                )
                
                results[section_name] = extracted_values
                found_count = len([v for v in extracted_values.values() if v is not None])
                logger.info(f"   ✓ Found {found_count}/{len(target_fields)} values for {section_name}")
            
            logger.info(f"\n{'='*80}")
            logger.info(f"EXTRACTION COMPLETE: Processed {total_fields} total fields")
            logger.info(f"{'='*80}\n")
            
            # Step 6: Validate extracted data
            validator = AccountingValidator()
            validation_results = validator.validate_all(results)
            
            # Step 7: Calculate confidence scores
            scorer = ConfidenceScorer()
            # Create empty metadata dict for each section
            all_metadata = {section: {} for section in results.keys()}
            confidence_scores = scorer.calculate_overall_confidence(
                results,
                all_metadata,
                validation_results
            )
            confidence_score = confidence_scores.get('overall', 0.0)
            
            # Step 8: Normalize values
            normalizer = ValueNormalizer(
                target_currency=currency_info['currency'],
                target_unit=currency_info['unit']
            )
            for section in results:
                results[section] = normalizer.normalize_dataset(
                    results[section],
                    currency_info['unit']
                )
            
            # Step 9: Prepare final output with ALL fields
            total_extracted = sum(len([v for v in section.values() if v is not None]) 
                                for section in results.values())
            
            output = {
                'metadata': metadata,
                'financial_statements': results,
                'validation': validation_results,
                'confidence_score': confidence_score,
                'processing_info': {
                    'total_pages': len(text),
                    'total_fields_in_schema': total_fields,
                    'total_fields_extracted': total_extracted,
                    'extraction_rate': f"{(total_extracted/total_fields*100):.1f}%",
                    'sections_in_schema': list(results.keys()),
                    'ocr_used': needs_ocr,
                    'extraction_method': self.config.get('provider', 'gemini')
                }
            }
            
            # Step 10: Save to JSON
            output_path = save_extraction_result(
                results,
                {
                    'entity_name': company_name,
                    'currency': currency_info,
                    'periods': periods,
                    'validation': validation_results,
                    'confidence_score': confidence_score,
                    'total_pages': len(text),
                    'total_fields_in_schema': total_fields,
                    'total_fields_extracted': total_extracted,
                    'extraction_rate': output['processing_info']['extraction_rate']
                },
                self.config.get('paths', {}).get('processed_json', 'data/processed/extracted_json'),
                company_name
            )
            
            logger.info(f"✓ Results saved to: {output_path}")
            logger.info(f"✓ Extracted {total_extracted}/{total_fields} fields ({output['processing_info']['extraction_rate']})")
            
            return output
            
        except Exception as e:
            logger.error(f"Error in extraction pipeline: {str(e)}", exc_info=True)
            return {
                'error': str(e),
                'traceback': str(e)
            }
    
    def extract_batch(self, pdf_directory: str) -> list:
        """
        Extract data from multiple PDFs.
        
        Args:
            pdf_directory: Directory containing PDF files
        
        Returns:
            List of extraction results
        """
        pdf_dir = Path(pdf_directory)
        pdf_files = list(pdf_dir.glob("*.pdf"))
        
        logger.info(f"Found {len(pdf_files)} PDF files in {pdf_directory}")
        
        results = []
        for idx, pdf_file in enumerate(pdf_files, 1):
            logger.info(f"\n{'='*80}")
            logger.info(f"Processing {idx}/{len(pdf_files)}: {pdf_file.name}")
            logger.info(f"{'='*80}")
            
            result = self.extract_from_pdf(str(pdf_file))
            results.append(result)
        
        logger.info(f"\n{'='*80}")
        logger.info(f"BATCH EXTRACTION COMPLETE: {len(results)} files processed")
        logger.info(f"{'='*80}")
        
        return results
