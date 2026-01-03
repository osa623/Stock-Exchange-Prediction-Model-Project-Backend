"""Debug script to check table content from PABC"""
import pdfplumber
from src.extractor.table_detector import TableDetector
from src.extractor.column_interpreter import ColumnInterpreter

pdf_path = "data/raw/pabc/pabc.pdf"

with pdfplumber.open(pdf_path) as pdf:
    # Check Income Statement pages (157-158 in 0-indexed)
    detector = TableDetector()
    tables = detector.detect_tables(pdf, [157, 158])
    
    print(f"\n=== Found {len(tables)} tables ===\n")
    
    for i, table in enumerate(tables):
        print(f"\n--- Table {i+1} (Page {table['page_num']+1}) ---")
        print(f"Rows: {table['row_count']}")
        
        # Show first 10 rows
        for row_idx, row in enumerate(table['rows'][:10]):
            print(f"Row {row_idx}: {row}")
        
        print(f"\n--- Column Interpretation ---")
        interpreter = ColumnInterpreter()
        column_info = interpreter.interpret_columns(table['rows'])
        print(f"Entity columns: {column_info['entity_cols']}")
        print(f"Year columns: {column_info['year_cols']}")
