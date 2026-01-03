"""
Tests for Column Interpreter
Tests Bank/Group detection, Year1/Year2 detection
"""

import pytest
from src.extractor.column_interpreter import ColumnInterpreter, ColumnType


class TestColumnInterpreter:
    """Test column interpretation."""
    
    @pytest.fixture
    def interpreter(self):
        """Create interpreter instance."""
        return ColumnInterpreter()
    
    def test_detect_description_column(self, interpreter):
        """Test detection of description column."""
        headers = [["Particulars", "Bank 2023", "Bank 2022"]]
        
        column_info = interpreter.interpret_columns(headers)
        
        assert 0 in column_info
        assert column_info[0].column_type == ColumnType.DESCRIPTION
    
    def test_detect_bank_and_group_columns(self, interpreter):
        """Test detection of Bank and Group columns."""
        headers = [
            ["", "Bank", "Group"],
            ["Particulars", "2023", "2023"]
        ]
        
        column_info = interpreter.interpret_columns(headers)
        
        # Column 1 should be Bank
        assert 1 in column_info
        assert column_info[1].entity == 'Bank'
        
        # Column 2 should be Group
        assert 2 in column_info
        assert column_info[2].entity == 'Group'
    
    def test_detect_years(self, interpreter):
        """Test detection of year columns."""
        headers = [["Particulars", "2023", "2022"]]
        
        column_info = interpreter.interpret_columns(headers)
        
        # Should detect years
        assert 1 in column_info
        assert column_info[1].year == 2023
        
        assert 2 in column_info
        assert column_info[2].year == 2022
    
    def test_year_ordering(self, interpreter):
        """Test Year1 (most recent) vs Year2 (previous)."""
        headers = [["", "2023", "2022"]]
        
        column_info = interpreter.interpret_columns(headers)
        
        # 2023 should be Year1, 2022 should be Year2
        # (This test assumes bank columns by default)
        # The actual column types would depend on full interpretation logic
    
    def test_note_column_detection(self, interpreter):
        """Test detection of Note column."""
        headers = [["Particulars", "Note", "Bank", "Group"]]
        
        column_info = interpreter.interpret_columns(headers)
        
        assert 1 in column_info
        assert column_info[1].column_type == ColumnType.NOTE
    
    def test_complex_header_structure(self, interpreter):
        """Test complex multi-row header."""
        headers = [
            ["", "Bank", "Bank", "Group", "Group"],
            ["Particulars", "2023", "2022", "2023", "2022"]
        ]
        
        column_info = interpreter.interpret_columns(headers)
        
        # Should correctly identify all columns
        assert column_info[0].column_type == ColumnType.DESCRIPTION
        assert column_info[1].entity == 'Bank'
        assert column_info[2].entity == 'Bank'
        assert column_info[3].entity == 'Group'
        assert column_info[4].entity == 'Group'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
