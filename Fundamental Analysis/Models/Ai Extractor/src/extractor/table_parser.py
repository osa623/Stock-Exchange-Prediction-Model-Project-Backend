"""
Table Parser
Parses text lines into structured data using ColumnInterpreter and Stream Extraction Strategy.
Refactored to handle both vertical (multiline) and horizontal (inline) layouts by tokenizing first.
"""

import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ColumnType(Enum):
    NOTE = "note"
    PAGE = "page"
    VALUE = "value"

@dataclass
class ColumnDef:
    col_type: ColumnType
    name: str  # e.g., "Bank 2024", "Note", "Page"
    year: Optional[int] = None
    entity: Optional[str] = None

class TableParser:
    """Parses text lines into financial data structure."""

    def __init__(self):
        pass

    def parse_lines(self, lines: List[str], schema: Optional[List[ColumnDef]] = None) -> Dict[str, Any]:
        """
        Parse lines of text into structured data.
        
        Args:
            lines: Text lines
            schema: Optional pre-defined schema (useful for multi-page statements)
        """
        # Filter empty lines
        clean_lines = [line.strip() for line in lines if line.strip()]
        if not clean_lines:
            return {}, None

        # 1. Detect Schema from Header if not provided
        if not schema:
            schema = self.detect_schema(clean_lines[:50])
            
        if not schema:
            logger.warning("Could not detect schema from headers and none provided.")
            return {}, None

        logger.info(f"Using schema: {[c.name for c in schema]}")

        # 2. Tokenize Content
        # We split every line by 2+ spaces to handle horizontal layouts
        # e.g. "Gross Income    100    200" -> ["Gross Income", "100", "200"]
        # And we flatten this into a single stream of tokens.
        tokens = []
        for line in clean_lines:
            # Split by 2+ spaces or tabs
            parts = re.split(r'\s{2,}|\t+', line)
            for part in parts:
                p = part.strip()
                if p:
                    tokens.append(p)

        # 3. Extract Data from Token Stream
        data = self._extract_data_from_tokens(tokens, schema)
        
        return data, schema

    def detect_schema(self, lines: List[str]) -> List[ColumnDef]:
        """Detect column schema from header lines."""
        years = []
        has_note = False
        has_page = False
        entities = []

        for line in lines:
            text = line.lower()
            
            # Skip Title lines/Report meta-data to avoid grabbing years from "Annual Report 2024"
            if "report" in text or "dated" in text:
                continue

            # Detect Years
            found_years = re.findall(r'20\d{2}', text)
            for y in found_years:
                if len(years) < 4: # Limit to expected max 4 years usually
                    years.append(int(y))
            
            if re.search(r'\bnote\b', text): has_note = True
            if re.search(r'\bpage\b', text) or re.search(r'\bno\.\b', text): has_page = True
            
            if "bank" in text: entities.append("Bank")
            if "group" in text: entities.append("Group")

        # Deduplicate Entities (preserve order)
        seen = set()
        unique_entities = [x for x in entities if not (x in seen or seen.add(x))]
        
        # Construct Schema
        schema = []
        
        if has_note:
            schema.append(ColumnDef(ColumnType.NOTE, "Note"))
        if has_page:
            schema.append(ColumnDef(ColumnType.PAGE, "Page"))
            
        if len(years) >= 4:
            if len(unique_entities) < 2:
                unique_entities = ["Entity1", "Entity2"]
            
            # Map based on standard layout (Entity1 Y1, Entity1 Y2, Entity2 Y1, Entity2 Y2)
            # OR (Entity1, Entity2, Y1, Y2...)
            # We assume order detected in years list matches column order.
            
            schema.append(ColumnDef(ColumnType.VALUE, f"{years[0]} ({unique_entities[0]})", years[0], unique_entities[0]))
            schema.append(ColumnDef(ColumnType.VALUE, f"{years[1]} ({unique_entities[0]})", years[1], unique_entities[0]))
            schema.append(ColumnDef(ColumnType.VALUE, f"{years[2]} ({unique_entities[1]})", years[2], unique_entities[1]))
            schema.append(ColumnDef(ColumnType.VALUE, f"{years[3]} ({unique_entities[1]})", years[3], unique_entities[1]))
            
        elif len(years) >= 2:
            schema.append(ColumnDef(ColumnType.VALUE, str(years[0]), years[0], "Bank"))
            schema.append(ColumnDef(ColumnType.VALUE, str(years[1]), years[1], "Bank"))
        else:
            # Only used if barely anything found
            schema.append(ColumnDef(ColumnType.VALUE, "Current Year"))
            schema.append(ColumnDef(ColumnType.VALUE, "Previous Year"))
            
        return schema

    def _extract_data_from_tokens(self, tokens: List[str], schema: List[ColumnDef]) -> Dict[str, Any]:
        """Extract data by matching stream of tokens to schema."""
        data = {}
        
        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            # Identify Key
            # Must be text, longer than 3 chars
            if self._is_valid_key(token):
                key = token
                # Check if next token is ALSO a key part? (e.g. "Gross", "Income")
                # Heuristic: if next token is NOT valid key (is number/short) -> current key is complete.
                # If next token IS valid key -> join them?
                # Actually, PyMuPDF line splitting might verify this.
                # But we split by \s{2,}. So "Gross Income" (1 space) stays as one token.
                # "Gross Income" (2 spaces) becomes two tokens.
                # We should try to join adjacent text tokens into the Key.
                
                j = i + 1
                while j < len(tokens):
                    next_tok = tokens[j]
                    if self._is_valid_key(next_tok):
                        # Join with space
                        key += " " + next_tok
                        j += 1
                    else:
                        break
                
                # Now collect values
                row_data = {}
                collected_values = []
                
                # Look ahead for values starting from j
                max_values_needed = len([c for c in schema if c.col_type == ColumnType.VALUE])
                max_notes_needed = len([c for c in schema if c.col_type in [ColumnType.NOTE, ColumnType.PAGE]])
                
                k = j
                while k < len(tokens):
                    val_tok = tokens[k]
                    
                    # Stop if we hit a new Key (that isn't a value)
                    if self._is_valid_key(val_tok):
                         break
                    
                    if self._is_numeric(val_tok):
                        # Filter small integers (likely percentages or noise)
                        # User Rule: "Actually evertime these values equals 4 or more than 4 digits"
                        # We allow dashes, floats (dots), and long integers (>= 4 digits)
                        if self._is_valid_financial_value(val_tok):
                            collected_values.append(val_tok)
                        else:
                           # Skip "small" numbers like 34, 205, (25)
                           pass
                    
                    k += 1
                    
                    if len(collected_values) >= max_values_needed + max_notes_needed:
                        break
                
                # Map collected values
                if collected_values:
                    self._map_values_to_schema(row_data, schema, collected_values)
                    if row_data:
                        data[key] = row_data
                
                # Advance main loop to k
                i = k
            else:
                # Noise or header token
                i += 1
                
        return data

    def _map_values_to_schema(self, row_data: Dict, schema: List[ColumnDef], values: List[str]):
        """
        Smart mapping of values to schema.
        Since we pre-filtered small integers (Notes/Pages), we assume 'values' contains only financial data.
        So we skip NOTE/PAGE columns in the schema and fill the VALUE columns.
        """
        schema_idx = 0
        
        for val in values:
            # Skip NOTE/PAGE columns until we find a VALUE column
            while schema_idx < len(schema) and schema[schema_idx].col_type in [ColumnType.NOTE, ColumnType.PAGE]:
                schema_idx += 1
            
            if schema_idx >= len(schema):
                break
                
            col_def = schema[schema_idx]
            
            if col_def.col_type == ColumnType.VALUE:
                row_data[col_def.name] = val
                schema_idx += 1

    def _is_valid_financial_value(self, text: str) -> bool:
        """
        True if text looks like a valid financial value (>= 4 digits, or float, or dash).
        Rejects small integers (noise, percentages, note numbers).
        """
        # Allow dash
        clean = text.replace('–', '-').strip()
        if clean == '-' or clean == '—': return True
        
        # Allow floats (must contain dot)
        if '.' in text: return True
        
        # Allow commas (implies > 999 usually)
        if ',' in text: return True
        
        # Check digit count
        digits = re.sub(r'\D', '', text)
        if len(digits) >= 4: return True
        
        return False

    def _is_valid_key(self, token: str) -> bool:
        """Check if token is a valid Row Key (Description)."""
        if self._is_numeric(token): return False
        if len(token) < 2: return False # Allow 2 chars? "Re"
        
        # Avoid headers (Use strict checks)
        lower = token.lower()
        # Headers usually are standalone "Bank" or "Group" or "Note"
        if lower in ["bank", "group", "note", "page", "lkr", "no."]:
            return False
            
        # Also check for regex if punctuation is attached like "Note." or "(Bank)"
        if re.match(r'^\(?(bank|group|note|page|lkr|no\.?)\)?$', lower):
            return False
            
        # Avoid "2024"
        if re.match(r'20\d{2}', token): return False
        return True

    def _is_numeric(self, text: str) -> bool:
        cleaned = text.replace(',', '').replace('(', '').replace(')', '').replace('-', '').replace('.', '').strip()
        if not cleaned: return False # Empty
        if cleaned == '–' or text.strip() == '-': return True
        return cleaned.isdigit()

    def _is_money_value(self, text: str) -> bool:
        """True if looks like a financial value (large, commas)."""
        if ',' in text: return True
        cleaned = text.replace(',', '').replace('(', '').replace(')', '').replace('-', '').replace('.', '').strip()
        if cleaned.isdigit() and len(cleaned) > 3: return True # > 999
        return False
