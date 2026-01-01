"""JSON storage module."""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any
from src.utils.logger import get_logger
from src.utils.helpers import ensure_dir

logger = get_logger(__name__)


def save_json(
    data: Dict[str, Any], 
    output_path: str, 
    pretty: bool = True
) -> bool:
    """
    Save data to JSON file.
    
    Args:
        data: Data to save
        output_path: Path to output file
        pretty: Whether to format JSON with indentation
    
    Returns:
        True if successful, False otherwise
    """
    try:
        output_path = Path(output_path)
        ensure_dir(output_path.parent)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            if pretty:
                json.dump(data, f, indent=2, ensure_ascii=False)
            else:
                json.dump(data, f, ensure_ascii=False)
        
        logger.info(f"Saved JSON to: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving JSON: {str(e)}")
        return False


def save_extraction_result(
    extracted_data: Dict[str, Any],
    metadata: Dict[str, Any],
    output_dir: str,
    company_name: str
) -> str:
    """
    Save extraction result with metadata.
    
    Args:
        extracted_data: Extracted financial data
        metadata: Extraction metadata
        output_dir: Output directory
        company_name: Company name
    
    Returns:
        Path to saved file
    """
    try:
        # Create output structure with clear organization
        result = {
            'metadata': {
                'company_name': company_name,
                'extraction_date': datetime.now().isoformat(),
                'extractor_version': '1.0',
                **metadata
            },
            'financial_statements': extracted_data,
            'extraction_summary': {
                'total_sections': len(extracted_data),
                'fields_per_section': {
                    section: len([v for v in values.values() if v is not None])
                    for section, values in extracted_data.items()
                }
            }
        }
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{company_name.replace(' ', '_')}_{timestamp}.json"
        output_path = Path(output_dir) / filename
        
        # Ensure output directory exists
        ensure_dir(output_path.parent)
        
        # Save with pretty formatting
        save_json(result, str(output_path), pretty=True)
        
        logger.info(f"Saved extraction result to: {output_path}")
        
        return str(output_path)
        
    except Exception as e:
        logger.error(f"Error saving extraction result: {str(e)}")
        return ""


def load_json(file_path: str) -> Dict[str, Any]:
    """
    Load data from JSON file.
    
    Args:
        file_path: Path to JSON file
    
    Returns:
        Loaded data dictionary
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Loaded JSON from: {file_path}")
        return data
        
    except Exception as e:
        logger.error(f"Error loading JSON: {str(e)}")
        return {}
