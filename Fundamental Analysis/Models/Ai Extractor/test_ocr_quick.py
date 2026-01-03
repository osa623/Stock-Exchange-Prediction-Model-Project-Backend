"""Quick test of OCR table detection."""
import sys
sys.path.insert(0, '.')

from src.extractor.table_detector import TableDetector
import pdfplumber

t = TableDetector(use_ocr_fallback=True)
pdf = pdfplumber.open('data/raw/dfcc/DFCC.pdf')
result = t.detect_tables(pdf, [225, 226])

print(f'\nFinal Result: {len(result)} tables')
for i, tbl in enumerate(result):
    print(f'  Table {i+1}: {tbl.get("extraction_method")} - {tbl.get("row_count")} rows')

pdf.close()
