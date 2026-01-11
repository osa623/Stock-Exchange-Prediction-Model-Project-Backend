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
import re
from typing import Optional, Dict, List
import pdfplumber
from src.extractor.shareholder_extractor import ShareholderExtractor
from src.locator.toc_detector import TOCDetector

# Configure logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check for Tesseract
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
    logger.info("Tesseract OCR is available")
except ImportError:
    TESSERACT_AVAILABLE = False
    logger.warning("pytesseract not available, using basic text extraction only")

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

# Configuration
RAW_DATA_PATH = Path(__file__).parent / "data" / "raw"
PROCESSED_DATA_PATH = Path(__file__).parent / "data" / "processed" / "extracted_json"
IMAGES_PATH = Path(__file__).parent / "app" / "statement_images"

# Ensure paths exist
RAW_DATA_PATH.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_PATH.mkdir(parents=True, exist_ok=True)
IMAGES_PATH.mkdir(parents=True, exist_ok=True)

# Initialize Shareholder Extractor and TOC Detector
shareholder_extractor = ShareholderExtractor()
toc_detector = TOCDetector()


def extract_data_from_selected_pages(pdf_path, pdf_id, selected_pages):
    """
    Extract text from selected pages using OCR and text extraction.
    
    Args:
        pdf_path: Path to the PDF file
        pdf_id: Unique identifier for the PDF
        selected_pages: Dict with statement types as keys and list of page numbers as values
                       Example: {'income': [5, 6], 'balance': [7], 'cashflow': [9]}
    
    Returns:
        Dictionary with extracted text data organized by statement and page
    """
    logger.info(f"Extracting data from selected pages using OCR: {selected_pages}")
    
    # Map frontend statement types to readable names
    statement_names = {
        'income': 'Income Statement',
        'balance': 'Balance Sheet',
        'cashflow': 'Cash Flow Statement'
    }
    
    # Initialize result structure
    extracted_data = {
        "pdf_id": pdf_id,
        "extraction_date": datetime.now().isoformat(),
        "statements": {}
    }
    
    try:
        doc = fitz.open(pdf_path)
        
        # Process each statement type
        for statement_type, pages in selected_pages.items():
            if not pages:
                continue
            
            statement_name = statement_names.get(statement_type, statement_type)
            logger.info(f"\n{'='*80}")
            logger.info(f"Processing {statement_name} from pages: {pages}")
            logger.info(f"{'='*80}\n")
            
            # Initialize statement data
            extracted_data['statements'][statement_type] = {}
            
            # Process each page
            for page_num in pages:
                page_idx = page_num - 1
                
                if page_idx >= len(doc) or page_idx < 0:
                    logger.warning(f"Page {page_num} is out of range, skipping")
                    continue
                
                logger.info(f"\nExtracting from page {page_num}")
                
                page = doc[page_idx]
                page_key = f'page_{page_num}'
                
                # Extract text using PyMuPDF (built-in text extraction)
                text_content = page.get_text("text")
                
                # Also try to get structured text (blocks)
                blocks = page.get_text("dict")["blocks"]
                
                # Extract text with better structure
                extracted_lines = []
                
                for block in blocks:
                    if block.get("type") == 0:  # Text block
                        for line in block.get("lines", []):
                            line_text = ""
                            for span in line.get("spans", []):
                                line_text += span.get("text", "")
                            
                            if line_text.strip():
                                extracted_lines.append(line_text.strip())
                
                # If no structured text, use OCR on the page image
                if not extracted_lines or len(extracted_lines) < 5:
                    logger.info(f"  Limited text found, attempting OCR...")
                    
                    try:
                        # Render page to image
                        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        
                        # Use OCR if available
                        if TESSERACT_AVAILABLE:
                            ocr_text = pytesseract.image_to_string(img)
                            extracted_lines = [line.strip() for line in ocr_text.split('\n') if line.strip()]
                            logger.info(f"  OCR extracted {len(extracted_lines)} lines")
                        else:
                            logger.warning("  pytesseract not available, using basic text extraction only")
                    
                    except Exception as e:
                        logger.error(f"  OCR failed: {str(e)}")
                
                # Parse lines into key-value pairs with year-based structure
                parsed_data = {}
                
                # Try to detect the year from the document
                current_year = None
                for line in extracted_lines[:20]:  # Check first 20 lines for year
                    year_match = re.search(r'(20\d{2})', line)
                    if year_match:
                        current_year = int(year_match.group(1))
                        break
                
                # Default to current year if not found
                if not current_year:
                    current_year = datetime.now().year
                
                previous_year = current_year - 1
                logger.info(f"  Detected years: {current_year}, {previous_year}")
                
                # Helper function to check if a line is likely a numeric value
                def is_numeric_value(text):
                    # Remove common separators and check if it's a number
                    cleaned = text.replace(',', '').replace('(', '').replace(')', '').replace('-', '').replace('.', '').strip()
                    return cleaned.isdigit() or (cleaned and all(c.isdigit() or c in '.,()-' for c in text))
                
                i = 0
                while i < len(extracted_lines):
                    line = extracted_lines[i].strip()
                    
                    # Skip very short lines
                    if len(line) < 3:
                        i += 1
                        continue
                    
                    # Skip standalone page numbers
                    if re.match(r'^\d+$', line) and len(line) < 4:
                        i += 1
                        continue
                    
                    # Check if line has multiple whitespace-separated parts (data on same line)
                    parts = re.split(r'\s{2,}|\t+', line)
                    
                    if len(parts) >= 2 and is_numeric_value(parts[1]):
                        # Data is on the same line: "Label    Value1    Value2"
                        key = parts[0].strip()
                        parsed_data[key] = {
                            str(current_year): parts[1].strip()
                        }
                        
                        # Store additional values if present (previous year)
                        if len(parts) > 2 and is_numeric_value(parts[2]):
                            parsed_data[key][str(previous_year)] = parts[2].strip()
                        
                        i += 1
                        
                    elif not is_numeric_value(line) and i + 1 < len(extracted_lines):
                        # Current line is a label, look ahead for values
                        key = line
                        
                        # Look at next lines to find numeric values
                        j = i + 1
                        values_found = []
                        
                        # Skip note numbers (single or double digit numbers)
                        while j < len(extracted_lines):
                            next_line = extracted_lines[j].strip()
                            
                            # Skip note numbers (typically 1-2 digits)
                            if re.match(r'^\d{1,2}$', next_line):
                                j += 1
                                continue
                            
                            # If it's a numeric value, collect it
                            if is_numeric_value(next_line) and len(next_line) > 2:
                                values_found.append(next_line)
                                j += 1
                                # Collect up to 2 values (current year, previous year)
                                if len(values_found) >= 2:
                                    break
                            else:
                                # Not a numeric value, stop looking
                                break
                        
                        # Store the key-value pair with year structure
                        if values_found:
                            parsed_data[key] = {
                                str(current_year): values_found[0]
                            }
                            # Store second value if present (usually previous year)
                            if len(values_found) > 1:
                                parsed_data[key][str(previous_year)] = values_found[1]
                        else:
                            # No values found, store empty
                            parsed_data[key] = {}
                        
                        i = j
                    else:
                        i += 1
                
                logger.info(f"  Extracted {len(parsed_data)} data items from page {page_num}")
                
                # Store the extracted data
                extracted_data['statements'][statement_type][page_key] = {
                    "raw_text_lines": len(extracted_lines),
                    "parsed_items": len(parsed_data),
                    "data": parsed_data,
                    "full_text": "\n".join(extracted_lines) if len(extracted_lines) < 500 else "\n".join(extracted_lines[:500]) + "\n... (truncated)"
                }
        
        doc.close()
        
    except Exception as e:
        logger.error(f"Error during extraction: {str(e)}", exc_info=True)
        raise
    
    logger.info(f"\n{'='*80}")
    logger.info("Extraction complete!")
    logger.info(f"{'='*80}\n")
    
    return extracted_data


