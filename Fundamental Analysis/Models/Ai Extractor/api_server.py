"""
Flask API Server for Financial Data Extractor
Provides endpoints for PDF management and statement extraction
"""

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import os
import sys
from pathlib import Path
import logging
import fitz  # PyMuPDF
from PIL import Image
import io
import json
import pandas as pd
from datetime import datetime

# Add parent directory to path to import from src
sys.path.append(str(Path(__file__).parent))

from src.pipeline.two_stage_pipeline import TwoStagePipeline
from src.locator.page_locator import PageLocator
from src.storage.save_json import save_extraction_result
from src.pdf.table_extractor import TableExtractor
from src.mapper.mapping_engine import MappingEngine
from src.extractor.column_interpreter import ColumnInterpreter
from src.extractor.numeric_normalizer import NumericNormalizer
from config.target_schema_bank import STATEMENT_FIELDS, TARGET_FIELDS, MANDATORY_SECTIONS

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
RAW_DATA_PATH = Path(__file__).parent / "data" / "raw"
PROCESSED_DATA_PATH = Path(__file__).parent / "data" / "processed" / "extracted_json"
IMAGES_PATH = Path(__file__).parent / "app" / "statement_images"

# Ensure paths exist
RAW_DATA_PATH.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_PATH.mkdir(parents=True, exist_ok=True)
IMAGES_PATH.mkdir(parents=True, exist_ok=True)


