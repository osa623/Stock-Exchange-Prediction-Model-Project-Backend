#!/usr/bin/env python
"""Main entry point for Bank Financial Statement AI Extractor."""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from src.pipeline.extract import ExtractionPipeline
from src.utils.logger import setup_logger, get_logger

setup_logger("ai_extractor", "logs")
logger = get_logger(__name__)


def print_banner():
    """Print welcome banner."""
    print("\n" + "="*70)
    print("   BANK FINANCIAL STATEMENT AI EXTRACTOR")
    print("   Automatically extract data from bank PDF reports")
    print("="*70 + "\n")


def check_setup():
    """Check if system is properly configured."""
    issues = []
    
    # Check API key
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        issues.append("❌ GOOGLE_API_KEY not found in .env file")
        issues.append("   Get free key at: https://makersuite.google.com/app/apikey")
    else:
        print(f"✓ Google API Key configured")
    
    # Check data directory
    data_dir = Path("data/raw")
    if not data_dir.exists():
        issues.append("❌ data/raw directory not found")
    else:
        print(f"✓ Data directory exists")
    
    if issues:
        print("\n⚠️  SETUP ISSUES:\n")
        for issue in issues:
            print(issue)
        print("\nPlease fix the issues above before running.\n")
        return False
    
    return True


def find_pdfs():
    """Find all PDF files in data/raw directory."""
    data_dir = Path("data/raw")
    pdf_files = list(data_dir.rglob("*.pdf"))
    return sorted(pdf_files)


def display_menu(pdf_files):
    """Display PDF selection menu."""
    print("\n" + "-"*70)
    print("AVAILABLE PDF FILES:")
    print("-"*70)
    
    if not pdf_files:
        print("\n❌ No PDF files found in data/raw/")
        print("\nPlease add bank PDF reports to one of these folders:")
        print("  - data/raw/hnb/")
        print("  - data/raw/alliance_finance/")
        print("  - data/raw/janashakthi/")
        print("\nOr create a new folder: data/raw/your_bank_name/\n")
        return None
    
    for i, pdf in enumerate(pdf_files, 1):
        relative_path = pdf.relative_to("data/raw")
        size_mb = pdf.stat().st_size / (1024 * 1024)
        print(f"  [{i}] {relative_path} ({size_mb:.1f} MB)")
    
    print(f"  [A] Process ALL {len(pdf_files)} files (batch mode)")
    print(f"  [Q] Quit")
    print("-"*70)
    
    return pdf_files


def get_user_choice(pdf_files):
    """Get user's selection."""
    while True:
        choice = input("\nSelect option (number, A for all, Q to quit): ").strip().upper()
        
        if choice == 'Q':
            return None, 'quit'
        
        if choice == 'A':
            return pdf_files, 'batch'
        
        try:
            index = int(choice) - 1
            if 0 <= index < len(pdf_files):
                return [pdf_files[index]], 'single'
            else:
                print(f"❌ Invalid number. Please enter 1-{len(pdf_files)}")
        except ValueError:
            print("❌ Invalid input. Please enter a number, A, or Q")


