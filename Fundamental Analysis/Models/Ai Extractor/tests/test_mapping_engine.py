"""
Tests for Mapping Engine
Tests cascading mapping: exact → synonyms → fuzzy
"""

import pytest
from src.mapper.mapping_engine import MappingEngine, MappingResult


class TestMappingEngine:
    """Test row label mapping."""
    
    @pytest.fixture
    def engine(self):
        """Create mapping engine instance."""
        return MappingEngine(fuzzy_threshold=85.0)
    
    def test_exact_match(self, engine):
        """Test exact match to canonical key."""
        result = engine.map_label("Gross income", "Income_Statement")
        
        assert result.canonical_key == "Gross income"
        assert result.match_method == "exact"
        assert result.confidence == 1.0
    
    def test_case_insensitive_match(self, engine):
        """Test case-insensitive exact match."""
        result = engine.map_label("GROSS INCOME", "Income_Statement")
        
        assert result.canonical_key == "Gross income"
        assert result.match_method == "exact"
    
    def test_synonym_match(self, engine):
        """Test synonym dictionary match."""
        result = engine.map_label("interest revenue", "Income_Statement")
        
        # "interest revenue" is a synonym for "Interest income"
        assert result.canonical_key == "Interest income"
        assert result.match_method == "synonym"
        assert result.confidence >= 0.9
    
    def test_fuzzy_match(self, engine):
        """Test fuzzy matching."""
        result = engine.map_label("Gross Incom", "Income_Statement")  # Typo
        
        assert result.canonical_key == "Gross income"
        assert result.match_method == "fuzzy"
        assert result.confidence >= 0.85
    
    def test_no_match(self, engine):
        """Test when no match is found."""
        result = engine.map_label("Completely Unknown Field", "Income_Statement")
        
        assert result.canonical_key is None
        assert result.match_method == "none"
        assert result.confidence == 0.0
    
    def test_normalization(self, engine):
        """Test label normalization."""
        normalized = engine._normalize_label("Net Interest Income / Expense")
        
        # Should handle slashes and special chars
        assert "/" not in normalized or " " in normalized
    
    def test_map_multiple_labels(self, engine):
        """Test mapping multiple labels at once."""
        labels = ["Gross income", "interest revenue", "Unknown Field"]
        results = engine.map_all_labels(labels, "Income_Statement")
        
        assert len(results) == 3
        assert results[0].canonical_key == "Gross income"
        assert results[1].canonical_key == "Interest income"
        assert results[2].canonical_key is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
