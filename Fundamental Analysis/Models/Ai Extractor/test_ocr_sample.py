"""Test OCR output to see what we're getting."""
import sys
sys.path.insert(0, '.')

from pdf2image import convert_from_path
import pytesseract
from config.ocr_config import POPPLER_PATH, TESSERACT_PATH

# Set Tesseract path
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

pdf_path = "data/raw/dfcc/DFCC.pdf"
first_page = 226  # 1-based for pdf2image
last_page = 226

print(f"Converting page {first_page}...")
images = convert_from_path(
    pdf_path,
    first_page=first_page,
    last_page=last_page,
    dpi=300,
    poppler_path=POPPLER_PATH
)

print(f"Got {len(images)} images")
print("\nPerforming OCR...")

ocr_text = pytesseract.image_to_string(images[0], config='--psm 6')

print(f"\nOCR Text Length: {len(ocr_text)}")
print("\n" + "="*80)
print("OCR OUTPUT (first 50 lines):")
print("="*80)

lines = ocr_text.split('\n')
for i, line in enumerate(lines[:50], 1):
    print(f"{i:3d}: {repr(line)}")

print("\n" + "="*80)
print(f"Total lines: {len(lines)}")
