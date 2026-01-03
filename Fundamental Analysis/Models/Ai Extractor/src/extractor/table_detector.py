"""
Table Detector
Detects and extracts table structures from PDF pages.
"""

import pdfplumber
from typing import List, Dict, Any


class TableDetector:
    """Detect and extract tables from PDF pages."""
    
    def __init__(self):
        """Initialize table detector."""
        # Try text-based strategy first (better for multi-column layouts)
        self.table_settings_text = {
            "vertical_strategy": "text",
            "horizontal_strategy": "text",
            "intersection_tolerance": 3
        }
        
        # Fallback to lines strategy
        self.table_settings_lines = {
            "vertical_strategy": "lines",
            "horizontal_strategy": "lines",
            "intersection_tolerance": 5
        }
    
    def detect_tables(self, pdf, page_range: List[int]) -> List[Dict[str, Any]]:
        """
        Extract tables from specified page range.
        
        Args:
            pdf: pdfplumber PDF object
            page_range: List of page numbers [start, end]
        
        Returns:
            List of table dictionaries with rows and metadata
        """
        tables = []
        
        for page_num in range(page_range[0], page_range[1] + 1):
            if page_num >= len(pdf.pages):
                continue
                
            page = pdf.pages[page_num]
            
            # Try with text strategy first (better for multi-column layouts)
            page_tables = page.extract_tables(self.table_settings_text)
            
            # If no good tables found, try lines-based extraction
            if not page_tables or all(len(t[0]) < 3 for t in page_tables if t):
                page_tables = page.extract_tables(self.table_settings_lines)
            
            # Process each table
            for idx, table in enumerate(page_tables):
                if table and len(table) > 2:  # At least header + 2 data rows
                    # Check if this is a real table (has multiple columns)
                    if len(table[0]) >= 2:
                        tables.append({
                            'page_num': page_num,
                            'table_idx': idx,
                            'rows': table,
                            'row_count': len(table)
                        })
        
        return tables
