"""Value normalizer module."""

from typing import Optional, Any
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ValueNormalizer:
    """Normalize extracted values."""
    
    def __init__(self, target_currency: str = 'LKR', target_unit: str = 'thousands'):
        """
        Initialize value normalizer.
        
        Args:
            target_currency: Target currency for normalization
            target_unit: Target unit for normalization
        """
        self.target_currency = target_currency
        self.target_unit = target_unit
        
        self.unit_multipliers = {
            'ones': 1,
            'thousands': 1_000,
            'millions': 1_000_000,
            'billions': 1_000_000_000
        }
        
        logger.info(f"Initialized ValueNormalizer: {target_currency} {target_unit}")
    
    def normalize_value(
        self, 
        value: float, 
        source_unit: Optional[str] = None
    ) -> Optional[float]:
        """
        Normalize value to target unit.
        
        Args:
            value: Value to normalize
            source_unit: Unit of source value
        
        Returns:
            Normalized value
        """
        if value is None:
            return None
        
        try:
            if source_unit and source_unit in self.unit_multipliers:
                # Convert to ones
                value_in_ones = value * self.unit_multipliers[source_unit]
                
                # Convert to target unit
                normalized = value_in_ones / self.unit_multipliers[self.target_unit]
                
                return round(normalized, 2)
            
            # If no source unit specified, assume it's already in target unit
            return round(value, 2)
            
        except Exception as e:
            logger.error(f"Error normalizing value: {str(e)}")
            return value
    
    def normalize_dataset(
        self, 
        data: dict, 
        source_unit: Optional[str] = None
    ) -> dict:
        """
        Normalize all values in a dataset.
        
        Args:
            data: Dictionary of field names to values
            source_unit: Unit of source values
        
        Returns:
            Normalized dataset
        """
        normalized = {}
        
        for key, value in data.items():
            if isinstance(value, (int, float)):
                normalized[key] = self.normalize_value(value, source_unit)
            else:
                normalized[key] = value
        
        logger.info(f"Normalized {len(normalized)} values")
        return normalized
