"""Debug OCR activation for DFCC."""
import sys
sys.path.insert(0, '.')

from src.extractor.table_detector import TableDetector
import pdfplumber

print("=" * 80)
print("TESTING OCR ACTIVATION FOR DFCC")
print("=" * 80)

# Check OCR availability
detector = TableDetector(use_ocr_fallback=True)
print(f"\n1. OCR Available: {detector.ocr_available}")
print(f"   Use OCR Fallback: {detector.use_ocr_fallback}")

# Test on DFCC pages
pdf_path = "data/raw/dfcc/DFCC.pdf"
print(f"\n2. Opening PDF: {pdf_path}")

with pdfplumber.open(pdf_path) as pdf:
    print(f"   Total pages: {len(pdf.pages)}")
    
    # Test Income Statement pages
    print(f"\n3. Testing pages 225-226 (Income Statement)...")
    
    # First check quality manually
    raw_tables = []
    for page_num in range(225, 227):
        page = pdf.pages[page_num]
        page_tables = page.extract_tables(detector.table_settings_text)
        for idx, table in enumerate(page_tables):
            if table and len(table) > 2:
                raw_tables.append({
                    'page_num': page_num,
                    'table_idx': idx,
                    'rows': table,
                    'row_count': len(table),
                    'extraction_method': 'pdfplumber'
                })
    
    if raw_tables:
        quality = detector._assess_table_quality(raw_tables)
        print(f"   Quality score: {quality:.3f} ({'GOOD ✓' if quality >= 0.5 else 'POOR ✗'})")
    
    # Now run the full detection (which includes quality check)
    tables = detector.detect_tables(pdf, [225, 226])
    
    print(f"\n4. Results:")
    print(f"   Tables found: {len(tables)}")
    
    if tables:
        for i, table in enumerate(tables):
            method = table.get('extraction_method', 'unknown')
            rows = table.get('row_count', 0)
            print(f"   Table {i+1}: {method} extraction, {rows} rows")
            
            if method == 'ocr':
                print("      ✓ OCR WAS USED!")
            elif method == 'pdfplumber':
                print("      ! Normal pdfplumber extraction worked")
                # Show first 3 rows to see if they're valid
                print("      First 3 rows:")
                for r in table['rows'][:3]:
                    print(f"        {r[:4] if len(r) > 4 else r}")
    else:
        print("   ❌ NO TABLES FOUND")
        print("   OCR should have been triggered but wasn't!")
        print("\n5. Debugging OCR availability:")
        
        # Check imports
        try:
            import pytesseract
            print("   ✓ pytesseract available")
        except ImportError:
            print("   ✗ pytesseract NOT installed")
        
        try:
            from PIL import Image
            print("   ✓ PIL available")
        except ImportError:
            print("   ✗ PIL NOT installed")
        
        try:
            import pdf2image
            print("   ✓ pdf2image available")
        except ImportError:
            print("   ✗ pdf2image NOT installed")
        
        try:
            from config.ocr_config import POPPLER_PATH
            print(f"   ✓ Poppler path: {POPPLER_PATH}")
        except Exception as e:
            print(f"   ✗ Poppler config error: {e}")

print("\n" + "=" * 80)
