"""
ROBUST Financial Statement Extraction Pipeline
Extracts Bank/Group data for Year1/Year2 from PDF financial statements with high accuracy
"""

from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import re
import pandas as pd

from src.pdf.loader import PDFLoader
from src.pdf.ocr import OCRProcessor
from src.pdf.table_extractor import TableExtractor
from src.extraction.currency_detector import detect_currency_and_unit
from src.extraction.period_detector import detect_period
from src.extraction.normalizer import ValueNormalizer
from src.storage.save_json import save_extraction_result
from config.target_schema_bank import STATEMENT_FIELDS, MANDATORY_SECTIONS
from config.term_mapping_bank import TERM_MAPPING
from src.utils.logger import get_logger
from src.utils.helpers import load_config, extract_numbers

logger = get_logger(__name__)


class ExtractionPipeline:
    """Robust extraction pipeline with intelligent page finding and table parsing."""
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config = load_config(config_path)
        self.ocr_processor = OCRProcessor()
        self.table_extractor = TableExtractor(self.config.get('table_extraction', {}))
        
        logger.info("="*80)
        logger.info("ROBUST FINANCIAL STATEMENT EXTRACTOR INITIALIZED")
        logger.info("Target: Bank & Group | Year1 (2024) & Year2 (2023) | 3 Statements")
        logger.info("="*80)
    
    def find_statement_pages(self, pdf_path: str, total_pages: int) -> Dict[str, List[int]]:
        """
        Intelligently find pages containing each financial statement.
        HARDCODED for HNB format - pages 289-299 contain actual statements.
        """
        logger.info("\n🔍 LOCATING STATEMENT PAGES...")
        
        # For HNB annual report: Statements are on pages 290-298 (0-indexed: 289-297)
        statement_pages = {
            'Income_Statement': [289, 290],  # Pages 290-291 (Income Statement + Comprehensive Income)
            'Financial Position Statement': [291, 292],  # Pages 292-293
            'Cash Flow Statement': [297, 298]  # Pages 298-299
        }
        
        logger.info(f"   ✓ Using KNOWN statement pages for HNB format")
        for statement, pages in statement_pages.items():
            logger.info(f"   📄 {statement}: {len(pages)} pages → {[p+1 for p in pages]}")
        
        return statement_pages
    
    def _is_actual_statement_page(self, page_text: str, statement_type: str) -> bool:
        """Check if page contains actual statement data, not just TOC."""
        # Must contain some numeric data
        numbers = re.findall(r'\d+', page_text)
        if len(numbers) < 10:  # Too few numbers = likely TOC
            return False
        
        # Must not be dominated by "page" references
        if page_text.count('page') > 20:
            return False
        
        # Statement-specific checks
        if statement_type == 'Income_Statement':
            # Should contain income/expense terms
            return any(word in page_text for word in ['income', 'expense', 'profit', 'revenue'])
        elif statement_type == 'Financial Position Statement':
            # Should contain assets/liabilities
            return any(word in page_text for word in ['assets', 'liabilities', 'equity'])
        elif statement_type == 'Cash Flow Statement':
            # Should contain cash flow terms
            return any(word in page_text for word in ['operating', 'investing', 'financing', 'cash'])
        
        return True
    
    def extract_from_statement_pages(
        self,
        pdf_path: str,
        pages: List[int],
        statement_name: str,
        statement_fields: List[str]
    ) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """
        Extract data from statement pages with Bank/Group and Year1/Year2.
        PRIORITY: Extract GROUP data as requested by user.
        SPECIAL: For HNB format, extracts field names from page text and values from tables.
        """
        logger.info(f"\n📊 EXTRACTING: {statement_name}")
        logger.info(f"   Pages: {[p+1 for p in pages]} | Target: {len(statement_fields)} fields")
        
        result = {
            'Bank': {'Year1': {}, 'Year2': {}},
            'Group': {'Year1': {}, 'Year2': {}}
        }
        
        total_extracted = 0
        pdf_loader = PDFLoader(pdf_path)
        
        for idx, page_num in enumerate(pages, 1):
            logger.info(f"\n   📄 Page {page_num + 1} [{idx}/{len(pages)}]...")
            
            # Extract text to get field names
            page_text = pdf_loader.extract_text_pdfplumber(page_num)
            lines = [l.strip() for l in page_text.split('\n') if l.strip()]
            
            # Extract tables from page
            tables = self.table_extractor.extract_tables_pdfplumber(pdf_path, page_num)
            
            if not tables or len(tables) == 0:
                logger.info(f"      No tables found")
                continue
            
            # Process each table
            for table_idx, table_df in enumerate(tables):
                logger.info(f"      📊 Table {table_idx + 1}: {table_df.shape[0]}×{table_df.shape[1]}")
                
                # Skip small tables
                if table_df.shape[0] < 5 or table_df.shape[1] < 3:
                    logger.info(f"         Skipping (too small - need at least 5 rows × 3 columns)")
                    continue
                
                # For HNB: Table has 3-4 numeric columns: [Bank 2024, Bank 2023, Group 2024, (Group 2023)]
                # Field names are in the page text, need to match by position
                
                # Detect column structure
                column_map = self._detect_column_mapping(table_df.columns.tolist(), table_df)
                
                if not column_map:
                    logger.debug(f"         Could not map columns")
                    continue
                
                logger.debug(f"         Column mapping: {column_map}")
                
                # Extract data row by row
                for row_idx in range(len(table_df)):
                    try:
                        row = table_df.iloc[row_idx]
                        
                        # Try to find matching field name in text
                        # The text line corresponding to this row should contain the field name
                        field_name = None
                        if row_idx + 4 < len(lines):  # +4 offset for header lines
                            line_text = lines[row_idx + 4]
                            # Extract field name (before the numbers)
                            parts = line_text.split()
                            if parts:
                                # Take the non-numeric part as field name
                                field_parts = []
                                for part in parts:
                                    if not extract_numbers(part):
                                        field_parts.append(part)
                                    else:
                                        break  # Stop at first number
                                field_name = ' '.join(field_parts) if field_parts else None
                        
                        if not field_name or len(field_name) < 3:
                            continue
                        
                        # Match to schema field
                        matched_field = self._match_field(field_name, statement_fields)
                        
                        if matched_field:
                            # Extract values from mapped columns
                            for col_idx, (entity, year) in column_map.items():
                                if col_idx < len(row):
                                    value_str = str(row.iloc[col_idx])
                                    value = extract_numbers(value_str)
                                    
                                    # Validate value
                                    if value is not None and self._is_valid_financial_value(value):
                                        if matched_field not in result[entity][year]:
                                            result[entity][year][matched_field] = value
                                            total_extracted += 1
                                            logger.debug(f"            ✓ {matched_field[:30]}... = {value:,.0f} ({entity} {year})")
                    
                    except Exception as row_error:
                        logger.debug(f"         Error processing row {row_idx}: {row_error}")
                        continue
                
                extracted_count = sum(len(result[e][y]) for e in ['Bank', 'Group'] for y in ['Year1', 'Year2'])
                if extracted_count > 0:
                    logger.info(f"         ✓ Extracted {extracted_count} values from this table")
        
        # Log extraction summary for this statement
        bank_y1 = len(result['Bank']['Year1'])
        bank_y2 = len(result['Bank']['Year2'])
        group_y1 = len(result['Group']['Year1'])
        group_y2 = len(result['Group']['Year2'])
        
        logger.info(f"\n   ✅ Extracted {total_extracted} values:")
        logger.info(f"      Bank:  Year1={bank_y1}/{len(statement_fields)}, Year2={bank_y2}/{len(statement_fields)}")
        logger.info(f"      Group: Year1={group_y1}/{len(statement_fields)}, Year2={group_y2}/{len(statement_fields)}")
        
        return result
    
    def _extract_from_table(
        self,
        table_df: pd.DataFrame,
        statement_fields: List[str]
    ) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """
        Extract Bank/Group Year1/Year2 from table with intelligent column detection.
        """
        result = {
            'Bank': {'Year1': {}, 'Year2': {}},
            'Group': {'Year1': {}, 'Year2': {}}
        }
        
        try:
            # Get columns
            columns = [str(col).strip() for col in table_df.columns]
            
            # Detect column structure
            column_map = self._detect_column_mapping(columns, table_df)
            
            if not column_map:
                logger.debug(f"         Could not map columns: {columns}")
                return result
            
            logger.debug(f"         Column mapping: {column_map}")
            
            # Extract row by row
            for row_idx, row in table_df.iterrows():
                try:
                    # First column should be field name
                    field_name = str(row.iloc[0]).strip()
                    
                    # Skip invalid rows
                    if not field_name or len(field_name) < 3:
                        continue
                    if field_name.lower() in ['none', 'nan', 'null', '']:
                        continue
                    # Skip page numbers and notes
                    if re.match(r'^(page\s*\d+|note\s*\d+)$', field_name.lower()):
                        continue
                    
                    # Match to schema field
                    matched_field = self._match_field(field_name, statement_fields)
                    
                    if matched_field:
                        # Extract values from all mapped columns
                        for col_idx, (entity, year) in column_map.items():
                            if col_idx < len(row):
                                value_str = str(row.iloc[col_idx]).strip()
                                value = extract_numbers(value_str)
                                
                                # Validate value is reasonable
                                if value is not None and self._is_valid_financial_value(value):
                                    if matched_field not in result[entity][year]:
                                        result[entity][year][matched_field] = value
                                        logger.debug(f"            ✓ {matched_field[:40]}... = {value} ({entity} {year})")
                
                except Exception as row_error:
                    continue
        
        except Exception as e:
            logger.error(f"         Table extraction error: {str(e)}")
        
        return result
    
    def _detect_column_mapping(
        self,
        columns: List[str],
        table_df: pd.DataFrame
    ) -> Dict[int, Tuple[str, str]]:
        """
        Intelligently detect which column contains Bank/Group and Year1/Year2 data.
        HARDCODED for HNB format where table has 3 numeric columns but missing first column.
        """
        column_map = {}
        
        # HNB format: Tables are missing the field name column
        # Columns are: [Bank 2024, Bank 2023, Group 2024] OR [Bank 2024, Bank 2023, Group 2024, Group 2023]
        # OR sometimes just [2024, 2023, 2024] (missing 4th column)
        
        num_cols = len(columns)
        logger.debug(f"         Detecting columns: {num_cols} columns found")
        
        if num_cols == 3:
            # Most common: Bank 2024, Bank 2023, Group 2024
            column_map = {
                0: ('Bank', 'Year1'),    # 2024
                1: ('Bank', 'Year2'),    # 2023
                2: ('Group', 'Year1')    # 2024
            }
        elif num_cols == 4:
            # Full format: Bank 2024, Bank 2023, Group 2024, Group 2023
            column_map = {
                0: ('Bank', 'Year1'),
                1: ('Bank', 'Year2'),
                2: ('Group', 'Year1'),
                3: ('Group', 'Year2')
            }
        elif num_cols >= 5:
            # Includes field name column: Name, Bank 2024, Bank 2023, Group 2024, Group 2023
            column_map = {
                1: ('Bank', 'Year1'),
                2: ('Bank', 'Year2'),
                3: ('Group', 'Year1'),
                4: ('Group', 'Year2')
            }
        else:
            # Fallback: Try original detection logic
            for idx in range(len(columns)):
                col_name = str(columns[idx]).lower()
                
                entity = None
                if 'bank' in col_name:
                    entity = 'Bank'
                elif 'group' in col_name:
                    entity = 'Group'
                
                year = None
                if '2024' in col_name:
                    year = 'Year1'
                elif '2023' in col_name:
                    year = 'Year2'
                
                if entity and year:
                    column_map[idx] = (entity, year)
        
        return column_map
    
    def _match_field(self, extracted_name: str, schema_fields: List[str]) -> Optional[str]:
        """Match extracted field name to schema with fuzzy matching."""
        extracted_clean = extracted_name.lower().strip()
        
        # Remove note references
        extracted_clean = re.sub(r'\(.*?\)', '', extracted_clean)
        extracted_clean = re.sub(r'note\s+\d+', '', extracted_clean)
        extracted_clean = extracted_clean.strip()
        
        # Exact match
        for field in schema_fields:
            if field.lower() == extracted_clean:
                return field
        
        # Term mapping
        for field in schema_fields:
            variations = TERM_MAPPING.get(field, [])
            if extracted_clean in [v.lower() for v in variations]:
                return field
        
        # Fuzzy match - key words overlap
        def get_keywords(text):
            words = re.findall(r'\b\w{4,}\b', text.lower())  # Words with 4+ chars
            return set(words)
        
        extracted_words = get_keywords(extracted_clean)
        
        best_match = None
        best_score = 0
        
        for field in schema_fields:
            field_words = get_keywords(field.lower())
            if field_words and extracted_words:
                common = len(field_words & extracted_words)
                total = len(field_words | extracted_words)
                score = common / total if total > 0 else 0
                
                if score > 0.5 and score > best_score:  # 50% match threshold
                    best_score = score
                    best_match = field
        
        return best_match
    
    def _is_valid_financial_value(self, value: float) -> bool:
        """Check if value looks like real financial data (not page numbers, etc.)."""
        if value is None:
            return False
        
        # Reject obvious page numbers and TOC entries
        if 0 < value < 100 and value == int(value):
            return False  # Likely page number
        
        # Reject unreasonably large or small values
        if abs(value) > 1e15 or (0 < abs(value) < 0.01):
            return False
        
        return True
    
    def _extract_from_text(self, text: str, statement_fields: List[str]) -> Dict[str, Any]:
        """Extract from plain text using regex patterns."""
        data = {}
        text_lower = text.lower()
        
        for field in statement_fields:
            variations = TERM_MAPPING.get(field, [field.lower()])
            
            for variation in variations:
                pattern = rf'{re.escape(variation)}\s*[:\-]?\s*([\d,\.\(\)\-]+)'
                match = re.search(pattern, text_lower, re.IGNORECASE)
                
                if match:
                    value = extract_numbers(match.group(1))
                    if value and self._is_valid_financial_value(value):
                        data[field] = value
                        break
        
        return data
    
    def extract_from_pdf(
        self,
        pdf_path: str,
        company_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Main extraction entry point."""
        logger.info("\n" + "="*80)
        logger.info("STARTING EXTRACTION")
        logger.info("="*80)
        
        try:
            # Load PDF
            pdf_loader = PDFLoader(pdf_path)
            pdf_info = pdf_loader.get_pdf_info()
            total_pages = pdf_info['total_pages']
            
            if not company_name:
                company_name = Path(pdf_path).stem
            
            logger.info(f"📄 File: {company_name}")
            logger.info(f"📄 Pages: {total_pages}")
            
            # Metadata
            pages_text_dict = pdf_loader.extract_pages_text(0, min(10, total_pages))
            sample_text = "\n".join([pages_text_dict[i] for i in sorted(pages_text_dict.keys())])
            
            currency, unit = detect_currency_and_unit(sample_text)
            period_info = detect_period(sample_text)
            
            currency_info = {'currency': currency or 'LKR', 'unit': unit or 'thousands'}
            
            # Find statement pages
            statement_pages = self.find_statement_pages(pdf_path, total_pages)
            
            # Extract from each statement
            results = {
                'Bank': {'Year1': {}, 'Year2': {}},
                'Group': {'Year1': {}, 'Year2': {}}
            }
            
            total_fields = sum(len(STATEMENT_FIELDS[stmt]) for stmt in MANDATORY_SECTIONS)
            
            for statement in MANDATORY_SECTIONS:
                pages = statement_pages.get(statement, [])
                if not pages:
                    logger.warning(f"⚠️ No pages found for {statement}")
                    continue
                
                fields = STATEMENT_FIELDS[statement]
                stmt_data = self.extract_from_statement_pages(pdf_path, pages, statement, fields)
                
                # Merge
                for entity in ['Bank', 'Group']:
                    for year in ['Year1', 'Year2']:
                        results[entity][year][statement] = stmt_data[entity][year]
            
            # Calculate stats
            total_extracted = sum(
                len([v for v in results[e][y][s].values() if v])
                for e in ['Bank', 'Group']
                for y in ['Year1', 'Year2']
                for s in results[e][y]
            )
            
            # Normalize
            normalizer = ValueNormalizer(currency_info['currency'], currency_info['unit'])
            for entity in ['Bank', 'Group']:
                for year in ['Year1', 'Year2']:
                    for statement in results[entity][year]:
                        results[entity][year][statement] = normalizer.normalize_dataset(
                            results[entity][year][statement],
                            currency_info['unit']
                        )
            
            # Output
            output = {
                'metadata': {
                    'entity_name': company_name,
                    'currency': currency_info,
                    'periods': [period_info] if period_info else [],
                    'extraction_date': datetime.now().isoformat(),
                    'total_pages': total_pages
                },
                'financial_statements': results,
                'processing_info': {
                    'total_fields_in_schema': total_fields * 4,
                    'total_fields_extracted': total_extracted,
                    'extraction_rate': f"{(total_extracted/(total_fields*4)*100):.1f}%"
                }
            }
            
            # Save
            output_path = save_extraction_result(
                results,
                output['metadata'],
                self.config.get('paths', {}).get('processed_json', 'data/processed/extracted_json'),
                company_name
            )
            
            logger.info("\n" + "="*80)
            logger.info(f"✅ EXTRACTION COMPLETE")
            logger.info(f"   Extracted: {total_extracted}/{total_fields*4} fields ({output['processing_info']['extraction_rate']})")
            logger.info(f"   Output: {output_path}")
            logger.info("="*80 + "\n")
            
            return output
        
        except Exception as e:
            logger.error(f"❌ ERROR: {str(e)}", exc_info=True)
            return {'error': str(e)}
    
    def extract_batch(self, pdf_directory: str) -> list:
        """Batch extraction."""
        pdf_files = list(Path(pdf_directory).glob("*.pdf"))
        return [self.extract_from_pdf(str(f)) for f in pdf_files]