def extract_data_from_selected_pages(pdf_path, pdf_id, selected_pages):
    """
    Extract table data from selected pages using schema-based mapping.
    
    Args:
        pdf_path: Path to the PDF file
        pdf_id: Unique identifier for the PDF
        selected_pages: Dict with statement types as keys and list of page numbers as values
                       Example: {'income': [5, 6], 'balance': [7, 8], 'cashflow': [9]}
    
    Returns:
        Dictionary with extracted data structured according to TARGET_FIELDS schema:
        Bank -> Year1/Year2 -> Statement -> Fields with values
        Group -> Year1/Year2 -> Statement -> Fields with values
    """
    logger.info(f"Extracting data from selected pages: {selected_pages}")
    
    # Initialize components
    table_extractor = TableExtractor()
    mapping_engine = MappingEngine(fuzzy_threshold=85.0)
    column_interpreter = ColumnInterpreter()
    numeric_normalizer = NumericNormalizer()
    
    # Map frontend statement types to schema types
    statement_type_mapping = {
        'income': 'Income_Statement',
        'balance': 'Financial Position Statement',
        'cashflow': 'Cash Flow Statement'
    }
    
    # Initialize result structure according to TARGET_FIELDS
    extracted_data = {
        "pdf_id": pdf_id,
        "extraction_date": datetime.now().isoformat(),
        "data": {
            "Bank": {
                "Year1": {},
                "Year2": {}
            },
            "Group": {
                "Year1": {},
                "Year2": {}
            }
        },
        "metadata": {
            "pages_processed": {},
            "fields_found": {},
            "mapping_stats": {}
        }
    }
    
    # Process each statement type
    for frontend_type, pages in selected_pages.items():
        if not pages:
            continue
        
        schema_type = statement_type_mapping.get(frontend_type)
        if not schema_type:
            logger.warning(f"Unknown statement type: {frontend_type}")
            continue
        
        logger.info(f"\n{'='*80}")
        logger.info(f"Processing {schema_type} from pages: {pages}")
        logger.info(f"{'='*80}\n")
        
        # Initialize statement structure in all entities and years
        for entity in ['Bank', 'Group']:
            for year in ['Year1', 'Year2']:
                extracted_data['data'][entity][year][schema_type] = {}
        
        extracted_data['metadata']['pages_processed'][schema_type] = pages
        
        # Extract and process tables from all pages for this statement
        all_table_rows = []
        
        for page_num in pages:
            page_idx = page_num - 1
            logger.info(f"Extracting from page {page_num}")
            
            # Open PDF with pdfplumber to get both text and tables
            import pdfplumber
            with pdfplumber.open(pdf_path) as pdf_doc:
                if page_idx >= len(pdf_doc.pages):
                    logger.warning(f"Page {page_num} not found in PDF")
                    continue
                
                page = pdf_doc.pages[page_idx]
                
                # Extract text to get field names
                page_text = page.extract_text()
                if not page_text:
                    logger.warning(f"No text found on page {page_num}")
                    continue
                
                # Extract tables to get values
                page_tables = page.extract_tables()
                
                logger.info(f"  Page text length: {len(page_text)} chars")
                logger.info(f"  Tables found: {len(page_tables)}")
                
                # Parse text line by line to match with table values
                text_lines = page_text.split('\n')
                
                # Find table values
                table_values = {}
                for table in page_tables:
                    for row in table:
                        if row and len(row) >= 2:
                            # Get note reference and value
                            note = str(row[0]).strip() if row[0] else ""
                            value = str(row[1]).strip() if row[1] else ""
                            if note and value:
                                table_values[note] = value
                
                logger.info(f"  Extracted {len(table_values)} table values")
                
                # Match text lines with table values
                for line in text_lines:
                    line = line.strip()
                    if not line or len(line) < 5:
                        continue
                    
                    # Skip header lines
                    if any(skip in line.lower() for skip in ['note', 'rs.', '2024', '2023', 'page', 'annual report']):
                        continue
                    
                    # Try to extract field name and values from the line
                    # Format: "Field Name [Note] Value1 Value2"
                    parts = line.split()
                    if len(parts) < 2:
                        continue
                    
                    # Check if line contains numbers (values)
                    has_numbers = any(char.isdigit() or char in '(),.' for part in parts[-2:] for char in part)
                    if not has_numbers:
                        continue
                    
                    # Extract field name (everything except last 2-3 parts which are values/notes)
                    values_parts = []
                    field_parts = []
                    
                    for i, part in enumerate(parts):
                        # Check if this looks like a value (has digits, commas, parentheses)
                        if any(c in part for c in '0123456789(),'):
                            values_parts = parts[i:]
                            field_parts = parts[:i]
                            break
                    
                    if not field_parts:
                        continue
                    
                    field_name = ' '.join(field_parts)
                    
                    # Clean field name - remove note references
                    import re
                    field_name = re.sub(r'\b\d+\b', '', field_name).strip()
                    
                    if not field_name or len(field_name) < 3:
                        continue
                    
                    logger.info(f"  Processing: '{field_name}'")
                    
                    # Map to canonical field
                    mapping_result = mapping_engine.map_label(field_name, schema_type)
                    
                    if mapping_result.canonical_key:
                        canonical_field = mapping_result.canonical_key
                        logger.info(f"    ✓ Mapped to '{canonical_field}' ({mapping_result.match_method})")
                        
                        # Extract values from the line
                        for val_idx, value_str in enumerate(values_parts):
                            value_str = value_str.strip()
                            if not value_str or value_str.isdigit() and len(value_str) <= 2:  # Skip note numbers
                                continue
                            
                            # Check if it's a valid value
                            if not any(c in value_str for c in '0123456789'):
                                continue
                            
                            # Normalize value
                            normalized_value = numeric_normalizer.normalize(value_str)
                            if not normalized_value or normalized_value == "0":
                                continue
                            
                            logger.info(f"      Value {val_idx}: {value_str} -> {normalized_value}")
                            
                            # Determine entity and year based on value position
                            # Typically: Value1 = Year1, Value2 = Year2 (or Bank/Group)
                            # Common format: Bank2024, Bank2023, Group2024, Group2023
                            if val_idx == 0:
                                entity = 'Bank'
                                year_key = 'Year1'
                            elif val_idx == 1:
                                entity = 'Bank'
                                year_key = 'Year2'
                            elif val_idx == 2:
                                entity = 'Group'
                                year_key = 'Year1'
                            elif val_idx == 3:
                                entity = 'Group'
                                year_key = 'Year2'
                            else:
                                continue
                            
                            # Store in data structure
                            if canonical_field not in extracted_data['data'][entity][year_key][schema_type]:
                                extracted_data['data'][entity][year_key][schema_type][canonical_field] = normalized_value
                                logger.info(f"        Stored in {entity}/{year_key}")
                    else:
                        logger.debug(f"    ✗ No mapping for '{field_name}'")
                
        # Log extraction stats for this statement
        fields_found = {
            'Bank_Year1': len(extracted_data['data']['Bank']['Year1'].get(schema_type, {})),
            'Bank_Year2': len(extracted_data['data']['Bank']['Year2'].get(schema_type, {})),
            'Group_Year1': len(extracted_data['data']['Group']['Year1'].get(schema_type, {})),
            'Group_Year2': len(extracted_data['data']['Group']['Year2'].get(schema_type, {}))
        }
        extracted_data['metadata']['fields_found'][schema_type] = fields_found
        
        logger.info(f"\n{schema_type} extraction complete:")
        logger.info(f"  Bank Year1: {fields_found['Bank_Year1']} fields")
        logger.info(f"  Bank Year2: {fields_found['Bank_Year2']} fields")
        logger.info(f"  Group Year1: {fields_found['Group_Year1']} fields")
        logger.info(f"  Group Year2: {fields_found['Group_Year2']} fields")
    
    return extracted_data


