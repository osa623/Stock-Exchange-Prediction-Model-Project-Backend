"""
Direct test of Commercial Bank extraction on known pages
"""

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent))

from src.pipeline.ml_extractor import MLFinancialExtractor


def main():
    print("\n" + "="*80)
    print("🧪 TESTING WITH KNOWN PAGES (297-305)")
    print("="*80 + "\n")
    
    extractor = MLFinancialExtractor()
    
    # Manually set the pages we know contain the statements
    statement_pages = {
        "Income_Statement": [296, 297],  # Pages 297-298 in PDF (0-indexed)
        "Financial Position Statement": [298, 299],  # Pages 299-300
        "Cash Flow Statement": [304, 305, 306]  # Pages 305-307
    }
    
    pdf_path = Path(__file__).parent / "data" / "raw" / "commercial" / "Commerical.pdf"
    
    print(f"📄 Processing: {pdf_path.name}\n")
    print(f"📋 Using pages: {statement_pages}\n")
    
    # Extract each statement
    result = {
        "Bank": {"Year1": {}, "Year2": {}},
        "Group": {"Year1": {}, "Year2": {}}
    }
    
    for statement_type, pages in statement_pages.items():
        print(f"\n🔍 Extracting {statement_type} from pages {[p+1 for p in pages]}...")
        
        extracted = extractor._extract_statement(pdf_path, pages, statement_type)
        
        # Merge results
        for entity in ["Bank", "Group"]:
            for year in ["Year1", "Year2"]:
                result[entity][year][statement_type] = extracted[entity][year].get(statement_type, {})
        
        year1_count = len(extracted["Group"]["Year1"])
        year2_count = len(extracted["Group"]["Year2"])
        print(f"   ✅ Group Year1: {year1_count} fields")
        print(f"   ✅ Group Year2: {year2_count} fields")
    
    # Save results
    output_path = Path(__file__).parent / "data" / "processed" / "extracted_json" / "commercial_direct_test.json"
    extractor.save_results(result, str(output_path))
    
    # Summary
    total_year1 = sum(len(result["Group"]["Year1"].get(s, {})) for s in statement_pages.keys())
    total_year2 = sum(len(result["Group"]["Year2"].get(s, {})) for s in statement_pages.keys())
    
    print(f"\n" + "="*80)
    print(f"🎯 TOTAL EXTRACTED:")
    print(f"   • Group Year 1: {total_year1} fields")
    print(f"   • Group Year 2: {total_year2} fields")
    print(f"   • Grand Total: {total_year1 + total_year2} fields")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
