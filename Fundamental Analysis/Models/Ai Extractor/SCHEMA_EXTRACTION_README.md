# Schema-Based Financial Statement Extraction System

## Overview

This system extracts financial data from PDFs using a **predefined schema** that ensures consistency and completeness. Unlike simple table extraction, this approach:

1. ✅ Maps extracted labels to **canonical field names**
2. ✅ Organizes data by **Bank/Group** entities
3. ✅ Separates data by **Year1/Year2** periods
4. ✅ Follows the **TARGET_FIELDS** structure from `target_schema_bank.py`
5. ✅ Uses intelligent **fuzzy matching** and **synonym dictionaries**

## Architecture

### Core Components

#### 1. Target Schema (`config/target_schema_bank.py`)
Defines the canonical structure:
- **Income_Statement**: 40+ mandatory fields
- **Financial Position Statement**: 35+ mandatory fields
- **Cash Flow Statement**: 65+ mandatory fields

#### 2. Term Mapping (`config/term_mapping_bank.py`)
Maps variations to canonical names:
```python
"Net interest income": [
    "net interest income",
    "nii",
    "interest income net",
    "net interest revenue"
]
```

#### 3. Mapping Engine (`src/mapper/mapping_engine.py`)
Cascading strategy:
1. Exact match (normalized)
2. Synonym lookup
3. Fuzzy matching (>85% similarity)
4. Semantic matching (optional)

#### 4. Column Interpreter (`src/extractor/column_interpreter.py`)
Detects:
- Bank vs Group columns
- Year columns (2023, 2024, etc.)
- Description/label columns
- Note reference columns

#### 5. Numeric Normalizer (`src/extractor/numeric_normalizer.py`)
Handles:
- Currency symbols (Rs, $, etc.)
- Thousands separators (1,234,567)
- Negative values (parentheses)
- Million/thousand notation

## Data Flow

```
PDF Pages (selected by user)
    ↓
Table Extraction (pdfplumber)
    ↓
Column Interpretation (Bank/Group, Year1/Year2)
    ↓
Row Label Mapping (canonical field names)
    ↓
Value Normalization (clean numbers)
    ↓
Schema Organization (TARGET_FIELDS structure)
    ↓
Output (JSON + Excel)
```

## Output Structure

### JSON Format
```json
{
  "pdf_id": "abl_ABL",
  "extraction_date": "2026-01-06T...",
  "data": {
    "Bank": {
      "Year1": {
        "Income_Statement": {
          "Gross income": "150234567890",
          "Interest income": "125678901234",
          "Interest expenses": "45678901234",
          "Net interest income": "80000000000",
          "Fee and commission income": "15234567890",
          ...
        },
        "Financial Position Statement": {
          "Cash and cash equivalents": "52345678901",
          "Total assets": "2567890123456",
          "Total liabilities": "2000000000000",
          ...
        },
        "Cash Flow Statement": {
          "Cash flows from operating activities": "85234567890",
          "Interest receipts": "130000000000",
          ...
        }
      },
      "Year2": {
        "Income_Statement": { ... },
        "Financial Position Statement": { ... },
        "Cash Flow Statement": { ... }
      }
    },
    "Group": {
      "Year1": { ... },
      "Year2": { ... }
    }
  },
  "metadata": {
    "pages_processed": {
      "Income_Statement": [5, 6],
      "Financial Position Statement": [7, 8],
      "Cash Flow Statement": [9, 10]
    },
    "fields_found": {
      "Income_Statement": {
        "Bank_Year1": 38,
        "Bank_Year2": 38,
        "Group_Year1": 37,
        "Group_Year2": 36
      },
      "Financial Position Statement": {
        "Bank_Year1": 32,
        "Bank_Year2": 32,
        "Group_Year1": 31,
        "Group_Year2": 30
      },
      "Cash Flow Statement": {
        "Bank_Year1": 58,
        "Bank_Year2": 55,
        "Group_Year1": 57,
        "Group_Year2": 54
      }
    },
    "mapping_stats": {}
  }
}
```

### Excel Format

#### Sheets Created:

**Summary Sheet**
- PDF ID
- Extraction Date
- Statements Processed

**Entity-Year-Statement Sheets** (Individual)
- `Bank_Year1_Income_Statement`
- `Bank_Year2_Income_Statement`
- `Bank_Year1_Financial Position`
- `Bank_Year2_Financial Position`
- `Bank_Year1_Cash Flow Sta`
- `Bank_Year2_Cash Flow Sta`
- `Group_Year1_Income_Statement`
- `Group_Year2_Income_Statement`
- (etc.)

