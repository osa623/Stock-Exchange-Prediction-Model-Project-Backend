"""Test OCR functionality."""

print("Testing OCR Configuration...")
print("=" * 80)

# Test 1: Check if libraries are installed
print("\n[1/4] Checking OCR libraries...")
try:
    import pytesseract
    print("  ✓ pytesseract installed")
except ImportError:
    print("  ✗ pytesseract not found. Install: pip install pytesseract")

try:
    from PIL import Image
    print("  ✓ PIL (Pillow) installed")
except ImportError:
    print("  ✗ PIL not found. Install: pip install Pillow")

try:
    import pdf2image
    print("  ✓ pdf2image installed")
except ImportError:
    print("  ✗ pdf2image not found. Install: pip install pdf2image")

# Test 2: Check configuration
print("\n[2/4] Checking configuration...")
try:
    from config.ocr_config import TESSERACT_PATH, POPPLER_PATH, OCR_CONFIG
    print(f"  Tesseract: {TESSERACT_PATH}")
    print(f"  Poppler: {POPPLER_PATH}")
    print(f"  DPI: {OCR_CONFIG.get('dpi', 300)}")
except ImportError as e:
    print(f"  ✗ Config error: {e}")

# Test 3: Verify Tesseract works
print("\n[3/4] Testing Tesseract...")
try:
    import pytesseract
    from config.ocr_config import TESSERACT_PATH
    
    if TESSERACT_PATH:
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
    
    version = pytesseract.get_tesseract_version()
    print(f"  ✓ Tesseract version: {version}")
except Exception as e:
    print(f"  ✗ Tesseract test failed: {e}")
    print("  Make sure Tesseract is installed and path is correct")

# Test 4: Check TableDetector OCR availability
print("\n[4/4] Testing TableDetector OCR integration...")
try:
    from src.extractor.table_detector import TableDetector
    
    detector = TableDetector(use_ocr_fallback=True)
    
    if detector.ocr_available:
        print("  ✓ OCR fallback is ENABLED and ready")
        print("  ✓ System will use OCR when normal extraction fails")
    else:
        print("  ✗ OCR fallback is NOT available")
        print("  Fix the issues above and try again")
except Exception as e:
    print(f"  ✗ TableDetector test failed: {e}")

print("\n" + "=" * 80)
print("Test complete!")
print("\nIf all tests passed, OCR is ready to use.")
print("The system will automatically use OCR for difficult PDFs.")
