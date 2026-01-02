#!/usr/bin/env python
"""Quick test to see what's in the PDF and why extraction isn't working."""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

import pdfplumber
import pandas as pd
from src.utils.helpers import extract_numbers

pdf_path = "data/raw/hnb/HNBannual.pdf"

print("="*80)
print("TESTING PDF EXTRACTION")
print("="*80)

# Test 1: Find statement pages
print("\n1. SEARCHING FOR STATEMENT PAGES (pages 10-100)...")
print("-"*80)

keywords = {
    'Income Statement': ['income statement', 'profit or loss', 'comprehensive income'],
    'Financial Position': ['financial position', 'balance sheet'],
    'Cash Flow': ['cash flow', 'statement of cash flows']
}

found_pages = {k: [] for k in keywords.keys()}

with pdfplumber.open(pdf_path) as pdf:
    for page_num in range(10, min(100, len(pdf.pages))):
        page = pdf.pages[page_num]
        text = page.extract_text()
        
        if text:
            text_lower = text.lower()
            for statement, kw_list in keywords.items():
                if any(kw in text_lower for kw in kw_list):
                    if page_num not in found_pages[statement]:
                        found_pages[statement].append(page_num)
                        print(f"✓ Found '{statement}' on page {page_num + 1}")
                        # Show first 200 chars
                        print(f"   Preview: {text[:200]}...")
                        break

print("\n2. SUMMARY OF FOUND PAGES:")
print("-"*80)
for statement, pages in found_pages.items():
    if pages:
        print(f"{statement}: Pages {[p+1 for p in pages[:5]]}")
    else:
        print(f"{statement}: NOT FOUND!")

# Test 2: Extract tables from first Income Statement page
print("\n3. EXTRACTING TABLES FROM FIRST PAGES...")
print("-"*80)

test_pages = []
for pages in found_pages.values():
    if pages:
        test_pages.append(pages[0])

if not test_pages:
    print("❌ No pages found to test!")
    sys.exit(1)

test_page = test_pages[0]
print(f"\nTesting page {test_page + 1}...")

with pdfplumber.open(pdf_path) as pdf:
    page = pdf.pages[test_page]
    tables = page.extract_tables()
    
    print(f"Found {len(tables)} tables on page {test_page + 1}")
    
    for i, table in enumerate(tables[:3]):  # Show first 3 tables
        print(f"\n--- TABLE {i+1} ---")
        if table and len(table) > 0:
            # Convert to DataFrame
            try:
                df = pd.DataFrame(table[1:], columns=table[0])
                print(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")
                print(f"Columns: {list(df.columns)}")
                print("\nFirst 5 rows:")
                print(df.head(5))
                
                # Check for numeric values
                print("\nChecking for numeric values...")
                for col_idx, col in enumerate(df.columns):
                    values = []
                    for val in df[col].head(5):
                        num = extract_numbers(str(val))
                        if num is not None:
                            values.append(num)
                    if values:
                        print(f"  Column {col_idx} ({col}): {values}")
                
            except Exception as e:
                print(f"Error converting to DataFrame: {e}")
                print(f"Raw table preview: {table[:3]}")

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)
from src.utils.logger import setup_logger, get_logger
import json

# Setup logging
setup_logger("test_extraction", "logs")
logger = get_logger(__name__)


def test_system_setup():
    """Test if the system is properly set up."""
    print("\n" + "="*60)
    print("TESTING SYSTEM SETUP")
    print("="*60)
    
    # Check imports
    try:
        import pdfplumber
        print("✓ pdfplumber installed")
    except ImportError:
        print("✗ pdfplumber NOT installed - run: pip install pdfplumber")
        return False
    
    try:
        import google.generativeai
        print("✓ google-generativeai installed")
    except ImportError:
        print("✗ google-generativeai NOT installed - run: pip install google-generativeai")
        return False
    
    # Check API key
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('GOOGLE_API_KEY')
    if api_key and len(api_key) > 20:
        print(f"✓ Google API Key configured: {api_key[:15]}...")
    else:
        print("✗ Google API Key NOT configured")
        print("  Get free key at: https://makersuite.google.com/app/apikey")
        print("  Then add to .env file: GOOGLE_API_KEY=your_key_here")
        return False
    
    # Check data directories
    data_dir = Path("data/raw")
    if data_dir.exists():
        print(f"✓ Data directory exists: {data_dir}")
        
        # Count PDF files
        pdf_files = list(data_dir.rglob("*.pdf"))
        print(f"  Found {len(pdf_files)} PDF file(s)")
        
        if pdf_files:
            print("\n  Available PDFs:")
            for pdf in pdf_files[:5]:  # Show first 5
                print(f"    - {pdf.relative_to(data_dir)}")
            if len(pdf_files) > 5:
                print(f"    ... and {len(pdf_files) - 5} more")
        else:
            print("  ⚠ No PDF files found in data/raw/")
            print("    Please add bank PDF reports to extract data from")
    else:
        print("✗ Data directory not found")
    
    print("\n" + "="*60)
    print("SYSTEM CHECK COMPLETE")
    print("="*60 + "\n")
    
    return True


