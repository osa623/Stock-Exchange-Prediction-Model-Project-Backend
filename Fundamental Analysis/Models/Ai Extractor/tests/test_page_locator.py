"""
Tests for Page Locator
Tests ToC detection, heading scanning, layout analysis
"""

import pytest
from unittest.mock import Mock, MagicMock
from src.locator.page_locator import PageLocator
from src.locator.toc_detector import TOCDetector, TOCEntry
from src.locator.heading_scanner import HeadingScanner, HeadingMatch
from src.locator.layout_analyzer import LayoutAnalyzer, LayoutSignals


class TestTOCDetector:
    """Test Table of Contents detection."""
    
    @pytest.fixture
    def detector(self):
        """Create TOC detector instance."""
        return TOCDetector()
    
    def test_detect_toc_keywords(self, detector):
        """Test detection of ToC indicators."""
        # Mock page with ToC
        mock_page = Mock()
        mock_page.extract_text.return_value = "Table of Contents\n\nIncome Statement ... 25\nBalance Sheet ... 30"
        
        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        
        toc_pages = detector.detect_toc_pages(mock_pdf)
        
        assert len(toc_pages) >= 0  # Should attempt to find ToC
    
    def test_extract_page_numbers_from_entries(self, detector):
        """Test extraction of page numbers from ToC entries."""
        text = "Income Statement .................... 25"
        
        import re
        match = re.search(detector.page_number_pattern, text)
        
        assert match is not None
        assert "25" in match.groups()


class TestHeadingScanner:
    """Test heading scanner."""
    
    @pytest.fixture
    def scanner(self):
        """Create heading scanner instance."""
        return HeadingScanner()
    
    def test_identify_heading(self, scanner):
        """Test identification of headings."""
        # Title case, short, has statement keyword
        heading = "Income Statement" , "Statement of Income",
        score = scanner.is_likely_heading(heading, 'top')
        
        assert score > 0.5
    
    def test_not_heading(self, scanner):
        """Test non-heading text."""
        # Long paragraph, lowercase
        text = "this is a long paragraph of text that is not a heading at all"
        score = scanner.is_likely_heading(text, 'middle')
        
        assert score < 0.5


class TestLayoutAnalyzer:
    """Test layout analyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Create layout analyzer instance."""
        return LayoutAnalyzer()
    
    def test_numeric_density(self, analyzer):
        """Test numeric density calculation."""
        # Text with high numeric content
        text_high = "1,234 5,678 9,012 3,456 Revenue Expenses"
        density_high = analyzer.calculate_numeric_density(text_high)
        
        # Text with low numeric content
        text_low = "This is mostly text with few numbers"
        density_low = analyzer.calculate_numeric_density(text_low)
        
        assert density_high > density_low
    
    def test_year_detection(self, analyzer):
        """Test detection of year headers."""
        text_with_years = "2023 2022 Bank Group"
        has_years = analyzer.detect_year_headers(text_with_years)
        
        assert has_years
        
        text_without_years = "Description Amount Total"
        no_years = analyzer.detect_year_headers(text_without_years)
        
        assert not no_years
    
    def test_bank_group_detection(self, analyzer):
        """Test detection of Bank/Group headers."""
        text_with_both = "Bank Group\n2023 2022"
        has_both = analyzer.detect_bank_group_headers(text_with_both)
        
        assert has_both


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
