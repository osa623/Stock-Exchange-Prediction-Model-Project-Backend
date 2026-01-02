"""
IMPROVED Text-based extraction for HNB format.
Directly parses text lines instead of relying on broken table extraction.
"""

from pathlib import Path
from typing import Dict, Any, List
import re
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pdf.loader import PDFLoader
from src.utils.helpers import extract_numbers
from config.target_schema_bank import STATEMENT_FIELDS
from config.term_mapping_bank import TERM_MAPPING

def extract_text_based(pdf_path: str, page_num: int, statement_name: str) -> Dict:
    """Extract using direct text parsing - better for HNB format."""
    
    result = {
        'Bank': {'Year1': {}, 'Year2': {}},
        'Group': {'Year1': {}, 'Year2': {}}
    }
    
    pdf_loader = PDFLoader(pdf_path)
    page_text = pdf_loader.extract_text_pdfplumber(page_num)
    lines = page_text.split('\n')
    
    statement_fields = STATEMENT_FIELDS[statement_name]
    
    for line in lines:
        line = line.strip()
        if not line or len(line) < 10:
            continue
        
        # Extract all numbers from the line
        parts = line.split()
        numbers = []
        field_parts = []
        found_first_number = False
        
        for part in parts:
            num = extract_numbers(part)
            if num is not None and abs(num) > 10:  # Valid financial number
                numbers.append(num)
                found_first_number = True
            elif not found_first_number:
                # Before numbers = field name
                field_parts.append(part)
        
        # If we have 4 numbers, this is a complete data row
        if len(numbers) >= 4:
            field_name = ' '.join(field_parts).strip()
            
            # Clean field name
            field_name = re.sub(r'\d+$', '', field_name)  # Remove trailing numbers (notes)
            field_name = re.sub(r'^Note\s+', '', field_name, flags=re.IGNORECASE)
            field_name = field_name.strip()
            
            if len(field_name) < 3:
                continue
            
            # Match to schema
            matched_field = match_field(field_name, statement_fields)
            
            if matched_field:
                result['Bank']['Year1'][matched_field] = numbers[0]
                result['Bank']['Year2'][matched_field] = numbers[1]
                result['Group']['Year1'][matched_field] = numbers[2]
                result['Group']['Year2'][matched_field] = numbers[3]
                print(f"  OK {matched_field}: {numbers}")
    
    return result

def match_field(extracted_name: str, schema_fields: List[str]) -> str:
    """Match extracted field name to schema."""
    extracted_clean = extracted_name.lower().strip()
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
    
    # Fuzzy match
    def get_keywords(text):
        words = re.findall(r'\b\w{4,}\b', text.lower())
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
            
            if score > 0.5 and score > best_score:
                best_score = score
                best_match = field
    
    return best_match

# Test
if __name__ == "__main__":
    pdf_path = "data/raw/hnb/HNBannual.pdf"
    
    print("="*80)
    print("TEXT-BASED EXTRACTION TEST")
    print("="*80)
    
    # Test Income Statement (page 290)
    print("\nINCOME STATEMENT (Page 290)")
    print("-"*80)
    result = extract_text_based(pdf_path, 289, 'Income_Statement')
    
    print(f"\nExtracted:")
    print(f"  Bank Year1: {len(result['Bank']['Year1'])} fields")
    print(f"  Bank Year2: {len(result['Bank']['Year2'])} fields")
    print(f"  Group Year1: {len(result['Group']['Year1'])} fields")
    print(f"  Group Year2: {len(result['Group']['Year2'])} fields")
    
    print(f"\nSample values:")
    for field in list(result['Bank']['Year1'].keys())[:5]:
        print(f"  {field}:")
        print(f"    Bank  2024: {result['Bank']['Year1'][field]:,.0f}")
        print(f"    Bank  2023: {result['Bank']['Year2'][field]:,.0f}")
        print(f"    Group 2024: {result['Group']['Year1'][field]:,.0f}")
        print(f"    Group 2023: {result['Group']['Year2'][field]:,.0f}")
