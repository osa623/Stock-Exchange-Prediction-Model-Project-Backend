"""
Main entry point for ML-based financial statement extraction
Works with ANY annual report PDF
"""

import logging
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent))

from src.pipeline.ml_extractor import MLFinancialExtractor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main execution function."""
    
    print("\n" + "="*80)
    print("🤖 ML-BASED FINANCIAL STATEMENT EXTRACTOR")
    print("="*80)
    print("✅ Works with any bank annual report")
    print("✅ Automatically detects financial statements")
    print("✅ Intelligent field matching using NLP")
    print("="*80 + "\n")
    
    # Initialize extractor
    extractor = MLFinancialExtractor()
    
    # Define PDF paths
    data_dir = Path(__file__).parent / "data" / "raw"
    
    # Available PDFs
    pdf_files = {
        "1": data_dir / "hnb" / "hnb.pdf",
        "2": data_dir / "commercial" / "Commerical.pdf",
        "3": data_dir / "janashakthi" / "janashakthi.pdf",
        "4": data_dir / "jhonkeels" / "jhonkeels.pdf",
    }
    
    # Display menu
    print("Select a PDF to extract:")
    print("1. HNB Bank")
    print("2. Commercial Bank")
    print("3. Janashakthi Bank")
    print("4. John Keells")
    print("5. Custom path")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    if choice in pdf_files:
        pdf_path = pdf_files[choice]
    elif choice == "5":
        custom_path = input("Enter PDF path: ").strip()
        pdf_path = Path(custom_path)
    else:
        print("❌ Invalid choice")
        return
    
    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    # Extract
    try:
        logger.info(f"\n🚀 Starting extraction from: {pdf_path.name}\n")
        
        results = extractor.extract_from_pdf(str(pdf_path))
        
        # Save results
        output_dir = Path(__file__).parent / "data" / "processed" / "extracted_json"
        output_file = output_dir / f"{pdf_path.stem}_extracted.json"
        
        extractor.save_results(results, str(output_file))
        
        # Display summary
        print("\n" + "="*80)
        print("✅ EXTRACTION COMPLETED SUCCESSFULLY")
        print("="*80)
        
        for entity in ["Bank", "Group"]:
            for year in ["Year1", "Year2"]:
                total_fields = sum(
                    len(results[entity][year].get(stmt, {}))
                    for stmt in results[entity][year]
                )
                print(f"📊 {entity} {year}: {total_fields} fields extracted")
        
        print(f"\n💾 Results saved to: {output_file}")
        print("="*80 + "\n")
        
    except Exception as e:
        logger.error(f"❌ Extraction failed: {e}", exc_info=True)


if __name__ == "__main__":
    main()
