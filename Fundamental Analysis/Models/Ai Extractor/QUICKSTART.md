# QUICK START GUIDE - Two-Stage Extraction Pipeline

## 🚀 What's Working Right Now

### ✅ Stage A: Page Location (100% Complete)
You can locate financial statement pages in any annual report PDF with confidence scoring.

### ✅ Core Components (80% Complete)
- Numeric normalization (brackets, dashes, decimals)
- Column interpretation (Bank/Group, Year1/Year2)
- Label mapping (exact, synonym, fuzzy)

### ⚠️ Stage B: Full Extraction (40% Complete)
Table extraction and row extraction need completion.

---

## 📦 Installation

```bash
# Already installed from requirements.txt
# Key dependencies:
# - pdfplumber, PyPDF2 (PDF processing)
# - rapidfuzz (fuzzy matching)
# - pandas, numpy (data processing)
# - pytest (testing)
```

---

## 🎯 Quick Examples

### Example 1: Locate Statement Pages

```python
from src.locator.page_locator import PageLocator

# Create locator
locator = PageLocator(min_confidence=0.5)

# Locate statements in a PDF
results = locator.locate_statements('path/to/annual_report.pdf')

# Print summary
locator.print_summary(results)

# Get best candidates
best = locator.get_best_candidates(results, top_n=1)

# Access specific statement
income_stmt_pages = best['Income_Statement'][0]
print(f"Income Statement on pages: {income_stmt_pages.page_range}")
print(f"Confidence: {income_stmt_pages.confidence:.2%}")
print(f"Evidence: {income_stmt_pages.evidence}")
```

**Output:**
```
================================================================================
STAGE A: PAGE LOCATION RESULTS
================================================================================

Income_Statement:
------------------------------------------------------------

  Candidate #1:
    📄 Pages: 25-27
    ✅ Confidence: 92%
    🔍 Sources: toc, heading_scan
    📋 Evidence:
       - ToC entry: 'Statement of Profit or Loss' (reported page 25)
       - Heading found: 'STATEMENT OF COMPREHENSIVE INCOME'
```

### Example 2: Normalize Numeric Values

```python
from src.extractor.numeric_normalizer import NumericNormalizer

normalizer = NumericNormalizer()

# Test various formats
test_values = [
    "1,234,567.89",      # Regular number with commas
    "(1,234.56)",        # Bracketed = negative
    "–",                 # Dash = null
    "Rs. 1,000,000",     # With currency symbol
    "nil"                # Null indicator
]

for value in test_values:
    result = normalizer.normalize(value)
    print(f"'{value}' → {result.normalized_value} "
          f"(negative: {result.is_negative}, null: {result.is_null})")
```

**Output:**
```
'1,234,567.89' → 1234567.89 (negative: False, null: False)
'(1,234.56)' → -1234.56 (negative: True, null: False)
'–' → None (negative: False, null: True)
'Rs. 1,000,000' → 1000000.0 (negative: False, null: False)
'nil' → None (negative: False, null: False)
```

### Example 3: Interpret Table Columns

```python
from src.extractor.column_interpreter import ColumnInterpreter

interpreter = ColumnInterpreter()

# Example header structure (multi-row)
headers = [
    ["", "Bank", "Bank", "Group", "Group"],
    ["Particulars", "2023", "2022", "2023", "2022"]
]

# Interpret columns
column_info = interpreter.interpret_columns(headers)

# Print results
for col_idx, info in column_info.items():
    print(f"Column {col_idx}: {info.column_type.value} "
          f"(entity: {info.entity}, year: {info.year}, "
          f"confidence: {info.confidence:.2%})")
```

**Output:**
```
Column 0: description (entity: None, year: None, confidence: 70%)
Column 1: bank_year1 (entity: Bank, year: 2023, confidence: 80%)
Column 2: bank_year2 (entity: Bank, year: 2022, confidence: 80%)
Column 3: group_year1 (entity: Group, year: 2023, confidence: 80%)
Column 4: group_year2 (entity: Group, year: 2022, confidence: 80%)
```

### Example 4: Map Row Labels

```python
from src.mapper.mapping_engine import MappingEngine

engine = MappingEngine(fuzzy_threshold=85.0)

# Test various label formats
test_labels = [
    "Gross income",           # Exact match
    "interest revenue",       # Synonym match
    "Net interest incom",     # Fuzzy match (typo)
    "Some Unknown Field"      # No match
]

for label in test_labels:
    result = engine.map_label(label, "Income_Statement")
    print(f"'{label}' → '{result.canonical_key}' "
          f"(method: {result.match_method}, "
          f"confidence: {result.confidence:.2%})")
```

**Output:**
```
'Gross income' → 'Gross income' (method: exact, confidence: 100%)
'interest revenue' → 'Interest income' (method: synonym, confidence: 95%)
'Net interest incom' → 'Net interest income' (method: fuzzy, confidence: 91%)
'Some Unknown Field' → 'None' (method: none, confidence: 0%)
```

### Example 5: Run Full Pipeline (Current State)

```python
from src.pipeline.two_stage_pipeline import TwoStagePipeline

# Create pipeline
pipeline = TwoStagePipeline(config={
    'min_page_confidence': 0.5,
    'fuzzy_threshold': 85.0,
    'validation_tolerance': 0.01
})

# Run extraction
result = pipeline.extract(
    'path/to/annual_report.pdf',
    save_intermediates=True
)

# Check status
print(f"Status: {result['overall_status']}")
print(f"Stage A complete: {bool(result['stage_a_results'])}")
print(f"Stage B complete: {bool(result['stage_b_results'])}")
```