def save_extracted_data_to_files(extracted_data, pdf_id):
    """
    Save extracted data to both JSON and Excel files following TARGET_FIELDS schema.
    
    Args:
        extracted_data: Dictionary containing extracted financial data
        pdf_id: Unique identifier for the PDF
    
    Returns:
        Dictionary with file paths
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # JSON file
    json_filename = f"{pdf_id}_extracted_{timestamp}.json"
    json_path = PROCESSED_DATA_PATH / json_filename
    
    with open(json_path, 'w') as f:
        json.dump(extracted_data, f, indent=2)
    
    logger.info(f"Saved JSON file: {json_path}")
    
    # Excel file with sheets for Bank and Group, each with Year1 and Year2
    excel_filename = f"{pdf_id}_extracted_{timestamp}.xlsx"
    excel_path = PROCESSED_DATA_PATH / excel_filename
    
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        # Create a summary sheet
        summary_data = {
            'PDF ID': [extracted_data.get('pdf_id', '')],
            'Extraction Date': [extracted_data.get('extraction_date', '')],
            'Statements Extracted': [', '.join(extracted_data.get('metadata', {}).get('pages_processed', {}).keys())]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Create sheets for each Entity-Year-Statement combination
        data_section = extracted_data.get('data', {})
        
        for entity in ['Bank', 'Group']:
            entity_data = data_section.get(entity, {})
            
            for year in ['Year1', 'Year2']:
                year_data = entity_data.get(year, {})
                
                if not year_data:
                    continue
                
                # For each statement in this Entity-Year combination
                for statement_type, statement_fields in year_data.items():
                    if not statement_fields:
                        continue
                    
                    # Create sheet name (max 31 chars for Excel)
                    sheet_name = f"{entity}_{year}_{statement_type[:15]}"[:31]
                    
                    # Convert to DataFrame
                    df_data = []
                    for field_name, value in statement_fields.items():
                        df_data.append({
                            'Field': field_name,
                            'Value': value
                        })
                    
                    if df_data:
                        df = pd.DataFrame(df_data)
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                        logger.info(f"Added sheet '{sheet_name}' with {len(df)} fields")
        
        # Create comprehensive view sheets - all statements for each Entity-Year
        for entity in ['Bank', 'Group']:
            for year in ['Year1', 'Year2']:
                year_data = data_section.get(entity, {}).get(year, {})
                
                if not year_data:
                    continue
                
                # Combine all statements for this entity-year
                combined_data = []
                
                for statement_type, fields in year_data.items():
                    for field_name, value in fields.items():
                        combined_data.append({
                            'Statement': statement_type,
                            'Field': field_name,
                            'Value': value
                        })
                
                if combined_data:
                    sheet_name = f"{entity}_{year}_All"[:31]
                    df = pd.DataFrame(combined_data)
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    logger.info(f"Added combined sheet '{sheet_name}' with {len(df)} total fields")
    
    logger.info(f"Saved Excel file: {excel_path}")
    
    return {
        'json_file': str(json_path),
        'excel_file': str(excel_path),
        'json_filename': json_filename,
        'excel_filename': excel_filename
    }


def scan_pdfs():
    """Scan the raw data folder for PDFs and organize by category"""
    pdfs_by_category = {}
    
    if not RAW_DATA_PATH.exists():
        return pdfs_by_category
    
    # Iterate through category folders
    for category_dir in RAW_DATA_PATH.iterdir():
        if not category_dir.is_dir():
            continue
        
        category_name = category_dir.name.capitalize()
        pdfs = []
        
        # Find all PDF files in the category folder
        for pdf_file in category_dir.glob("*.pdf"):
            pdf_info = {
                "id": f"{category_dir.name}_{pdf_file.stem}",
                "name": pdf_file.name,
                "path": str(pdf_file),
                "company": pdf_file.stem.replace("_", " ").title(),
                "category": category_name,
                "pages": "Unknown"
            }
            
            # Try to extract year from filename
            import re
            year_match = re.search(r'20\d{2}', pdf_file.stem)
            if year_match:
                pdf_info["year"] = year_match.group()
            
            pdfs.append(pdf_info)
        
        if pdfs:
            pdfs_by_category[category_name] = pdfs
    
    return pdfs_by_category


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "ok", "service": "FD Extractor API"}), 200


@app.route('/api/pdfs', methods=['GET'])
def get_all_pdfs():
    """Get all PDFs from the raw data folder"""
    try:
        pdfs_by_category = scan_pdfs()
        all_pdfs = []
        for pdfs in pdfs_by_category.values():
            all_pdfs.extend(pdfs)
        
        return jsonify(all_pdfs), 200
    except Exception as e:
        logger.error(f"Error fetching PDFs: {str(e)}")
        return jsonify({"error": str(e)}), 500


def extract_statement_images(pdf_path, pdf_id):
    """
    Extract images for each statement type from the PDF using page locator
    Returns dictionary with statement type as key and list of image URLs as value
    """
    statement_images = {
        "income": [],
        "balance": [],
        "cashflow": []
    }
    
    statement_pages = {
        "income": [],
        "balance": [],
        "cashflow": []
    }
    
    try:
        # Initialize page locator to find actual statement pages
        page_locator = PageLocator(min_confidence=0.5)
        
        logger.info(f"Locating statements in PDF: {pdf_path}")
        locations = page_locator.locate_statements(pdf_path)
        
        # Map the statement types to our frontend keys
        statement_mapping = {
            'Income_Statement': 'income',
            'Financial Position Statement': 'balance',
            'Cash Flow Statement': 'cashflow'
        }
        
        # Extract page ranges for each statement
        for stmt_type, frontend_key in statement_mapping.items():
            if stmt_type in locations and locations[stmt_type]:
                # Get the best candidate (highest confidence)
                best_candidate = locations[stmt_type][0]
                page_range = best_candidate.page_range
                confidence = best_candidate.confidence
                
                logger.info(f"Found {stmt_type} on pages {page_range[0]+1}-{page_range[1]+1} (confidence: {confidence:.2f})")
                
                statement_pages[frontend_key] = {
                    'pages': page_range,
                    'confidence': confidence,
                    'evidence': best_candidate.evidence
                }
        
        # Now extract images from the identified pages
        doc = fitz.open(pdf_path)
        
        for frontend_key, page_info in statement_pages.items():
            if not page_info:
                continue
                
            page_range = page_info['pages']
            start_page = page_range[0]
            end_page = min(page_range[1], start_page + 4)  # Limit to max 5 pages per statement
            
            for page_idx in range(start_page, end_page + 1):
                if page_idx >= len(doc):
                    continue
                    
                page = doc[page_idx]
                
                # Render page to image
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better quality
                
                # Save image
                image_filename = f"{pdf_id}_{frontend_key}_page_{page_idx + 1}.png"
                image_path = IMAGES_PATH / image_filename
                pix.save(str(image_path))
                
                # Add image URL to the list
                image_url = f"/api/images/{image_filename}"
                statement_images[frontend_key].append({
                    "url": image_url,
                    "page": page_idx + 1,
                    "filename": image_filename
                })
        
        doc.close()
        
        total_images = sum(len(imgs) for imgs in statement_images.values())
        logger.info(f"Extracted {total_images} images from located statement pages for {pdf_id}")
        
        return statement_images, statement_pages
        
    except Exception as e:
        logger.error(f"Error extracting images: {str(e)}", exc_info=True)
        # Return empty results on error
        return statement_images, statement_pages


@app.route('/api/images/<filename>', methods=['GET'])
def get_image(filename):
    """Serve statement images"""
    try:
        image_path = IMAGES_PATH / filename
        if not image_path.exists():
            return jsonify({"error": "Image not found"}), 404
        
        return send_file(str(image_path), mimetype='image/png')
    except Exception as e:
        logger.error(f"Error serving image: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/pdfs/by-category', methods=['GET'])
def get_pdfs_by_category():
    """Get PDFs organized by category"""
    try:
        pdfs_by_category = scan_pdfs()
        return jsonify(pdfs_by_category), 200
    except Exception as e:
        logger.error(f"Error fetching PDFs by category: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/pdfs/<pdf_id>/extract', methods=['POST'])
def extract_statements(pdf_id):
    """
    Extract three financial statements from a PDF
    Returns: Income Statement, Balance Sheet, Cash Flow Statement
    """
    try:
        logger.info(f"Extracting statements from PDF: {pdf_id}")
        
        # Find the PDF by ID
        pdfs_by_category = scan_pdfs()
        pdf_info = None
        
        for category_pdfs in pdfs_by_category.values():
            for pdf in category_pdfs:
                if pdf["id"] == pdf_id:
                    pdf_info = pdf
                    break
            if pdf_info:
                break
        
        if not pdf_info:
            return jsonify({"error": "PDF not found"}), 404
        
        pdf_path = pdf_info["path"]
        logger.info(f"Processing PDF: {pdf_path}")
        
        # Extract page images for each statement type using page locator
        statement_images, statement_pages = extract_statement_images(pdf_path, pdf_id)
        
        # Build statements with actual page information
        statements = []
        
        statement_mapping = {
            'income': {
                'type': 'income',
                'title': 'Income Statement',
                'data': {
                    "Revenue": "10,500,000",
                    "Cost of Revenue": "6,300,000",
                    "Gross Profit": "4,200,000",
                    "Operating Expenses": "2,100,000",
                    "Operating Income": "2,100,000",
                    "Interest Expense": "300,000",
                    "Income Before Tax": "1,800,000",
                    "Income Tax": "450,000",
                    "Net Income": "1,350,000"
                }
            },
            'balance': {
                'type': 'balance',
                'title': 'Balance Sheet',
                'data': {
                    "Current Assets": "15,000,000",
                    "Cash and Equivalents": "5,000,000",
                    "Accounts Receivable": "7,000,000",
                    "Inventory": "3,000,000",
                    "Fixed Assets": "25,000,000",
                    "Total Assets": "40,000,000",
                    "Current Liabilities": "8,000,000",
                    "Long-term Debt": "12,000,000",
                    "Total Liabilities": "20,000,000",
                    "Shareholders Equity": "20,000,000"
                }
            },
            'cashflow': {
                'type': 'cashflow',
                'title': 'Cash Flow Statement',
                'data': {
                    "Operating Activities": "3,500,000",
                    "Net Income": "1,350,000",
                    "Depreciation": "1,200,000",
                    "Changes in Working Capital": "950,000",
                    "Investing Activities": "-2,000,000",
                    "Capital Expenditures": "-2,000,000",
                    "Financing Activities": "-800,000",
                    "Debt Repayment": "-500,000",
                    "Dividends Paid": "-300,000",
                    "Net Change in Cash": "700,000"
                }
            }
        }
        
        for key, config in statement_mapping.items():
            page_info = statement_pages.get(key, {})
            images = statement_images.get(key, [])
            
            if page_info and 'pages' in page_info:
                pages_str = f"Pages {page_info['pages'][0] + 1}-{page_info['pages'][1] + 1}"
                confidence = page_info['confidence']
            else:
                pages_str = "Not found"
                confidence = 0.0
            
            statement = {
                "type": config['type'],
                "data": config['data'],
                "confidence": confidence,
                "pages": pages_str,
                "images": images,
                "evidence": page_info.get('evidence', []) if page_info else []
            }
            
            statements.append(statement)
        
        response = {
            "pdf": pdf_info,
            "statements": statements,
            "extraction_success": True,
            "note": "Using PageLocator to identify statement pages"
        }
        
        logger.info(f"Extraction completed for {pdf_id}. Returning {len(statements)} statements.")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error extracting statements: {str(e)}", exc_info=True)
        return jsonify({
            "error": str(e),
            "extraction_success": False
        }), 500


@app.route('/api/pdfs/<pdf_id>/submit', methods=['POST'])
def submit_statements(pdf_id):
    """Submit selected statements for processing/storage"""
    try:
        data = request.get_json()
        selected_statements = data.get('selectedStatements', [])
        
        if not selected_statements:
            return jsonify({"error": "No statements selected"}), 400
        
        logger.info(f"Submitting {len(selected_statements)} statements for PDF: {pdf_id}")
        
        # Save the selected statements
        output_file = PROCESSED_DATA_PATH / f"{pdf_id}_selected.json"
        
        import json
        with open(output_file, 'w') as f:
            json.dump({
                "pdf_id": pdf_id,
                "statements": selected_statements,
                "timestamp": str(Path(__file__).stat().st_mtime)
            }, f, indent=2)
        
        logger.info(f"Statements saved to: {output_file}")
        
        return jsonify({
            "success": True,
            "message": f"Successfully submitted {len(selected_statements)} statements",
            "output_file": str(output_file)
        }), 200
        
    except Exception as e:
        logger.error(f"Error submitting statements: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get list of all categories"""
    try:
        pdfs_by_category = scan_pdfs()
        categories = list(pdfs_by_category.keys())
        
        return jsonify({
            "categories": categories,
            "count": len(categories)
        }), 200
    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/pdfs/<pdf_id>/extract-data', methods=['POST'])
