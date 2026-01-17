"""
Table Parser
Parses text lines into structured data using ColumnInterpreter and Stream Extraction Strategy.
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
            return {}

        # 1. Detect Schema from Header if not provided
        if not schema:
            schema = self.detect_schema(clean_lines[:50])
            
        if not schema:
            logger.warning("Could not detect schema from headers and none provided.")
            # Fallback? return empty for now
            return {}

        logger.info(f"Using schema: {[c.name for c in schema]}")

        # 2. Extract Data
        data = self._extract_data_stream(clean_lines, schema)
        
        return data, schema

    def detect_schema(self, lines: List[str]) -> List[ColumnDef]:
        """Detect column schema from header lines."""
        years = []
        has_note = False
        has_page = False
        entities = []

        # Keywords
        for line in lines:
            text = line.lower()
            
            # Stop if we hit what looks like a data row (e.g. "Gross income")
            # Heuristic: simple text line, no numbers, not a header keyword
            # But "Gross income" might be confused with header. 
            # Let's just scan all header tokens.
            
            # Skip Title lines/Report meta-data to avoid grabbing years from "Annual Report 2024"
            if "report" in text or "dated" in text:
                continue

            # Detect Years
            found_years = re.findall(r'20\d{2}', text)
            for y in found_years:
                if len(years) < 4: # Limit to expected max 4 years usually
                    years.append(int(y))
            
            # Detect Note/Page
            if re.search(r'\bnote\b', text):
                has_note = True
            if re.search(r'\bpage\b', text) or re.search(r'\bno\.\b', text): # 'no.' often accompanies Page
                has_page = True
                
            # Detect Entities
            if "bank" in text:
                entities.append("Bank")
            if "group" in text:
                entities.append("Group")

        # Deduplicate Entities (preserve order)
        seen = set()
        unique_entities = [x for x in entities if not (x in seen or seen.add(x))]
        
        # Construct Schema
        schema = []
        
        if has_note:
            schema.append(ColumnDef(ColumnType.NOTE, "Note"))
        if has_page:
            schema.append(ColumnDef(ColumnType.PAGE, "Page"))
            
        # Map Years to Entities
        # Case 1: 4 years, 2 entities (Bank, Group)
        # Expected: Bank Y1, Bank Y2, Group Y1, Group Y2 (or similar)
        # We need to map the ORDER of values to the columns.
        # From the example: Bank ... Group ... 2024 ... 2023 ... 2024 ... 2023
        # This implies: Column 1 = Bank 2024, Col 2 = Bank 2023, Col 3 = Group 2024, Col 4 = Group 2023.
        
        # If we found 4 years:
        if len(years) >= 4:
            # Assume 2 entities with 2 years each
            # Default entities if not found
            if len(unique_entities) < 2:
                unique_entities = ["Entity1", "Entity2"]
            
            # Sort years descending (recent first) usually
            # But the order in `years` list reflects extraction order.
            # In the example: 2024, 2023, 2024, 2023.
            
            # Assign
            schema.append(ColumnDef(ColumnType.VALUE, f"{years[0]} ({unique_entities[0]})", years[0], unique_entities[0]))
            schema.append(ColumnDef(ColumnType.VALUE, f"{years[1]} ({unique_entities[0]})", years[1], unique_entities[0]))
            schema.append(ColumnDef(ColumnType.VALUE, f"{years[2]} ({unique_entities[1]})", years[2], unique_entities[1]))
            schema.append(ColumnDef(ColumnType.VALUE, f"{years[3]} ({unique_entities[1]})", years[3], unique_entities[1]))
            
        elif len(years) >= 2:
            # Assume 1 entity or merged
            schema.append(ColumnDef(ColumnType.VALUE, str(years[0]), years[0], "Bank"))
            schema.append(ColumnDef(ColumnType.VALUE, str(years[1]), years[1], "Bank"))
        else:
            # Minimal fallback
            schema.append(ColumnDef(ColumnType.VALUE, "Current Year"))
            schema.append(ColumnDef(ColumnType.VALUE, "Previous Year"))
            
        return schema

    def _extract_data_stream(self, lines: List[str], schema: List[ColumnDef]) -> Dict[str, Any]:
        """Extract data by matching stream of tokens to schema."""
        data = {}
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Identify Key
            # Must be text, longer than 3 chars, not a number, not a reserved keyword
            if self._is_valid_key(line):
                key = line
                row_data = {}
                
                # Look ahead for values
                j = i + 1
                collected_values = []
                
                # Greedily finding numeric tokens
                # We stop if we hit something that looks like a Key (text)
                # OR if we found enough values for all value columns
                
                max_values_needed = len([c for c in schema if c.col_type == ColumnType.VALUE])
                max_notes_needed = len([c for c in schema if c.col_type in [ColumnType.NOTE, ColumnType.PAGE]])
                
                while j < len(lines):
                    token = lines[j]
                    if self._is_valid_key(token):
                        # Next key found, stop collecting
                        break
                    
                    if self._is_numeric(token):
                        collected_values.append(token)
                    
                    j += 1
                    
                    # Safety break
                    if len(collected_values) >= max_values_needed + max_notes_needed:
                        break
                
                # Map collected values to schema
                if collected_values:
                    self._map_values_to_schema(row_data, schema, collected_values)
                    
                    if row_data:
                        data[key] = row_data
                
                # Advance main loop
                i = j
            else:
                # noise or header, skip
                i += 1
                
        return data

    def _map_values_to_schema(self, row_data: Dict, schema: List[ColumnDef], values: List[str]):
        """
        Smart mapping of values to schema.
        Distinguish Note/Page (small ints) from Money (large numbers, commas).
        """
        # Value columns (money)
        val_schema = [c for c in schema if c.col_type == ColumnType.VALUE]
        note_schema = [c for c in schema if c.col_type in [ColumnType.NOTE, ColumnType.PAGE]]
        
        # Heuristic: Large numbers (>1000 or contains comma) are definitely Values.
        # Small numbers (<1000, no comma) could be Note, Page, OR Value (if value is small).
        # But in financial statements, Values usually aligned.
        
        money_values = []
        other_values = []
        
        for v in values:
            if self._is_money_value(v):
                money_values.append(v)
            else:
                other_values.append(v)
        
        # If we have enough money values to fill the value slots, assign them left-to-right to the VALUE columns
        # Note/Page get whatever is left (if any), or skipped
        
        # Strict mapping:
        # If we have 4 value columns and 4 money_values, perfect match.
        # What if we have 5 values (1 note, 4 money)?
        # The list `values` preserves order.
        
        # Try to map sequentially but skip Note/Page if value looks like money
        val_idx = 0
        schema_idx = 0
        
        for val in values:
            if schema_idx >= len(schema):
                break
                
            col_def = schema[schema_idx]
            
            # If column is Note/Page
            if col_def.col_type in [ColumnType.NOTE, ColumnType.PAGE]:
                if not self._is_money_value(val):
                    # Looks like a note/page, assign it
                    # (We ignore note/page in output as per user request, or store it?)
                    # User said: "statement1 : { year1: value ... }"
                    # Implies we don't need Note/Page in output.
                    schema_idx += 1
                else:
                    # We expected Note/Page but got Money.
                    # Assume Note/Page was empty/missing. 
                    # Skip this column and try to match Money to next VALUE column.
                    schema_idx += 1
                    # Re-eval this value against next column
                    # But we need to stay on this value? 
                    # No, let's just retry logic.
                    # Actually, if we skip, we should check if *this* value matches *next* column.
                    if schema_idx < len(schema) and schema[schema_idx].col_type == ColumnType.VALUE:
                         row_data[schema[schema_idx].name] = val
                         schema_idx += 1
            
            # If column is Value
            elif col_def.col_type == ColumnType.VALUE:
                # Assign key
                row_data[col_def.name] = val
                schema_idx += 1
                
        # If we missed some value columns due to strict mapping, that's life.
        # This logic is decent.

    def _is_valid_key(self, line: str) -> bool:
        """Check if line is a valid Row Key (Description)."""
        if self._is_numeric(line): return False
        if len(line) < 3: return False
        # Avoid headers
        lower = line.lower()
        if "bank" in lower or "group" in lower or "note" in lower or "page" in lower or "lkr" in lower:
            return False
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

