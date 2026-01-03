"""Test ToC detection on Commercial Bank PDF"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pdfplumber
from src.locator.toc_detector import TOCDetector

# Open PDF
pdf_path = "data/raw/commercial/Commerical.pdf"
print(f"Opening PDF: {pdf_path}\n")

with pdfplumber.open(pdf_path) as pdf:
    detector = TOCDetector()
    
    # Step 1: Find ToC pages
    print("=" * 80)
    print("STEP 1: Detecting ToC Pages")
    print("=" * 80)
    toc_pages = detector.detect_toc_pages(pdf)
    print(f"ToC pages found: {toc_pages}")
    
    if toc_pages:
        print("\nToC Page Content (first 50 lines):")
        for toc_page in toc_pages[:2]:  # Show first 2 ToC pages
            page = pdf.pages[toc_page]
            text = page.extract_text() or ""
            lines = text.split('\n')[:50]
            print(f"\n--- ToC Page {toc_page + 1} ---")
            for i, line in enumerate(lines, 1):
                print(f"{i:3d}: {line}")
    
    # Step 2: Extract entries
    if toc_pages:
        print("\n" + "=" * 80)
        print("STEP 2: Extracting Statement Entries from ToC")
        print("=" * 80)
        toc_entries = detector.extract_entries_from_toc(pdf, toc_pages)
        
        for statement_type, entries in toc_entries.items():
            if entries:
                print(f"\n{statement_type}:")
                for entry in entries:
                    print(f"  - '{entry.title}' → Page {entry.reported_page}")
    
    # Step 3: Compute offset
    if toc_pages and any(toc_entries.values()):
        print("\n" + "=" * 80)
        print("STEP 3: Computing PDF Page Offset")
        print("=" * 80)
        offset = detector.compute_pdf_page_offset(pdf, toc_entries)
        print(f"Computed offset: {offset}")
        print(f"(Meaning: PDF page index = Reported page + {offset})")
        
        # Show what pages we'll check
        print("\nExpected PDF pages:")
        for statement_type, entries in toc_entries.items():
            if entries:
                for entry in entries:
                    pdf_page_idx = entry.reported_page + offset
                    print(f"  {statement_type}: Reported {entry.reported_page} → PDF index {pdf_page_idx} (PDF page {pdf_page_idx + 1})")
    
    # Step 4: Full results
    print("\n" + "=" * 80)
    print("STEP 4: Full Results")
    print("=" * 80)
    results = detector.get_statement_pages_from_toc(pdf)
    
    for statement_type, candidates in results.items():
        if candidates:
            print(f"\n{statement_type}:")
            for candidate in candidates:
                print(f"  Pages: {candidate['page_range']}")
                print(f"  Confidence: {candidate['confidence']}")
                print(f"  Evidence: {candidate['evidence']}")
                if 'metadata' in candidate:
                    print(f"  Metadata: {candidate['metadata']}")