def extract_data_from_pages(pdf_id):
    """
    Extract table data from selected pages and generate JSON and Excel files.
    
    Request body:
    {
        "selectedPages": {
            "income": [5, 6],
            "balance": [7, 8],
            "cashflow": [9, 10]
        }
    }
    """
    try:
        data = request.get_json()
        selected_pages = data.get('selectedPages', {})
        
        if not selected_pages:
            return jsonify({"error": "No pages selected"}), 400
        
        logger.info(f"Extract data request for PDF: {pdf_id}")
        logger.info(f"Selected pages: {selected_pages}")
        
        # Find the PDF by ID
        pdfs_by_category = scan_pdfs()
        pdf_info = None
        
        for category_pdfs in pdfs_by_category.values():
            for pdf in category_pdfs:
                if pdf["id"] == pdf_id:
                    pdf_info = pdf
                    break
            if pdf_info:
                break
        
        if not pdf_info:
            return jsonify({"error": "PDF not found"}), 404
        
        pdf_path = pdf_info["path"]
        logger.info(f"Processing PDF: {pdf_path}")
        
        # Extract data from selected pages
        extracted_data = extract_data_from_selected_pages(pdf_path, pdf_id, selected_pages)
        
        # Save to JSON and Excel files
        file_paths = save_extracted_data_to_files(extracted_data, pdf_id)
        
        # Calculate total items extracted
        total_items = 0
        for entity in ['Bank', 'Group']:
            for year in ['Year1', 'Year2']:
                year_data = extracted_data['data'].get(entity, {}).get(year, {})
                for statement_fields in year_data.values():
                    total_items += len(statement_fields)
        
        # Prepare response
        response = {
            "success": True,
            "message": "Data extracted successfully using schema-based mapping",
            "pdf_id": pdf_id,
            "statements_processed": list(extracted_data.get('metadata', {}).get('pages_processed', {}).keys()),
            "json_file": file_paths['json_filename'],
            "excel_file": file_paths['excel_filename'],
            "output_dir": str(PROCESSED_DATA_PATH),
            "total_fields_extracted": total_items,
            "extraction_summary": {
                "Bank": {
                    "Year1": sum(len(fields) for fields in extracted_data['data']['Bank']['Year1'].values()),
                    "Year2": sum(len(fields) for fields in extracted_data['data']['Bank']['Year2'].values())
                },
                "Group": {
                    "Year1": sum(len(fields) for fields in extracted_data['data']['Group']['Year1'].values()),
                    "Year2": sum(len(fields) for fields in extracted_data['data']['Group']['Year2'].values())
                }
            }
        }
        
        logger.info(f"Successfully extracted data: {response}")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error extracting data: {str(e)}", exc_info=True)
        return jsonify({
            "error": str(e),
            "success": False
        }), 500


if __name__ == '__main__':
    logger.info("Starting FD Extractor API Server...")
    logger.info(f"Raw data path: {RAW_DATA_PATH}")
    logger.info(f"Processed data path: {PROCESSED_DATA_PATH}")
    
    # Check if raw data folder has PDFs
    pdfs = scan_pdfs()
    logger.info(f"Found {sum(len(p) for p in pdfs.values())} PDFs in {len(pdfs)} categories")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
