"""Debug extraction from page 290 (Income Statement)."""
import pdfplumber
import pandas as pd
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.helpers import extract_numbers

pdf_path = "data/raw/hnb/HNBannual.pdf"
page_num = 289  # Page 290 (0-indexed)

print("="*80)
print(f"DEBUGGING PAGE {page_num + 1} - INCOME STATEMENT")
print("="*80)

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[page_num]
    
    # First check the text to see headers
    text = page.extract_text()
    lines = text.split('\n')[:20]
    print("\nFirst 20 lines of text on page:")
    print("-"*80)
    for i, line in enumerate(lines, 1):
        print(f"{i:2d}: {line}")
    
    tables = page.extract_tables()
    
    print(f"\n\nFound {len(tables)} tables on page {page_num + 1}\n")
    
    for i, table in enumerate(tables):
        if not table or len(table) == 0:
            continue
            
        print(f"\n{'='*80}")
        print(f"TABLE {i+1} - RAW")
        print(f"{'='*80}")
        
        print(f"Total rows: {len(table)}")
        print(f"\nFirst 5 rows (RAW):")
        for row_idx, row in enumerate(table[:5]):
            print(f"  Row {row_idx}: {row}")

print("\n" + "="*80)
print("DEBUG COMPLETE")
print("="*80)
