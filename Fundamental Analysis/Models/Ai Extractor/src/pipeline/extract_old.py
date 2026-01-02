"""Main extraction pipeline module - processes entire PDF for all fields."""

from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from src.pdf.loader import PDFLoader
from src.pdf.ocr import OCRProcessor
from src.pdf.page_locator import PageLocator
from src.pdf.table_extractor import TableExtractor
from src.extraction.currency_detector import detect_currency_and_unit
from src.extraction.period_detector import detect_period
from src.extraction.key_value import KeyValueExtractor
from src.extraction.normalizer import ValueNormalizer
from src.validation.accounting_rules import AccountingValidator
from src.validation.confidence_score import ConfidenceScorer
from src.storage.save_json import save_extraction_result
from config.target_schema_bank import TARGET_FIELDS, STATEMENT_FIELDS, MANDATORY_SECTIONS
from src.utils.logger import get_logger
from src.utils.helpers import load_config, fuzzy_match

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
            
            # Step 5: Locate statement pages and extract tables (prefer 'Group' columns)
            logger.info("="*80)
            logger.info("LOCATING STATEMENT PAGES AND EXTRACTING TABLES (GROUP COLUMNS PREFERRED)")
            logger.info("="*80)

            page_locator = PageLocator(pdf_loader)
            sections_pages = page_locator.locate_financial_statements()
            table_extractor = TableExtractor(self.config)
            key_value_extractor = KeyValueExtractor(self.config)

            # Mapping between page_locator section keys and TARGET_FIELDS keys
            section_map = {
                'income_statement': 'Income_Statement',
                'balance_sheet': 'Financial Position Statement',
                'cash_flow': 'Cash Flow Statement'
            }

            results = {}
            total_fields = 0

            # Process each known section and prefer table-based extraction first
            for sec_key, schema_key in section_map.items():
                target_fields = TARGET_FIELDS.get(schema_key, [])
                if not target_fields:
                    continue

                total_fields += len(target_fields)
                logger.info(f"\n📋 Processing section: {schema_key} (pages: {sections_pages.get(sec_key)})")

                # Prepare per-year container for this section
                section_output: Dict[str, Dict[str, Any]] = {}

                pages = sections_pages.get(sec_key, list(range(len(text))))

                # Extract tables from the located pages
                tables_by_page = table_extractor.extract_tables_from_pages(pdf_path, pages)

                # For each table, extract multi-column values (prefer Group columns)
                for page_num, tables in tables_by_page.items():
                    for df in tables:
                        table_items = table_extractor.extract_multi_column_values(df)
                        # table_items: {item_name: {year_label: value}}
                        for item_name, year_map in table_items.items():
                            # Try to match item_name to one of the target fields
                            matched = fuzzy_match(item_name, target_fields, threshold=80)
                            if matched:
                                for year_label, value in year_map.items():
                                    if year_label not in section_output:
                                        section_output[year_label] = {}
                                    # If field not already set for that year, set it
                                    section_output[year_label].setdefault(matched, value)

                # Fallback: use text-based key-value extraction for any missing fields
                # (this does not guarantee per-year values; it tries to populate missing fields)
                missing = []
                for field in target_fields:
                    found_any = any(field in yr_map for yr_map in section_output.values())
                    if not found_any:
                        missing.append(field)

                if missing:
                    logger.info(f"Fields missing from tables for {schema_key}: {len(missing)}. Using text fallback.")
                    section_text = page_locator.get_section_text(sec_key)
                    fallback_data = key_value_extractor.extract(section_text or full_text, schema_key, None)
                    # fallback_data is flat {field: value}; attach to a generic 'unspecified' year if no years
                    default_year = 'unspecified'
                    for f, v in fallback_data.items():
                        if f in missing and v is not None:
                            section_output.setdefault(default_year, {})[f] = v

                results[schema_key] = section_output
                found_count = sum(len(yr) for yr in section_output.values())
                logger.info(f"   ✓ Found {found_count}/{len(target_fields)} values for {schema_key}")
            
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
    
    def _extract_from_tables(
        self,
        all_tables: Dict[int, List],
        statement_section: str,
        statement_fields: List[str]
    ) -> Dict[str, Any]:
        """
        Extract data from tables for a specific statement section.
        
        Args:
            all_tables: Dictionary of page numbers to tables
            statement_section: Statement section name
            statement_fields: List of field names to extract
        
        Returns:
            Nested dictionary with Bank/Group and Year1/Year2 data
        """
        from src.pdf.table_extractor import TableExtractor
        
        result = {
            'Bank': {'Year1': {}, 'Year2': {}},
            'Group': {'Year1': {}, 'Year2': {}}
        }
        
        try:
            table_extractor = TableExtractor()
            
            # Find tables related to this statement section
            for page_num, tables in all_tables.items():
                for table_df in tables:
                    # Check if table is relevant to this section
                    table_type = table_extractor.identify_financial_table(table_df)
                    
                    # Map section names to table types
                    section_map = {
                        'Income_Statement': 'income_statement',
                        'Financial Position Statement': 'balance_sheet',
                        'Cash Flow Statement': 'cash_flow'
                    }
                    
                    if table_type == section_map.get(statement_section):
                        # Extract multi-column data (Bank Year1, Bank Year2, Group Year1, Group Year2)
                        multi_col_data = table_extractor.extract_multi_column_values(table_df)
                        
                        if multi_col_data:
                            # Parse the multi-column structure
                            # Columns typically: Field Name | Bank Y1 | Bank Y2 | Group Y1 | Group Y2
                            for field_name, year_values in multi_col_data.items():
                                # Match field name to schema fields
                                matched_field = self._match_field_name(field_name, statement_fields)
                                
                                if matched_field:
                                    # Distribute values to appropriate entity/year
                                    for col_label, value in year_values.items():
                                        col_lower = col_label.lower()
                                        
                                        # Determine entity and year from column label
                                        if 'bank' in col_lower or 'company' in col_lower:
                                            if '2024' in col_label or 'year1' in col_lower or 'current' in col_lower:
                                                result['Bank']['Year1'][matched_field] = value
                                            elif '2023' in col_label or 'year2' in col_lower or 'previous' in col_lower:
                                                result['Bank']['Year2'][matched_field] = value
                                        elif 'group' in col_lower or 'consolidated' in col_lower:
                                            if '2024' in col_label or 'year1' in col_lower or 'current' in col_lower:
                                                result['Group']['Year1'][matched_field] = value
                                            elif '2023' in col_label or 'year2' in col_lower or 'previous' in col_lower:
                                                result['Group']['Year2'][matched_field] = value
                                        else:
                                            # Default to Bank Year1 if unclear
                                            result['Bank']['Year1'][matched_field] = value
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting from tables: {str(e)}")
            return result
    
    def _match_field_name(self, extracted_name: str, schema_fields: List[str]) -> Optional[str]:
        """
        Match extracted field name to schema field using fuzzy matching.
        
        Args:
            extracted_name: Field name from PDF
            schema_fields: List of schema field names
        
        Returns:
            Matched schema field name or None
        """
        from config.term_mapping_bank import TERM_MAPPING
        
        extracted_lower = extracted_name.lower().strip()
        
        # Direct match
        for schema_field in schema_fields:
            if schema_field.lower() == extracted_lower:
                return schema_field
        
        # Term mapping match
        for schema_field in schema_fields:
            variations = TERM_MAPPING.get(schema_field, [])
            for variation in variations:
                if variation.lower() == extracted_lower:
                    return schema_field
        
        # Fuzzy match (contains)
        for schema_field in schema_fields:
            if extracted_lower in schema_field.lower() or schema_field.lower() in extracted_lower:
                if len(extracted_lower) > 5:  # Avoid short false matches
                    return schema_field
        
        return None
    
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
    
    def strict_extract_from_pdf(self, pdf_path: str, company_name: Optional[str] = None) -> Dict[str, Any]:
        """Strict extraction per ARCHITECTURE.md: Bank/Group separation, Year1/Year2, dual JSON output."""
        import pandas as pd
        import pdfplumber
        from src.extraction.normalizer import StrictFinancialExtractor
        from src.storage.save_json import save_dual_extraction_result
        
        logger.info(f"STRICT MODE: {pdf_path}")
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            return {'success': False, 'error': f'PDF not found: {pdf_path}'}
        
        try:
            # Step 1: Load PDF
            logger.info("Step 1/7: Loading PDF")
            pdf_loader = PDFLoader(str(pdf_path))
            pdf_info = pdf_loader.get_pdf_info()
            company_name = company_name or pdf_path.stem
            
            # Step 2: Locate 3 mandatory sections
            logger.info("Step 2/7: Locating mandatory sections")
            try:
                page_locator = PageLocator(pdf_loader)
                all_sections = page_locator.locate_financial_statements()
            except:
                all_sections = {'income_statement': list(range(40, 65)), 'balance_sheet': list(range(65, 90)), 'cash_flow': list(range(90, 115))}
            
            sections_pages = {
                'Income_Statement': all_sections.get('income_statement', []),
                'Financial Position Statement': all_sections.get('balance_sheet', []),
                'Cash Flow Statement': all_sections.get('cash_flow', [])
            }
            
            # Step 3: Extract tables (limit to 5 pages per section for performance)
            logger.info("Step 3/7: Extracting tables")
            sections_data = {}
            for stmt, pages in sections_pages.items():
                tables = []
                for page_num in pages[:5]:
                    try:
                        with pdfplumber.open(str(pdf_path)) as pdf:
                            if 0 <= page_num < len(pdf.pages):
                                for tbl in (pdf.pages[page_num].extract_tables() or []):
                                    if tbl and len(tbl) > 1:
                                        df = pd.DataFrame(tbl[1:], columns=tbl[0]).dropna(how='all').dropna(axis=1, how='all')
                                        if not df.empty:
                                            tables.append(df)
                    except Exception as e:
                        logger.warning(f"Page {page_num} failed: {e}")
                sections_data[stmt] = tables
                logger.info(f"{stmt}: {len(tables)} tables")
            
            # Step 4-5: Metadata + Strict Extraction
            logger.info("Step 4-5/7: Metadata + Strict extraction")
            currency_info = detect_currency_and_unit(pdf_loader)
            period_info = detect_period(pdf_loader)
            
            extractor = StrictFinancialExtractor(fuzzy_threshold=85.0)
            bank_data, group_data = extractor.extract(sections_data)
            
            # Step 6-7: Build outputs + Save
            logger.info("Step 6-7/7: Saving Bank and Group JSONs")
            metadata = {
                'company_name': company_name,
                'source_file': str(pdf_path),
                'extraction_date': datetime.now().isoformat(),
                'currency': currency_info.get('currency', 'Unknown'),
                'unit': currency_info.get('unit', 'Unknown'),
                'period': period_info,
                'extraction_type': 'strict'
            }
            
            output_dir = Path("data/processed/extracted_json")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            bank_file = output_dir / f"{company_name.replace(' ', '_')}_Bank_{ts}.json"
            group_file = output_dir / f"{company_name.replace(' ', '_')}_Group_{ts}.json"
            
            bank_result = {'metadata': {**metadata, 'entity': 'Bank'}, 'financial_data': bank_data}
            group_result = {'metadata': {**metadata, 'entity': 'Group'}, 'financial_data': group_data}
            
            save_dual_extraction_result(bank_result, group_result, str(bank_file), str(group_file))
            
            def count_filled(d):
                return sum(1 if not isinstance(v, dict) and v is not None else count_filled(v) for v in d.values())
            
            return {
                'success': True,
                'bank_file': str(bank_file),
                'group_file': str(group_file),
                'metadata': metadata,
                'statistics': {'bank_fields_extracted': count_filled(bank_data), 'group_fields_extracted': count_filled(group_data)}
            }
        except Exception as e:
            logger.error(f"Strict extraction failed: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
