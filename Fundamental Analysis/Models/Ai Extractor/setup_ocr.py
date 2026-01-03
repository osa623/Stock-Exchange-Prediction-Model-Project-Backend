"""
Setup script to configure Poppler path for OCR extraction.
Run this once to set your Poppler installation path.
"""

import sys
from pathlib import Path

print("=" * 80)
print("OCR CONFIGURATION SETUP")
print("=" * 80)

# Ask for Poppler path
print("\nPlease enter your Poppler bin directory path.")
print("Example: C:\\Program Files\\poppler-24.08.0\\Library\\bin")
print("Or press Enter to skip (will use system PATH)")
print()

poppler_input = input("Poppler path: ").strip()

# Validate path if provided
if poppler_input:
    poppler_path = Path(poppler_input)
    if not poppler_path.exists():
        print(f"\n⚠️  Warning: Path does not exist: {poppler_path}")
        confirm = input("Continue anyway? (y/n): ").strip().lower()
        if confirm != 'y':
            print("Setup cancelled.")
            sys.exit(0)
    
    poppler_str = f'r"{poppler_input}"'
else:
    poppler_str = 'None'
    print("\n✓ Will use system PATH for Poppler")

# Update ocr_config.py
config_file = Path("config/ocr_config.py")

if config_file.exists():
    with open(config_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace POPPLER_PATH line
    import re
    content = re.sub(
        r'POPPLER_PATH = .*',
        f'POPPLER_PATH = {poppler_str}',
        content
    )
    
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n✓ Configuration updated: {config_file}")
    print("\nCurrent configuration:")
    print("-" * 40)
    
    # Show current config
    exec(open(config_file).read())
    print(f"Tesseract: {TESSERACT_PATH}")
    print(f"Poppler: {POPPLER_PATH}")
    
    print("\n" + "=" * 80)
    print("✓ SETUP COMPLETE")
    print("=" * 80)
    print("\nOCR is now enabled as a fallback for PDFs that fail normal extraction.")
    print("When pdfplumber can't extract tables, the system will automatically")
    print("convert pages to images and use Tesseract OCR.")
    print("\nTest it by running: python main.py")
else:
    print(f"\n❌ Error: Config file not found at {config_file}")
    sys.exit(1)
