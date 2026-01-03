"""Debug why DFCC has 0 year columns."""
import sys
sys.path.insert(0, '.')

from src.extractor.table_detector import TableDetector
from src.extractor.column_interpreter import ColumnInterpreter
import pdfplumber

pdf_path = "data/raw/dfcc/DFCC.pdf"

with pdfplumber.open(pdf_path) as pdf:
    detector = TableDetector()
    tables = detector.detect_tables(pdf, [225, 226])
    
    if tables:
        main_table = tables[0]
        print(f"Main table has {main_table['row_count']} rows")
        
        print("\nFirst 15 rows of main table:")
        for i, row in enumerate(main_table['rows'][:15]):
            print(f"Row {i:2d}: {row}")
        
        # Try column interpretation
        interpreter = ColumnInterpreter()
        column_info = interpreter.interpret_columns(main_table['rows'])
        
        print(f"\n\nColumn Interpretation:")
        print(f"Entity columns: {column_info['entity_cols']}")
        print(f"Year columns: {column_info['year_cols']}")
        
        if not column_info['year_cols']:
            print("\n❌ NO YEAR COLUMNS DETECTED!")
            print("\nLooking for years in first 20 rows:")
            for i, row in enumerate(main_table['rows'][:20]):
                row_text = ' '.join([str(cell) for cell in row if cell])
                if '2024' in row_text or '2023' in row_text or '2022' in row_text:
                    print(f"  Row {i} has year: {row}")
