"""
Quick test script for ML-based extraction
"""

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent))

from src.pipeline.ml_extractor import MLFinancialExtractor


def test_extraction():
    """Test extraction with available PDFs."""
    
    print("\n" + "="*80)
    print("🧪 TESTING ML-BASED EXTRACTION")
    print("="*80 + "\n")
    
    # Initialize extractor
    extractor = MLFinancialExtractor()
    
    # Test with Commercial Bank
    data_dir = Path(__file__).parent / "data" / "raw"
    test_pdfs = [
        ("Commercial Bank", data_dir / "commercial" / "Commerical.pdf"),
        ("HNB Bank", data_dir / "hnb" / "hnb.pdf"),
    ]
    
    for bank_name, pdf_path in test_pdfs:
        if not pdf_path.exists():
            print(f"⚠️ {bank_name} PDF not found: {pdf_path}")
            continue
        
        print(f"\n{'='*80}")
        print(f"🔍 TESTING: {bank_name}")
        print(f"{'='*80}\n")
        
        try:
            results = extractor.extract_from_pdf(str(pdf_path))
            
            # Count extracted fields
            total_fields = 0
            for entity in ["Bank", "Group"]:
                for year in ["Year1", "Year2"]:
                    for statement in results[entity][year]:
                        field_count = len(results[entity][year][statement])
                        total_fields += field_count
                        if field_count > 0:
                            print(f"✅ {entity} {year} - {statement}: {field_count} fields")
            
            print(f"\n📊 Total fields extracted: {total_fields}")
            
            # Save results
            output_dir = Path(__file__).parent / "data" / "processed" / "extracted_json"
            output_file = output_dir / f"{pdf_path.stem}_test_extracted.json"
            extractor.save_results(results, str(output_file))
            
            print(f"✅ Test passed for {bank_name}!\n")
            
        except Exception as e:
            print(f"❌ Test failed for {bank_name}: {e}\n")


if __name__ == "__main__":
    test_extraction()