Each sheet contains:
| Field | Value |
|-------|-------|
| Gross income | 150234567890 |
| Interest income | 125678901234 |
| Net interest income | 80000000000 |

**Comprehensive Sheets** (All statements combined)
- `Bank_Year1_All`
- `Bank_Year2_All`
- `Group_Year1_All`
- `Group_Year2_All`

Each sheet contains:
| Statement | Field | Value |
|-----------|-------|-------|
| Income_Statement | Gross income | 150234567890 |
| Income_Statement | Interest income | 125678901234 |
| Financial Position Statement | Total assets | 2567890123456 |

## Mapping Examples

### Exact Match
```
Extracted: "Net interest income"
Canonical: "Net interest income"
Method: exact
Confidence: 100%
```

### Synonym Match
```
Extracted: "NII"
Canonical: "Net interest income"
Method: synonym
Confidence: 95%
```

### Fuzzy Match
```
Extracted: "Net Interest Revenue"
Canonical: "Net interest income"
Method: fuzzy
Confidence: 90%
Score: 88.5
```

## Usage

### 1. Start API Server
```bash
cd "Fundamental Analysis/Models/Ai Extractor"
python api_server.py
```

### 2. Start Frontend
```bash
cd "Fundamental Analysis/Models/fdextractor"
npm run dev
```

### 3. Extract Data
1. Navigate to PDF details page
2. Select pages for each statement type
3. Click "Extract Data"
4. Review extraction summary
5. Find output files in `data/processed/extracted_json/`

## Configuration

### Adjust Fuzzy Threshold
In `api_server.py`:
```python
mapping_engine = MappingEngine(fuzzy_threshold=85.0)  # Default: 85%
```

Lower = more matches (less precise)
Higher = fewer matches (more precise)

### Add Custom Synonyms
In `config/term_mapping_bank.py`:
```python
TERM_MAPPING = {
    "Your Canonical Field": [
        "variation 1",
        "variation 2",
        "abbreviation"
    ],
    ...
}
```

### Modify Schema
In `config/target_schema_bank.py`:
```python
STATEMENT_FIELDS = {
    "Income_Statement": [
        "New Field Name",
        "Another Field",
        ...
    ],
    ...
}
```

## Validation & Quality Assurance

### Check Extraction Quality

1. **Review JSON metadata**:
   - `fields_found`: Shows how many fields were extracted for each entity-year-statement
   - Compare with total fields in schema

2. **Check Excel files**:
   - Open comprehensive sheets (`Bank_Year1_All`)
   - Verify all expected statements are present
   - Check for missing or incorrect values

3. **Review Logs**:
   - API server logs show mapping details
   - Look for "✓ Mapped" messages
   - Check fuzzy match scores

### Common Issues

**Low Field Count**
- Solution: Select more pages, ensure table headers are included

**Incorrect Values**
- Solution: Check column interpretation, adjust header detection patterns

**Missing Fields**
- Solution: Add synonyms to `term_mapping_bank.py`, lower fuzzy threshold

**Wrong Entity Assignment**
- Solution: Improve column headers, add explicit "Bank" or "Group" labels

## Performance

- **Table Extraction**: ~1-2 seconds per page
- **Mapping**: ~0.1 seconds per row
- **File Generation**: ~1-2 seconds

**Typical Processing Time**:
- 3 statements × 3 pages each = 9 pages
- Total time: ~15-20 seconds

## Benefits of Schema-Based Extraction

✅ **Consistency**: Same field names across all PDFs  
✅ **Completeness**: Attempts to extract all predefined fields  
✅ **Accuracy**: Fuzzy matching handles variations  
✅ **Structure**: Organized by Bank/Group and Year  
✅ **Validation**: Easy to check against schema  
✅ **Integration**: Ready for downstream analysis  

## Next Steps

1. **Financial Analysis**: Use extracted data for ratio calculations
2. **Time Series Analysis**: Compare Year1 vs Year2
3. **Peer Comparison**: Compare Bank vs Group entities
4. **ML Models**: Feed structured data into prediction models
5. **Automated Reporting**: Generate standardized reports

## Support

For issues or questions:
1. Check server logs in terminal
2. Review `EXTRACTION_GUIDE.md`
3. Examine sample output files in `data/processed/extracted_json/`
4. Test with known good PDFs first
