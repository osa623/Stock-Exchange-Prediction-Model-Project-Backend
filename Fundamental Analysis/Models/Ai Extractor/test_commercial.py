"""
Simple test to verify ML extraction with Commercial Bank PDF
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from src.pipeline.ml_extractor import MLFinancialExtractor
import json


def main():
    print("\n" + "="*80)
    print("TESTING ML-BASED EXTRACTION - COMMERCIAL BANK")
    print("="*80 + "\n")
    
    # Initialize extractor
    extractor = MLFinancialExtractor()
    
    # Test with Commercial Bank
    pdf_path = Path(__file__).parent / "data" / "raw" / "commercial" / "Commerical.pdf"
    
    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    print(f"📄 Processing: {pdf_path.name}\n")
    
    # Extract
    results = extractor.extract_from_pdf(str(pdf_path))
    
    # Display results
    print("\n" + "="*80)
    print("📊 EXTRACTION RESULTS")
    print("="*80 + "\n")
    
    for statement_type in ["Income_Statement", "Financial Position Statement", "Cash Flow Statement"]:
        year1_fields = len(results["Group"]["Year1"].get(statement_type, {}))
        year2_fields = len(results["Group"]["Year2"].get(statement_type, {}))
        
        print(f"📋 {statement_type}:")
        print(f"   • Group Year 1: {year1_fields} fields")
        print(f"   • Group Year 2: {year2_fields} fields")
    
    # Total
    total_year1 = sum(len(results["Group"]["Year1"].get(s, {})) 
                     for s in ["Income_Statement", "Financial Position Statement", "Cash Flow Statement"])
    total_year2 = sum(len(results["Group"]["Year2"].get(s, {})) 
                     for s in ["Income_Statement", "Financial Position Statement", "Cash Flow Statement"])
    
    print(f"\n🎯 TOTAL GROUP FIELDS:")
    print(f"   • Year 1: {total_year1} fields")
    print(f"   • Year 2: {total_year2} fields")
    print(f"   • Grand Total: {total_year1 + total_year2} fields")
    
    # Save results
    output_path = Path(__file__).parent / "data" / "processed" / "extracted_json" / "commercial_final.json"
    extractor.save_results(results, str(output_path))
    
    print(f"\n💾 Results saved to: {output_path.name}")
    
    # Show sample extracted fields
    print(f"\n📝 SAMPLE EXTRACTED FIELDS (Year 2):")
    count = 0
    for statement in ["Income_Statement", "Financial Position Statement", "Cash Flow Statement"]:
        for field, value in results["Group"]["Year2"].get(statement, {}).items():
            if count < 10:
                print(f"   • {field}: {value}")
                count += 1
            else:
                break
        if count >= 10:
            break
    
    print("\n" + "="*80)
    print("✅ EXTRACTION COMPLETED SUCCESSFULLY!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