**Current Output:**
```
================================================================================
📄 PROCESSING: annual_report.pdf
================================================================================

🔍 STAGE A: PAGE LOCATION
--------------------------------------------------------------------------------
[Page location results displayed]

💾 Saved Stage A results to: data/processed/extracted_json/annual_report_stage_a_locations.json

================================================================================
📊 STAGE B: STRUCTURED EXTRACTION
--------------------------------------------------------------------------------
📄 Extracting Income_Statement
   Pages: 25-27
   Confidence: 92.00%
   🔧 TODO: Full extraction implementation

[Stage B is partially implemented - shows TODOs]

Status: PENDING
```

---

## 🧪 Running Tests

### Run All Tests
```bash
cd "f:\Stock-Exchange-Prediction-Model-Project\Fundamental Analysis\Models\Ai Extractor"
pytest tests/ -v
```

### Run Specific Test Modules
```bash
# Test numeric normalization
pytest tests/test_numeric_normalizer.py -v -s

# Test column interpretation
pytest tests/test_column_interpreter.py -v -s

# Test mapping engine
pytest tests/test_mapping_engine.py -v -s

# Test page locator
pytest tests/test_page_locator.py -v -s
```

### Expected Test Results
```
tests/test_numeric_normalizer.py::TestNumericNormalizer::test_simple_number PASSED
tests/test_numeric_normalizer.py::TestNumericNormalizer::test_number_with_commas PASSED
tests/test_numeric_normalizer.py::TestNumericNormalizer::test_bracketed_number_as_negative PASSED
tests/test_numeric_normalizer.py::TestNumericNormalizer::test_dash_as_null PASSED
[... more tests ...]

================================ X passed in Y.YY s ================================
```

---

## 🐛 Troubleshooting

### Import Errors

**Problem:**
```
ModuleNotFoundError: No module named 'src'
```

**Solution:**
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
```

### PDF Not Found

**Problem:**
```
FileNotFoundError: PDF file not found
```

**Solution:**
Use absolute paths or check working directory:
```python
from pathlib import Path
pdf_path = Path('data/raw/hnb/hnb.pdf').absolute()
```

### Test Failures

**Problem:**
Some tests fail due to missing dependencies.

**Solution:**
```bash
pip install -r requirements.txt
```

---

## 📚 Next Steps for Development

### To Complete Stage B:

1. **Implement Table Detector**
   - File: `src/extractor/table_detector.py`
   - Use pdfplumber/camelot to extract tables
   - Return structured table with cell coordinates

2. **Implement Row Extractor**
   - File: `src/extractor/row_extractor.py`
   - Extract rows cell-by-cell
   - Wire together: column interpretation → normalization → mapping

3. **Complete Pipeline Integration**
   - Update `_extract_statement()` in `two_stage_pipeline.py`
   - Connect all components
   - Test end-to-end

4. **Finish Output Builders**
   - Complete `canonical_builder.py`
   - Complete `review_payload.py`
   - Add metadata

5. **Test with Real PDFs**
   - Start with small PDFs (50 pages)
   - Progress to large PDFs (500+ pages)
   - Measure accuracy and performance

---

## 📖 Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture and design
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - What's implemented and what's TODO
- [CLEANUP_PLAN.md](CLEANUP_PLAN.md) - File deprecation and cleanup plan
- [README.md](README.md) - Main project README (to be updated)

---

## 🎯 Quick Reference

### Key Components Status

| Component | Status | File |
|-----------|--------|------|
| ToC Detector | ✅ Complete | `src/locator/toc_detector.py` |
| Heading Scanner | ✅ Complete | `src/locator/heading_scanner.py` |
| Layout Analyzer | ✅ Complete | `src/locator/layout_analyzer.py` |
| Page Locator | ✅ Complete | `src/locator/page_locator.py` |
| Numeric Normalizer | ✅ Complete | `src/extractor/numeric_normalizer.py` |
| Column Interpreter | ✅ Complete | `src/extractor/column_interpreter.py` |
| Mapping Engine | ✅ Complete | `src/mapper/mapping_engine.py` |
| Table Detector | ⚠️ TODO | `src/extractor/table_detector.py` |
| Row Extractor | ⚠️ TODO | `src/extractor/row_extractor.py` |
| Canonical Builder | ⚠️ Stub | `src/schema/canonical_builder.py` |
| Review Payload | ⚠️ Stub | `src/schema/review_payload.py` |
| Two-Stage Pipeline | 🔄 Partial | `src/pipeline/two_stage_pipeline.py` |

### CLI Commands

```bash
# Run new pipeline (partial implementation)
python scripts/run_pipeline.py path/to/report.pdf

# Run old pipeline (for comparison)
python main_ml.py

# Run tests
pytest tests/ -v

# Run specific test
pytest tests/test_numeric_normalizer.py::TestNumericNormalizer::test_bracketed_number_as_negative -v
```

---

## 💡 Tips

1. **Start with Page Location**: Stage A is fully complete and very useful on its own
2. **Test Incrementally**: Test each component independently before integration
3. **Use Real PDFs**: Test with actual bank annual reports as soon as possible
4. **Check Confidence**: Always review confidence scores - they indicate reliability
5. **Review Flagged Items**: Low confidence items need manual review - that's by design

---

## 🤝 Contributing

When continuing development:

1. Follow the modular architecture
2. Add tests for new components
3. Update documentation as you go
4. Use type hints and docstrings
5. Keep confidence scoring in mind
6. Design for review workflow

---

## ✅ Summary

**You can use right now:**
- ✅ Page location with confidence scoring
- ✅ Numeric normalization
- ✅ Column interpretation
- ✅ Label mapping

**Coming soon (2-3 days of work):**
- ⚠️ Complete table extraction
- ⚠️ Full Stage B integration
- ⚠️ Canonical JSON output
- ⚠️ Review payload generation

The foundation is solid and ready to build on! 🚀