def save_extracted_data_to_files(extracted_data, pdf_id):
    """
    Save extracted data to both JSON and Excel files.
    
    Args:
        extracted_data: Dictionary containing extracted text data
        pdf_id: Unique identifier for the PDF
    
    Returns:
        Dictionary with file paths
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # JSON file
    json_filename = f"{pdf_id}_ocr_{timestamp}.json"
    json_path = PROCESSED_DATA_PATH / json_filename
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(extracted_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved JSON file: {json_path}")
    
    # Excel file
    excel_filename = f"{pdf_id}_ocr_{timestamp}.xlsx"
    excel_path = PROCESSED_DATA_PATH / excel_filename
    
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        # Create summary sheet
        summary_data = {
            'PDF ID': [extracted_data.get('pdf_id', '')],
            'Extraction Date': [extracted_data.get('extraction_date', '')],
            'Statements Extracted': [', '.join(extracted_data.get('statements', {}).keys())]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Create sheets for each statement and page
        statements = extracted_data.get('statements', {})
        
        for statement_type, pages_data in statements.items():
            for page_key, page_info in pages_data.items():
                data_dict = page_info.get('data', {})
                
                if not data_dict:
                    continue
                
                # Convert nested dictionary to DataFrame with columns: Key, Year, Value
                rows = []
                for key, year_values in data_dict.items():
                    if isinstance(year_values, dict):
                        for year, value in year_values.items():
                            rows.append({"Key": key, "Year": year, "Value": value})
                    else:
                        # Handle edge case if not nested
                        rows.append({"Key": key, "Year": "", "Value": year_values})
                
                df = pd.DataFrame(rows)
                
                # Create sheet name
                sheet_name = f"{statement_type}_{page_key}"[:31]
                
                # Write to sheet
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                logger.info(f"Added sheet '{sheet_name}' with {len(df)} rows")
    
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
                
                # Add image URL to the list (use full URL for frontend)
                image_url = f"http://localhost:5000/api/images/{image_filename}"
                statement_images[frontend_key].append({
                    "url": image_url,
                    "page": page_idx + 1,
                    "filename": image_filename
                })
                
                logger.info(f"  Saved image: {image_filename} for page {page_idx + 1}")
        
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
        
        # Build statements with actual page information and images
        statements = []
        
        statement_configs = {
            'income': {
                'type': 'income',
                'title': 'Income Statement'
            },
            'balance': {
                'type': 'balance',
                'title': 'Balance Sheet'
            },
            'cashflow': {
                'type': 'cashflow',
                'title': 'Cash Flow Statement'
            }
        }
        
        # Build response for each statement type
        for key, config in statement_configs.items():
            page_info = statement_pages.get(key, {})
            images = statement_images.get(key, [])
            
            if page_info and 'pages' in page_info:
                pages_str = f"Pages {page_info['pages'][0] + 1}-{page_info['pages'][1] + 1}"
                confidence = page_info['confidence']
            else:
                pages_str = "Not found"
                confidence = 0.0
            
            # Only include statements that were actually found
            if images:
                statement = {
                    "type": config['type'],
                    "title": config['title'],
                    "data": {},  # Will be populated after user selects pages
                    "confidence": confidence,
                    "pages": pages_str,
                    "images": images,
                    "evidence": page_info.get('evidence', []) if page_info else []
                }
                statements.append(statement)
            else:
                logger.warning(f"No images found for {key} statement")
        
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
        
        # Count total items extracted
        total_items = 0
        total_pages = 0
        statements_count = extracted_data.get('statements', {})
        
        for stmt_type, pages_data in statements_count.items():
            for page_key, page_info in pages_data.items():
                total_pages += 1
                data_items = page_info.get('data', [])
                total_items += len(data_items)
        
        # Prepare response
        response = {
            "success": True,
            "message": "Text extracted successfully using OCR",
            "pdf_id": pdf_id,
            "statements_processed": list(extracted_data.get('statements', {}).keys()),
            "json_file": file_paths['json_filename'],
            "excel_file": file_paths['excel_filename'],
            "output_dir": str(PROCESSED_DATA_PATH),
            "extraction_summary": {
                "total_pages": total_pages,
                "total_items": total_items,
                "statements": list(extracted_data.get('statements', {}).keys())
            }
        }
        
        logger.info(f"Successfully extracted: {total_pages} pages, {total_items} items")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error extracting data: {str(e)}", exc_info=True)
        return jsonify({
            "error": str(e),
            "success": False
        }), 500
        
    except Exception as e:
        logger.error(f"Error extracting data: {str(e)}", exc_info=True)
        return jsonify({
            "error": str(e),
            "success": False
        }), 500


# ============================================================================
# INVESTOR RELATIONS ENDPOINTS
# ============================================================================

@app.route('/api/pdfs/<pdf_id>/investor-relations/detect', methods=['POST'])
def detect_investor_relations(pdf_id):
    """
    Detect Investor Relations page from TOC.
    """
    try:
        # Find PDF
        pdfs_by_category = scan_pdfs()
        pdf_data = None
        for category_pdfs in pdfs_by_category.values():
            for pdf in category_pdfs:
                if pdf['id'] == pdf_id:
                    pdf_data = pdf
                    break
            if pdf_data:
                break
        
        if not pdf_data:
            return jsonify({'error': 'PDF not found'}), 404
        
        pdf_path = pdf_data['path']
        logger.info(f"Detecting investor relations for PDF: {pdf_path}")
        
        # Detect investor relations pages
        with pdfplumber.open(pdf_path) as pdf:
            logger.info(f"PDF has {len(pdf.pages)} pages")
            pages = toc_detector.get_investor_relations_page_from_toc(pdf)
            logger.info(f"Detected pages: {pages}")
        
        if not pages:
            logger.warning(f"No investor relations pages detected for {pdf_id}")
        
        response_data = {
            'pdf_id': pdf_id,
            'pdf_name': pdf_data['name'],
            'pages': pages,
            'page_count': len(pages) if pages else 0,
            'method': 'toc_detection',
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Returning response: {response_data}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Investor relations detection error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/pdfs/<pdf_id>/investor-relations/images', methods=['POST'])
def get_investor_relations_images(pdf_id):
    """
    Get full page images from all detected shareholder pages.
    """
    try:
        data = request.get_json() or {}
        pages = data.get('pages')  # Array of page numbers
        
        if not pages:
            return jsonify({'error': 'pages array required'}), 400
        
        # Find PDF
        pdfs_by_category = scan_pdfs()
        pdf_data = None
        for category_pdfs in pdfs_by_category.values():
            for pdf in category_pdfs:
                if pdf['id'] == pdf_id:
                    pdf_data = pdf
                    break
            if pdf_data:
                break
        
        if not pdf_data:
            return jsonify({'error': 'PDF not found'}), 404
        
        pdf_path = pdf_data['path']
        
        # Extract full page image for each detected page
        all_images = []
        for page_num in pages:
            logger.info(f"Extracting full page image from page {page_num}")
            page_images = shareholder_extractor.extract_page_images(pdf_path, page_num)
            all_images.extend(page_images)
        
        response_data = {
            'pdf_id': pdf_id,
            'pages': pages,
            'images': all_images,
            'image_count': len(all_images),
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Image extraction error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/pdfs/<pdf_id>/investor-relations/extract', methods=['POST'])
def extract_investor_relations_table(pdf_id):
    """
    Extract investor relations information from selected image using OCR.
    """
    try:
        data = request.get_json() or {}
        page_num = data.get('page_num')
        bbox = data.get('bbox')
        
        if page_num is None:
            return jsonify({'error': 'page_num required'}), 400
        
        # Find PDF
        pdfs_by_category = scan_pdfs()
        pdf_data = None
        for category_pdfs in pdfs_by_category.values():
            for pdf in category_pdfs:
                if pdf['id'] == pdf_id:
                    pdf_data = pdf
                    break
            if pdf_data:
                break
        
        if not pdf_data:
            return jsonify({'error': 'PDF not found'}), 404
        
        pdf_path = pdf_data['path']
        
        # Extract table data
        logger.info(f"Extracting investor relations data from page {page_num}")
        extracted_data = shareholder_extractor.extract_table_from_page(
            pdf_path, 
            page_num, 
            bbox=bbox
        )
        
        # Save to JSON
        output_dir = PROCESSED_DATA_PATH.parent / 'investor_relations'
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_dir / f"{pdf_id}_investor_relations_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(extracted_data, f, indent=2)
        
        logger.info(f"Saved investor relations data to {output_file}")
        
        response_data = {
            'pdf_id': pdf_id,
            'page_num': page_num,
            'data': extracted_data,
            'saved_to': str(output_file),
            'success': True,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Extraction error: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


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
