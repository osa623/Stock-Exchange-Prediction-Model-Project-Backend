"""
Simplified Financial Statement Page Image Extractor
Only extracts and saves statement pages as images (no data extraction)
"""

import logging
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent))

from src.locator.page_locator import PageLocator
from src.utils.image_saver import StatementImageSaver

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point for image extraction."""
    
    print("\n" + "="*80)
    print("📷 FINANCIAL STATEMENT PAGE IMAGE EXTRACTOR")
    print("="*80)
    print("📄 Locates financial statement pages and saves them as images")
    print("="*80 + "\n")
    
    # Initialize components
    page_locator = PageLocator(min_confidence=0.5)
    image_saver = StatementImageSaver(output_base_dir="app/statement_images")
    
    # Define PDF paths
    data_dir = Path(__file__).parent / "data" / "raw"
    
    # Available PDFs
    pdf_files = {
        "1": ("Pan Asia Banking Corporation (PABC)", data_dir / "pabc" / "pabc.pdf"),
        "2": ("HNB Bank", data_dir / "hnb" / "hnb.pdf"),
        "3": ("Commercial Bank", data_dir / "commercial" / "Commerical.pdf"),
        "4": ("DFCC Bank", data_dir / "dfcc" / "DFCC.pdf"),
        "5": ("Sampath Bank", data_dir / "samp" / "SAMP.pdf"),
        "6": ("NDB Bank", data_dir / "ndb" / "NDB.pdf"),
        "7": ("Custom path", None)
    }
    
    # Display menu
    
    # Display menu
    print("Select a PDF to process:")
    for key, (name, _) in pdf_files.items():
        print(f"{key}. {name}")
    
    choice = input("\nEnter choice (1-7): ").strip()
    
    if choice == "7":
        custom_path = input("Enter PDF path: ").strip()
        pdf_path = Path(custom_path)
    elif choice in pdf_files:
        _, pdf_path = pdf_files[choice]
    else:
        print("❌ Invalid choice")
        return
    
    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        return
    
    # Process PDF
    try:
        logger.info(f"\n🚀 Processing: {pdf_path.name}\n")
        
        # Stage 1: Locate statement pages
        logger.info("=" * 80)
        logger.info("📍 STAGE 1: LOCATING STATEMENT PAGES")
        logger.info("=" * 80)
        
        page_locations = page_locator.locate_statements(str(pdf_path))
        best_locations = page_locator.get_best_candidates(page_locations, top_n=1)
        
        # Print summary
        page_locator.print_summary(best_locations)
        
        # Stage 2: Save images
        logger.info("\n" + "=" * 80)
        logger.info("📷 STAGE 2: SAVING STATEMENT PAGE IMAGES")
        logger.info("=" * 80)
        
        saved_images = image_saver.save_statement_images(
            pdf_path=str(pdf_path),
            page_locations=best_locations
        )
        
        # Display summary
        print("\n" + "="*80)
        print("✅ IMAGE EXTRACTION COMPLETE")
        print("="*80)
        
        total_images = sum(len(imgs) for imgs in saved_images.values())
        print(f"📊 Total images saved: {total_images}")
        
        for statement, images in saved_images.items():
            print(f"   - {statement}: {len(images)} pages")
        
        company_dir = image_saver.get_company_directory(pdf_path.stem)
        print(f"\n💾 Images saved to: {company_dir}")
        print("="*80 + "\n")
        
    except Exception as e:
        logger.error(f"❌ Processing failed: {e}", exc_info=True)


if __name__ == "__main__":
    main()