def process_single_pdf(pdf_path, pipeline):
    """Process a single PDF file."""
    print("\n" + "="*70)
    print(f"PROCESSING: {pdf_path.name}")
    print("="*70)
    print(f"Location: {pdf_path}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nExtracting data... (this may take 30-60 seconds)\n")
    
    try:
        # Extract data
        result = pipeline.extract_from_pdf(str(pdf_path))
        
        if 'error' in result:
            print(f"\n❌ EXTRACTION FAILED: {result['error']}")
            if 'suggestion' in result:
                print(f"\n💡 SUGGESTIONS:")
                print(f"{result['suggestion']}")
            print()
            return False
        
        # Display results
        print("\n" + "="*70)
        print("✓ EXTRACTION SUCCESSFUL")
        print("="*70)
        print(f"Company: {result.get('company_name', 'Unknown')}")
        print(f"Period: {result.get('period', {}).get('text', 'N/A')}")
        print(f"Currency: {result.get('currency', 'N/A')}")
        print(f"Unit: {result.get('unit', 'N/A')}")
        
        # Display results summary  
        print(f"\n📊 EXTRACTION SUMMARY:")
        print(f"  • Company: {result.get('metadata', {}).get('entity_name', 'Unknown')}")
        print(f"  • Currency: {result.get('metadata', {}).get('currency', {}).get('currency', 'Unknown')} ({result.get('metadata', {}).get('currency', {}).get('unit', 'Unknown')})")
        print(f"  • Periods: {len(result.get('metadata', {}).get('periods', []))}")
        print(f"  • Pages: {result.get('processing_info', {}).get('total_pages', 0)}")
        print(f"  • Fields in Schema: {result.get('processing_info', {}).get('total_fields_in_schema', 0)}")
        print(f"  • Fields Extracted: {result.get('processing_info', {}).get('total_fields_extracted', 0)}")
        print(f"  • Extraction Rate: {result.get('processing_info', {}).get('extraction_rate', '0%')}")
        print(f"  • Confidence: {result.get('confidence_score', 0):.2%}")
        
        print(f"\n📊 STATEMENTS EXTRACTED:")
        for statement, data in result.get('financial_statements', {}).items():
            found = len([v for v in data.values() if v is not None]) if isinstance(data, dict) else 0
            total = len(data) if isinstance(data, dict) else 0
            print(f"  ✓ {statement.replace('_', ' ').title()}: {found}/{total} fields")
            
            # Show sample values
            if isinstance(data, dict):
                sample_count = 0
                for key, value in data.items():
                    if value is not None and sample_count < 3:
                        print(f"      - {key}: {value}")
                        sample_count += 1
        
        print(f"\n✅ VALIDATION:")
        for key, passed in result.get('validation', {}).items():
            if isinstance(passed, dict):
                status = "✓ PASSED" if passed.get('passed', False) else "✗ FAILED"
            else:
                status = "✓ PASSED" if passed else "✗ FAILED"
            print(f"  {status} - {key.replace('_', ' ').title()}")
        
        print(f"\n💾 OUTPUT:")
        print(f"  • JSON: data/processed/extracted_json/")
        print(f"  • Logs: logs/")
        print("="*70 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}\n")
        logger.error(f"Error processing {pdf_path}: {str(e)}", exc_info=True)
        return False


def process_batch(pdf_files, pipeline):
    """Process multiple PDF files."""
    print("\n" + "="*70)
    print(f"BATCH PROCESSING: {len(pdf_files)} FILES")
    print("="*70 + "\n")
    
    successful = 0
    failed = 0
    
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"\n[{i}/{len(pdf_files)}] Processing: {pdf_path.name}")
        print("-"*70)
        
        try:
            result = pipeline.extract_from_pdf(str(pdf_path))
            
            if 'error' in result:
                print(f"❌ Failed: {result['error']}")
                failed += 1
            else:
                print(f"✓ Success: {len(result.get('data', {}))} statements extracted")
                successful += 1
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            failed += 1
    
    # Summary
    print("\n" + "="*70)
    print("BATCH PROCESSING COMPLETE")
    print("="*70)
    print(f"Total Files: {len(pdf_files)}")
    print(f"✓ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"Success Rate: {(successful/len(pdf_files)*100):.1f}%")
    print(f"\n💾 Results saved to: data/processed/extracted_json/")
    print("="*70 + "\n")


def main():
    """Main function."""
    print_banner()
    
    # Check setup
    if not check_setup():
        sys.exit(1)
    
    # Find PDFs
    pdf_files = find_pdfs()
    
    # Display menu
    pdf_files = display_menu(pdf_files)
    if pdf_files is None:
        sys.exit(0)
    
    # Get user choice
    selected_files, mode = get_user_choice(pdf_files)
    
    if selected_files is None:
        print("\n👋 Goodbye!\n")
        sys.exit(0)
    
    # Initialize pipeline
    print("\n🔧 Initializing extraction pipeline...")
    try:
        pipeline = ExtractionPipeline("config/settings.yaml")
        print("✓ Pipeline ready\n")
    except Exception as e:
        print(f"\n❌ Failed to initialize pipeline: {str(e)}\n")
        sys.exit(1)
    
    # Process files
    if mode == 'single':
        success = process_single_pdf(selected_files[0], pipeline)
        sys.exit(0 if success else 1)
    else:  # batch
        process_batch(selected_files, pipeline)
        sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}\n")
        sys.exit(1)
