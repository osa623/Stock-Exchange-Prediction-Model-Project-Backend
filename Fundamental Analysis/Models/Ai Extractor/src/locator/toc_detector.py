"""
Table of Contents Detector
Detects and parses ToC to identify statement pages with reported page numbers.
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import pdfplumber


@dataclass
class TOCEntry:
    """Represents a ToC entry with title and reported page number."""
    title: str
    reported_page: int
    toc_page: int  # The ToC page where this entry was found
    confidence: float = 1.0


class TOCDetector:
    """Detect and parse Table of Contents to find statement pages."""
    
    def __init__(self):
        """Initialize ToC detector with common patterns."""

        self.toc_indicators = [
            r'CONTENTS',
            r'contents',
            r'table\s+of\s+contents',
        ]
        
        # Statement titles to look for
        self.statement_patterns = {
            'Income_Statement': [
                r'INCOME\s+STATEMENT',
                r'statement\s+of\s+(profit\s+(or\s+)?loss|comprehensive\s+income|income)',
                r'income\s+statement',
                r'profit\s+(and|&|or)\s+loss',
            ],
            'Financial Position Statement': [
                r'STATEMENT\s+OF\s+FINANCIAL\s+POSITION',
                r'balance\s+sheet',
                r'statement\s+of\s+assets\s+and\s+liabilities',
            ],
            'Cash Flow Statement': [
                r'STATEMENT\s+OF\s+CASH\s+FLOWS',
                r'statement\s+of\s+cash\s+flows?',
                r'cash\s+flow\s+statement',
            ]
        }
        
        # Pattern to extract page numbers from ToC entries
        # Format 1: "Statement Name ... 25" or "Statement Name  25"  (page at end)
        # Format 2: "25 Statement Name" (page at start)
        self.page_at_end_pattern = r'[.\s]{2,}(\d{1,4})\s*$'
        self.page_at_start_pattern = r'^\s*(\d{1,4})\s+(.+)$'
    
    def detect_toc_pages(self, pdf) -> List[int]:
        """
        Detect which pages contain the Table of Contents.
        
        Args:
            pdf: pdfplumber PDF object
            
        Returns:
            List of ToC page numbers (0-indexed)
        """
        toc_pages = []
        
        # Usually ToC is in first 20 pages
        search_limit = min(10, len(pdf.pages))
        
        for page_num in range(search_limit):
            try:
                page = pdf.pages[page_num]
                text = page.extract_text() or ""
                text_lower = text.lower()
                
                # Check for ToC indicators
                for pattern in self.toc_indicators:
                    if re.search(pattern, text_lower, re.IGNORECASE):
                        toc_pages.append(page_num)
                        break
                        
            except Exception:
                continue
        
        return toc_pages
    
    def extract_entries_from_toc(self, pdf, toc_pages: List[int]) -> Dict[str, List[TOCEntry]]:
        """
        Extract relevant ToC entries for financial statements.
        
        Args:
            pdf: pdfplumber PDF object
            toc_pages: List of ToC page numbers
            
        Returns:
            Dictionary mapping statement types to list of TOCEntry objects
        """
        entries = {
            'Income_Statement': [],
            'Statement of Financial Position': [],
            'Statement of Cash Flows': []
        }
        
        for toc_page in toc_pages:
            try:
                page = pdf.pages[toc_page]
                text = page.extract_text() or ""
                lines = text.split('\n')
                
                # Process lines, combining multi-line entries
                i = 0
                while i < len(lines):
                    line = lines[i].strip()
                    if not line:
                        i += 1
                        continue
                    
                    line_lower = line.lower()
                    
                    # Check each statement type
                    for statement_type, patterns in self.statement_patterns.items():
                        # Skip if we already found this statement on this ToC page
                        if any(e.toc_page == toc_page for e in entries[statement_type]):
                            continue
                        
                        # Check if this line (or combined with next lines) matches any pattern
                        for pattern in patterns:
                            # Try matching just this line first
                            combined_line = line
                            combined_line_lower = line_lower
                            
                            # If no match, try combining with next 2 lines (for multi-line entries)
                            lines_to_try = [combined_line]
                            if not re.search(pattern, combined_line_lower):
                                if i + 1 < len(lines):
                                    combined_line = line + " " + lines[i + 1].strip()
                                    combined_line_lower = combined_line.lower()
                                    lines_to_try.append(combined_line)
                                if i + 2 < len(lines):
                                    combined_line = line + " " + lines[i + 1].strip() + " " + lines[i + 2].strip()
                                    combined_line_lower = combined_line.lower()
                                    lines_to_try.append(combined_line)
                            
                            # Check if any combination matches
                            matched_line = None
                            for test_line in lines_to_try:
                                if re.search(pattern, test_line.lower()):
                                    matched_line = test_line
                                    break
                            
                            if matched_line:
                                # Extract page number (look for 3-digit number in range 150-500)
                                numbers = re.findall(r'\b(\d{3})\b', matched_line)
                                statement_range_numbers = [int(n) for n in numbers if 150 <= int(n) <= 500]
                                
                                if statement_range_numbers:
                                    reported_page = statement_range_numbers[0]
                                    
                                    entry = TOCEntry(
                                        title=matched_line,
                                        reported_page=reported_page,
                                        toc_page=toc_page,
                                        confidence=0.95
                                    )
                                    entries[statement_type].append(entry)
                                    break
                        
                    i += 1
                                
            except Exception:
                continue
        
        return entries
    
    def compute_pdf_page_offset(
        self, 
        pdf,
        toc_entries: Dict[str, List[TOCEntry]]
    ) -> int:
        """
        Compute the offset between reported page numbers and actual PDF page indices.
        
        Strategy: For each reported page, scan nearby PDF pages for matching statement content.
        
        Args:
            pdf: pdfplumber PDF object
            toc_entries: Extracted ToC entries
            
        Returns:
            Page offset (pdf_page_index = reported_page + offset)
        """
        # Collect all reported pages with their statement types
        test_cases = []
        for statement_type, entries in toc_entries.items():
            for entry in entries:
                # Determine key phrases to look for
                if 'income' in statement_type.lower():
                    key_phrases = ['income statement', 'profit or loss', 'profit and loss']
                elif 'financial position' in statement_type.lower():
                    key_phrases = ['financial position', 'balance sheet', 'statement of financial position']
                elif 'cash flow' in statement_type.lower():
                    key_phrases = ['cash flow', 'statement of cash flow']
                else:
                    key_phrases = []
                
                test_cases.append({
                    'reported_page': entry.reported_page,
                    'key_phrases': key_phrases,
                    'type': statement_type
                })
        
        if not test_cases:
            return 0
        
        # Try different offsets (-5 to +10) and score them
        best_offset = 0
        best_score = 0
        
        for test_offset in range(-5, 11):
            score = 0
            
            for case in test_cases:
                pdf_page_idx = case['reported_page'] + test_offset
                
                # Check if this page exists
                if not (0 <= pdf_page_idx < len(pdf.pages)):
                    continue
                
                try:
                    page = pdf.pages[pdf_page_idx]
                    text = (page.extract_text() or "").lower()[:1500]  # First 1500 chars
                    
                    # Check if any key phrases appear
                    for phrase in case['key_phrases']:
                        if phrase in text:
                            score += 2  # Strong match
                            break
                    
                except Exception:
                    continue
            
            if score > best_score:
                best_score = score
                best_offset = test_offset
        
        return best_offset
    
    def get_statement_pages_from_toc(
        self, 
        pdf
    ) -> Dict[str, List[Dict]]:
        """
        Main method: detect ToC and extract statement page locations.
        
        Returns:
            Dictionary with statement type -> list of candidate pages with metadata
            Format: {
                'Income_Statement': [
                    {
                        'page_range': [start, end],
                        'confidence': 0.9,
                        'evidence': 'Found in ToC',
                        'source': 'toc'
                    }
                ]
            }
        """
        results = {
            'Income_Statement': [],
            'Financial Position Statement': [],
            'Cash Flow Statement': []
        }
        
        # Step 1: Detect ToC pages
        toc_pages = self.detect_toc_pages(pdf)
        if not toc_pages:
            return results  # No ToC found
        
        # Step 2: Extract entries
        toc_entries = self.extract_entries_from_toc(pdf, toc_pages)
        
        # Step 3: Compute offset
        offset = self.compute_pdf_page_offset(pdf, toc_entries)
        
        # Step 4: Convert reported pages to PDF page indices
        for statement_type, entries in toc_entries.items():
            for entry in entries:
                pdf_page_idx = entry.reported_page + offset
                
                # Clamp to valid range
                if 0 <= pdf_page_idx < len(pdf.pages):
                    # Financial statements typically span 1-2 pages each
                    page_range = [
                        pdf_page_idx,
                        min(pdf_page_idx + 1, len(pdf.pages) - 1)
                    ]
                    
                    results[statement_type].append({
                        'page_range': page_range,
                        'confidence': 0.98,  # VERY HIGH confidence for ToC-based results
                        'evidence': f"ToC entry: '{entry.title}' (reported page {entry.reported_page}, PDF page {pdf_page_idx + 1})",
                        'source': 'toc',
                        'metadata': {
                            'toc_page': entry.toc_page,
                            'reported_page': entry.reported_page,
                            'pdf_page': pdf_page_idx,
                            'offset': offset
                        }
                    })
        
        return results
