"""Check if Group 2023 data is on page 291 or in continuation tables."""
import pdfplumber
import pandas as pd

pdf_path = "data/raw/hnb/HNBannual.pdf"

print("="*80)
print("CHECKING FOR GROUP 2023 DATA")
print("="*80)

for page_num in [289, 290, 291, 292]:  # Pages 290-293
    print(f"\n{'='*80}")
    print(f"PAGE {page_num + 1}")
    print(f"{'='*80}")
    
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_num]
        
        # Check text
        text = page.extract_text()
        lines = text.split('\n')[:15]
        
        print("\nFirst 15 lines:")
        for i, line in enumerate(lines, 1):
            print(f"  {i:2d}: {line}")
        
        # Check tables
        tables = page.extract_tables()
        print(f"\nTables found: {len(tables)}")
        
        for i, table in enumerate(tables):
            if table and len(table) > 0:
                print(f"\nTable {i+1}:")
                print(f"  Rows: {len(table)}, Columns: {len(table[0]) if table else 0}")
                
                # Show first few rows
                for row_idx, row in enumerate(table[:5]):
                    print(f"  Row {row_idx}: {row}")
