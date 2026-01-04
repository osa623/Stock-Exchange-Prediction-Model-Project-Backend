"""
Configure OCR paths for Windows.
Run this once to set up Tesseract and Poppler paths.
"""

import os
import sys
from pathlib import Path

# Common Tesseract installation paths
TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    r"C:\Users\{}\AppData\Local\Programs\Tesseract-OCR\tesseract.exe".format(os.getenv('USERNAME')),
]

# Common Poppler installation paths
POPPLER_PATHS = [
    r"C:\Program Files\poppler\bin",
    r"C:\Program Files (x86)\poppler\bin",
    r"C:\poppler\bin",
]

def find_tesseract():
    """Find Tesseract installation."""
    for path in TESSERACT_PATHS:
        if Path(path).exists():
            return path
    return None

def find_poppler():
    """Find Poppler installation."""
    for path in POPPLER_PATHS:
        if Path(path).exists():
            return path
    return None

def configure_ocr():
    """Configure OCR paths."""
    print("=" * 80)
    print("OCR Configuration Check")
    print("=" * 80)
    
    # Check Tesseract
    tesseract_path = find_tesseract()
    if tesseract_path:
        print(f"\n✓ Tesseract found: {tesseract_path}")
        
        # Try to import and configure
        try:
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            version = pytesseract.get_tesseract_version()
            print(f"  Version: {version}")
        except Exception as e:
            print(f"  Warning: {str(e)}")
    else:
        print("\n✗ Tesseract NOT found!")
        print("  Download from: https://github.com/UB-Mannheim/tesseract/wiki")
        print("  Or install via: choco install tesseract")
    
    # Check Poppler
    poppler_path = find_poppler()
    if poppler_path:
        print(f"\n✓ Poppler found: {poppler_path}")
    else:
        print("\n✗ Poppler NOT found!")
        print("  Download from: https://github.com/oschwartz10612/poppler-windows/releases")
        print("  Extract and add to PATH")
    
    # Check Python packages
    print("\n" + "=" * 80)
    print("Python Packages:")
    print("=" * 80)
    
    packages = ['pytesseract', 'PIL', 'pdf2image']
    for pkg in packages:
        try:
            if pkg == 'PIL':
                import PIL
                print(f"✓ Pillow: {PIL.__version__}")
            else:
                module = __import__(pkg)
                version = getattr(module, '__version__', 'installed')
                print(f"✓ {pkg}: {version}")
        except ImportError:
            print(f"✗ {pkg}: NOT INSTALLED")
            print(f"  Install: pip install {pkg}")
    
    # Save config to file
    config_file = Path(__file__).parent / 'config' / 'ocr_config.py'
    config_file.parent.mkdir(exist_ok=True)
    
    with open(config_file, 'w') as f:
        f.write('"""Auto-generated OCR configuration."""\n\n')
        if tesseract_path:
            f.write(f'TESSERACT_PATH = r"{tesseract_path}"\n')
        else:
            f.write('TESSERACT_PATH = None\n')
        
        if poppler_path:
            f.write(f'POPPLER_PATH = r"{poppler_path}"\n')
        else:
            f.write('POPPLER_PATH = None\n')
    
    print(f"\n✓ Configuration saved to: {config_file}")
    
    # Test OCR
    if tesseract_path and poppler_path:
        print("\n" + "=" * 80)
        print("OCR Test:")
        print("=" * 80)
        try:
            import pytesseract
            from PIL import Image
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            
            # Simple test
            print("✓ OCR is ready to use!")
            print("\nYou can now run extractions with OCR fallback enabled.")
        except Exception as e:
            print(f"✗ OCR test failed: {str(e)}")
    else:
        print("\n! Please install missing components to enable OCR")

if __name__ == '__main__':
    configure_ocr()
