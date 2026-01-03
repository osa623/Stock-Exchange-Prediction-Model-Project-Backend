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
        # Patterns that indicate a ToC page
        self.toc_indicators = [
            r'^\s*contents\s*$',
            r'table\s+of\s+contents',
            r'^\s*index\s*$',
        ]
        
        # Statement titles to look for
        self.statement_patterns = {
            'Income_Statement': [
                r'statement\s+of\s+(profit\s+(or\s+)?loss|comprehensive\s+income|income)',
                r'income\s+statement',
                r'profit\s+(and|&|or)\s+loss',
            ],
            'Financial Position Statement': [
                r'statement\s+of\s+financial\s+position',
                r'balance\s+sheet',
                r'statement\s+of\s+assets\s+and\s+liabilities',
            ],
            'Cash Flow Statement': [
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
        search_limit = min(20, len(pdf.pages))
        
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
            'Financial Position Statement': [],
            'Cash Flow Statement': []
        }
        
        for toc_page in toc_pages:
            try:
                page = pdf.pages[toc_page]
                text = page.extract_text() or ""
                lines = text.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # First, check if this line contains any statement keywords
                    line_lower = line.lower()
                    has_statement_keyword = False
                    for patterns in self.statement_patterns.values():
                        for pattern in patterns:
                            if re.search(pattern, line_lower):
                                has_statement_keyword = True
                                break
                        if has_statement_keyword:
                            break
                    
                    if not has_statement_keyword:
                        continue  # Skip lines that don't mention statements
                    
                    # Find ALL numbers in the line
                    all_numbers = re.findall(r'\b(\d{1,4})\b', line)
                    if not all_numbers:
                        continue
                    
                    # For lines with statement keywords, the page number is likely:
                    # 1. The LAST number in the line (most common)
                    # 2. Or a number in range 200-500 (typical for financial statements)
                    
                    # First try: Look for numbers in financial statement range (200-500)
                    statement_range_numbers = [int(n) for n in all_numbers if 200 <= int(n) <= 500]
                    
                    if statement_range_numbers:
                        # Use the first number in statement range
                        reported_page = statement_range_numbers[0]
                    else:
                        # Fallback: use the last number in the line
                        reported_page = int(all_numbers[-1])
                    
                    # Extract title (just use the whole line for now, will match pattern below)
                    title = line
                    
                    # Match against statement patterns
                    for statement_type, patterns in self.statement_patterns.items():
                        matched = False
                        for pattern in patterns:
                            if re.search(pattern, title, re.IGNORECASE):
                                entry = TOCEntry(
                                    title=title,
                                    reported_page=reported_page,
                                    toc_page=toc_page,
                                    confidence=0.95  # Very high confidence for ToC matches
                                )
                                entries[statement_type].append(entry)
                                matched = True
                                break
                        if matched:
                            break
                                
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
        
        Strategy: Check pages around the reported page numbers to find matching content.
        
        Args:
            pdf: pdfplumber PDF object
            toc_entries: Extracted ToC entries
            
        Returns:
            Page offset (reported_page + offset = pdf_index)
        """
        # Collect all reported pages and titles
        candidates = []
        for statement_type, entries in toc_entries.items():
            for entry in entries:
                # Extract key words from title for matching
                title_lower = entry.title.lower()
                key_words = []
                if 'income' in title_lower:
                    key_words = ['income', 'statement', 'profit', 'loss']
                elif 'financial position' in title_lower or 'balance' in title_lower:
                    key_words = ['financial position', 'balance sheet', 'assets', 'liabilities']
                elif 'cash flow' in title_lower:
                    key_words = ['cash flow', 'statement']
                
                candidates.append({
                    'reported_page': entry.reported_page,
                    'key_words': key_words,
                    'title': entry.title
                })
        
        if not candidates:
            return 0
        
        # Try different offsets and score them
        best_offset = 0
        best_score = 0
        
        # Test offsets from -10 to +10
        for test_offset in range(-10, 11):
            score = 0
            
            for candidate in candidates:
                pdf_page_idx = candidate['reported_page'] + test_offset
                
                # Check if this page exists
                if not (0 <= pdf_page_idx < len(pdf.pages)):
                    continue
                
                try:
                    page = pdf.pages[pdf_page_idx]
                    text = (page.extract_text() or "").lower()
                    
                    # Check if key words appear on this page
                    words_found = sum(1 for word in candidate['key_words'] if word in text)
                    score += words_found
                    
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