def run_demo_extraction():
    """Run a demo extraction if PDF files are available."""
    print("\n" + "="*60)
    print("DEMO EXTRACTION")
    print("="*60)
    
    # Find first PDF
    data_dir = Path("data/raw")
    pdf_files = list(data_dir.rglob("*.pdf"))
    
    if not pdf_files:
        print("\nNo PDF files found to process.")
        print("Add a bank annual report PDF to data/raw/ and run again.")
        print("\nExample structure:")
        print("  data/raw/hnb/HNB_Annual_Report_2023.pdf")
        print("  data/raw/alliance_finance/Alliance_AR_2023.pdf")
        return
    
    # Use first PDF
    pdf_path = pdf_files[0]
    print(f"\nProcessing: {pdf_path.name}")
    print(f"Location: {pdf_path}")
    
    try:
        # Initialize pipeline
        print("\nInitializing extraction pipeline...")
        pipeline = ExtractionPipeline("config/settings.yaml")
        
        # Extract
        print("Extracting data (this may take 30-60 seconds)...\n")
        result = pipeline.extract_from_pdf(str(pdf_path))
        
        # Display results
        if 'error' in result:
            print(f"\n✗ Extraction failed: {result['error']}")
        else:
            print("\n" + "="*60)
            print("EXTRACTION RESULTS")
            print("="*60)
            print(f"Company: {result.get('company_name', 'Unknown')}")
            print(f"Period: {result.get('period', {}).get('text', 'N/A')}")
            print(f"Currency: {result.get('currency', 'N/A')}")
            print(f"Unit: {result.get('unit', 'N/A')}")
            
            print(f"\nStatements extracted:")
            for statement, data in result.get('data', {}).items():
                print(f"  - {statement}: {len(data)} fields")
                # Show first 3 fields as sample
                for i, (key, value) in enumerate(list(data.items())[:3]):
                    print(f"      • {key}: {value}")
                if len(data) > 3:
                    print(f"      ... and {len(data) - 3} more fields")
            
            print(f"\nConfidence: {result.get('confidence', {}).get('overall', 'N/A')}")
            print(f"\nResults saved to: data/processed/extracted_json/")
            print("="*60 + "\n")
            
    except Exception as e:
        print(f"\n✗ Error during extraction: {str(e)}")
        import traceback
        traceback.print_exc()


def show_usage_examples():
    """Show usage examples."""
    print("\n" + "="*60)
    print("HOW TO USE THIS SYSTEM")
    print("="*60)
    
    print("\n1. EXTRACT FROM SINGLE PDF:")
    print("   python scripts/run_single_pdf.py \"data/raw/hnb/report.pdf\"")
    
    print("\n2. BATCH PROCESS FOLDER:")
    print("   python scripts/run_batch.py \"data/raw/hnb/\"")
    
    print("\n3. USE IN PYTHON CODE:")
    print("""
   from src.pipeline.extract import ExtractionPipeline
   
   pipeline = ExtractionPipeline()
   result = pipeline.extract_from_pdf("path/to/report.pdf")
   
   print(result['data']['income_statement'])
   print(result['confidence'])
    """)
    
    print("\n4. VIEW EXTRACTED DATA:")
    print("   - JSON files saved in: data/processed/extracted_json/")
    print("   - Logs saved in: logs/")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("BANK FINANCIAL STATEMENT AI EXTRACTOR - TEST SCRIPT")
    print("="*60)
    
    # Test system setup
    if not test_system_setup():
        print("\n⚠ System setup incomplete. Please fix the issues above.")
        sys.exit(1)
    
    # Show usage
    show_usage_examples()
    
    # Ask if user wants to run demo
    print("\nWould you like to run a demo extraction?")
    print("This will process the first PDF found in data/raw/")
    
    # Check if PDFs exist
    pdf_files = list(Path("data/raw").rglob("*.pdf"))
    if pdf_files:
        print(f"\nPress Enter to extract from: {pdf_files[0].name}")
        print("Or type 'skip' to exit: ", end="")
        
        user_input = input().strip().lower()
        
        if user_input != 'skip':
            run_demo_extraction()
    else:
        print("\n⚠ No PDF files found. Add PDFs to data/raw/ first.")
    
    print("\n✓ Test script completed!")
