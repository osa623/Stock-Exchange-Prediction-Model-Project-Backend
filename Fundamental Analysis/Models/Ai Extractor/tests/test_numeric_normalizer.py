"""
Tests for Numeric Normalizer
Tests bracket negatives, dash nulls, comma stripping, decimal preservation
"""

import pytest
from src.extractor.numeric_normalizer import NumericNormalizer, NumericValue


class TestNumericNormalizer:
    """Test numeric value normalization."""
    
    @pytest.fixture
    def normalizer(self):
        """Create normalizer instance."""
        return NumericNormalizer()
    
    def test_simple_number(self, normalizer):
        """Test simple positive number."""
        result = normalizer.normalize("1234")
        assert result.normalized_value == 1234.0
        assert not result.is_negative
        assert not result.is_null
    
    def test_number_with_commas(self, normalizer):
        """Test number with thousands separators."""
        result = normalizer.normalize("1,234,567")
        assert result.normalized_value == 1234567.0
        assert not result.is_negative
    
    def test_number_with_decimals(self, normalizer):
        """Test number with decimal places."""
        result = normalizer.normalize("1,234.56")
        assert result.normalized_value == 1234.56
        assert not result.is_negative
    
    def test_bracketed_number_as_negative(self, normalizer):
        """Test bracketed number interpreted as negative."""
        result = normalizer.normalize("(1,234)")
        assert result.normalized_value == -1234.0
        assert result.is_negative
        assert not result.is_null
    
    def test_bracketed_decimal_as_negative(self, normalizer):
        """Test bracketed decimal as negative."""
        result = normalizer.normalize("(1,234.56)")
        assert result.normalized_value == -1234.56
        assert result.is_negative
    
    def test_dash_as_null(self, normalizer):
        """Test dash interpreted as null."""
        for dash in ["-", "–", "—", "−"]:
            result = normalizer.normalize(dash)
            assert result.normalized_value is None
            assert result.is_null
    
    def test_empty_as_null(self, normalizer):
        """Test empty string as null."""
        result = normalizer.normalize("")
        assert result.normalized_value is None
        assert result.is_null
    
    def test_none_as_null(self, normalizer):
        """Test None as null."""
        result = normalizer.normalize(None)
        assert result.normalized_value is None
        assert result.is_null
    
    def test_currency_symbol_removal(self, normalizer):
        """Test currency symbols are stripped."""
        result = normalizer.normalize("Rs. 1,234.56")
        assert result.normalized_value == 1234.56
        
        result = normalizer.normalize("$1,234.56")
        assert result.normalized_value == 1234.56
    
    def test_negative_with_minus_sign(self, normalizer):
        """Test explicit negative with minus sign."""
        result = normalizer.normalize("-1,234.56")
        assert result.normalized_value == -1234.56
        assert result.is_negative
    
    def test_nil_as_null(self, normalizer):
        """Test 'nil' interpreted as null."""
        result = normalizer.normalize("nil")
        assert result.normalized_value is None
        assert result.is_null
    
    def test_unit_conversion(self, normalizer):
        """Test unit conversion."""
        value = normalizer.normalize("1000")
        
        # Convert from thousands to millions
        converted = normalizer.apply_unit_conversion(value, 'thousands', 'millions')
        assert converted.normalized_value == 1.0
        
        # Convert from millions to thousands
        converted = normalizer.apply_unit_conversion(value, 'millions', 'thousands')
        assert converted.normalized_value == 1000000.0
    
    def test_normalize_row(self, normalizer):
        """Test normalizing a row of values."""
        row = ["1,234", "(567)", "-", "8.90"]
        results = normalizer.normalize_row(row)
        
        assert len(results) == 4
        assert results[0].normalized_value == 1234.0
        assert results[1].normalized_value == -567.0
        assert results[2].is_null
        assert results[3].normalized_value == 8.90


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
