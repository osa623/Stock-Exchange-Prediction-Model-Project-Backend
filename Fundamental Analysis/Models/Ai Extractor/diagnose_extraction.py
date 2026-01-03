"""Diagnose why extraction returns 0 rows."""
import pdfplumber
import sys
sys.path.insert(0, '.')

from src.extractor.table_detector import TableDetector
from src.extractor.column_interpreter import ColumnInterpreter
from src.extractor.row_extractor import RowExtractor

def diagnose_statement(pdf_path, pages, statement_name):
    """Diagnose extraction for a single statement."""
    print("\n" + "=" * 80)
    print(f"DIAGNOSING: {statement_name}")
    print(f"Pages: {pages}")
    print("=" * 80)
    
    with pdfplumber.open(pdf_path) as pdf:
        # Step 1: Detect tables
        detector = TableDetector()
        tables = detector.detect_tables(pdf, pages)
        print(f"\n✓ Found {len(tables)} tables")
        
        if not tables:
            print("❌ No tables found!")
            return
        
        main_table = tables[0]
        print(f"  - Main table: {main_table['row_count']} rows, page {main_table['page_num']}")
        
        # Show first 10 rows of raw table
        print("\n  First 10 rows of main table:")
        for i, row in enumerate(main_table['rows'][:10]):
            print(f"    Row {i}: {row[:4] if len(row) > 4 else row}")
        
        # Step 2: Interpret columns
        interpreter = ColumnInterpreter()
        column_info = interpreter.interpret_columns(main_table['rows'])
        
        print(f"\n✓ Column interpretation:")
        print(f"  - Entity columns: {column_info['entity_cols']}")
        print(f"  - Year columns: {column_info['year_cols']}")
        
        if not column_info['year_cols']:
            print("\n❌ No year columns found! Checking headers...")
            for i, row in enumerate(main_table['rows'][:5]):
                print(f"  Header row {i}: {row}")
        
        # Step 3: Extract rows
        extractor = RowExtractor()
        rows = extractor.extract_rows(main_table, column_info, statement_name)
        
        print(f"\n✓ Extracted {len(rows)} rows")
        
        if rows:
            print("\n  First 3 extracted rows:")
            for i, row in enumerate(rows[:3]):
                print(f"    Row {i+1}:")
                print(f"      Original: {row.get('original_label')}")
                print(f"      Canonical: {row.get('canonical_label')}")
                print(f"      Values: {list(row.get('values', {}).keys())}")
        else:
            print("\n❌ No rows extracted! Checking data rows...")
            data_rows = main_table['rows'][3:]
            print(f"  Data rows available: {len(data_rows)}")
            print("\n  First 5 data rows:")
            for i, row in enumerate(data_rows[:5]):
                label = str(row[0]).strip() if row and row[0] else ''
                print(f"    DataRow {i}: label='{label}' | len={len(label)} | full={row[:3] if len(row) > 3 else row}")

# Test Commercial Bank
print("\n" + "=" * 80)
print("COMMERCIAL BANK DIAGNOSIS")
print("=" * 80)

pdf_path = "data/raw/commercial/Commerical.pdf"

# From the stage_a_locations.json, the actual page ranges are:
# Income: 297-298 (0-indexed)
# Position: 297-298 (0-indexed) 
# Cash Flow: 306-307 (0-indexed)

diagnose_statement(pdf_path, [297, 298], "Income_Statement")
diagnose_statement(pdf_path, [297, 298], "Financial Position Statement")  
diagnose_statement(pdf_path, [306, 307], "Cash Flow Statement")
