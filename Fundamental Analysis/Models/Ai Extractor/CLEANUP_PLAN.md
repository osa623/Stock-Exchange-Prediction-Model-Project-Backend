# CODEBASE CLEANUP PLAN

## Files to DEPRECATE (Move to `deprecated/`)

These files contain useful logic but are replaced by new architecture. Move to `deprecated/` folder with README explaining why.

### Pipeline Files (OLD → NEW)
```
DEPRECATE: src/pipeline/extract_ml.py
REASON: Replaced by src/pipeline/two_stage_pipeline.py
OLD FEATURES: ML extraction pipeline
NEW LOCATION: Logic integrated into two-stage pipeline
TIMELINE: Move after new pipeline is fully tested

DEPRECATE: src/pipeline/ml_extractor.py  
REASON: Replaced by modular extractors in src/extractor/
OLD FEATURES: Monolithic ML-based extractor
NEW LOCATION: Split into table_detector, column_interpreter, row_extractor
TIMELINE: Move after Stage B is complete
```

### ML Components (INTEGRATED → NEW)
```
DEPRECATE: src/ml/document_classifier.py
REASON: Functionality integrated into src/locator/ modules
OLD FEATURES: Document classification for page location
NEW LOCATION: Integrated into page_locator.py, heading_scanner.py
TIMELINE: Move after page locator is validated

DEPRECATE: src/ml/intelligent_field_matcher.py
REASON: Replaced by src/mapper/mapping_engine.py
OLD FEATURES: ML-based field matching
NEW LOCATION: src/mapper/ with cascading strategy
TIMELINE: Move after mapping engine is tested
```

### Old Page Locator (DUPLICATE)
```
DEPRECATE: src/pdf/page_locator.py (OLD VERSION)
REASON: Replaced by src/locator/page_locator.py (NEW VERSION)
NEW VERSION: Complete rewrite with ToC, heading, and layout analysis
TIMELINE: Move immediately (new version is complete)
```

### Extraction Utilities (MAYBE)
```
EVALUATE: src/extraction/key_value.py
REASON: May not be actively used
ACTION: Check imports and references
IF UNUSED: Move to deprecated/
IF USED: Keep and document
```

### Test Files (OLD)
```
DEPRECATE: test_ml_extraction.py (root level)
REASON: Old test for deprecated ml_extractor.py
NEW VERSION: tests/test_page_locator.py and new test suite
TIMELINE: Move after new tests are validated
```

---

## Files to DELETE (After Verification)

These are placeholder/test files outside the main codebase with no imports or references.

### Test Placeholders (SAFE TO DELETE)
```
DELETE: app/test.py
DELETE: Economic Analysis/test.py  
DELETE: Fundamental Analysis/test.py
DELETE: Fundamental Analysis/Caculations/test.py
DELETE: Fundamental Analysis/Forecasting/test.py
DELETE: Fundamental Analysis/Models/test.py
DELETE: Order Flow Analysis/test.py
DELETE: Sentimental Analysis/test.py
DELETE: Technical Analysis/test.py

REASON: Empty placeholder files, not part of extraction system
ACTION: Delete after confirming no imports
VERIFICATION: grep -r "from.*test import" . (should find nothing)
```

### Empty Test Files (POPULATE OR DELETE)
```
STATUS: tests/test_number_cleaning.py (EMPTY)
ACTION: Either populate with tests or delete
DECISION: Populate with numeric normalization tests (DONE - see test_numeric_normalizer.py)
```

---

## Files to KEEP (No Changes)

### Core Configuration
```
✅ config/keywords.py - Statement detection keywords
✅ config/settings.yaml - System configuration  
✅ config/target_schema_bank.py - Target schema definition
✅ config/term_mapping_bank.py - Synonym mappings
```

### PDF Processing
```
✅ src/pdf/loader.py - PDF loading utilities
✅ src/pdf/ocr.py - OCR processing
✅ src/pdf/table_extractor.py - Table extraction (to be used by new pipeline)
```

### Extraction Utilities
```
✅ src/extraction/normalizer.py - Legacy normalizer (keep for reference)
✅ src/extraction/currency_detector.py - Currency detection
✅ src/extraction/period_detector.py - Period detection
```

### Validation
```
✅ src/validation/accounting_rules.py - Accounting validation
✅ src/validation/confidence_score.py - Confidence scoring
```

### Utilities
```
✅ src/utils/helpers.py - Helper functions
✅ src/utils/logger.py - Logging utilities
```

### Storage
```
✅ src/storage/save_json.py - JSON output
✅ src/storage/db_writer.py - Database writing
```

### Scripts
```
✅ scripts/run_single_pdf.py - Single PDF runner (to be updated)
✅ scripts/run_batch.py - Batch processing (to be updated)
```

### Data & Logs
```
✅ data/ - All data folders
✅ logs/ - Log files
✅ app/ - Web app templates (if used) - EVALUATE for deprecation
```

---

## Deprecation Process

### Step 1: Create Deprecated Folder
```bash
mkdir deprecated
```

### Step 2: Create README in deprecated/
```markdown
# Deprecated Code

This folder contains code that has been replaced by the new two-stage pipeline architecture.

## Why These Files Were Deprecated

The original extraction system had several limitations:
- Monolithic design (hard to test and maintain)
- OCR-first approach (expensive and error-prone)
- Inconsistent page location
- Limited validation

The new architecture addresses these with:
- Two-stage pipeline (locate then extract)
- Table-first extraction
- Confidence scoring at every step
- Comprehensive validation

## Files in This Folder

### `extract_ml.py` (OLD PIPELINE)
- **Deprecated**: [Date]
- **Replaced by**: `src/pipeline/two_stage_pipeline.py`
- **Reason**: Monolithic design, replaced by modular two-stage approach

### `ml_extractor.py` (OLD EXTRACTOR)
- **Deprecated**: [Date]
- **Replaced by**: Multiple modules in `src/extractor/`, `src/mapper/`
- **Reason**: Split into specialized components for better maintainability

### `document_classifier.py` (OLD ML)
- **Deprecated**: [Date]
- **Replaced by**: `src/locator/page_locator.py`
- **Reason**: Integrated into new page location strategy

### `intelligent_field_matcher.py` (OLD MATCHER)
- **Deprecated**: [Date]
- **Replaced by**: `src/mapper/mapping_engine.py`
- **Reason**: New cascading strategy with better confidence scoring

## Can I Delete These Files?

**Not yet!** Keep them for:
1. Reference during development
2. Comparison testing
3. Migration validation

**Timeline**: These files can be permanently deleted after:
- New pipeline is fully tested
- All edge cases are handled
- Performance is validated
- Team has reviewed and approved

**Estimated**: 2-3 months after new pipeline is deployed to production.
```

### Step 3: Move Files
```bash
# Move old pipeline files
mv src/pipeline/extract_ml.py deprecated/
mv src/pipeline/ml_extractor.py deprecated/

# Move old ML components
mv src/ml/document_classifier.py deprecated/
mv src/ml/intelligent_field_matcher.py deprecated/

# Move old page locator
mv src/pdf/page_locator.py deprecated/page_locator_old.py

# Move old test
mv test_ml_extraction.py deprecated/
```

### Step 4: Update Imports
```bash
# Find any remaining imports of deprecated modules
grep -r "from src.pipeline.extract_ml import" .
grep -r "from src.pipeline.ml_extractor import" .
grep -r "from src.ml.document_classifier import" .
grep -r "from src.ml.intelligent_field_matcher import" .

# Update or remove these imports
```

### Step 5: Verify No Breakage
```bash
# Run all tests
pytest tests/ -v

# Try running main scripts
python scripts/run_pipeline.py --help

# Check for import errors
python -c "from src.pipeline.two_stage_pipeline import TwoStagePipeline"
```

---

## File Deletion Process

### Step 1: Verify No References
```bash
# For each file to delete, verify no imports
grep -r "from app.test import" .
grep -r "import.*test" . | grep -v "pytest" | grep -v "__pycache__"
```

### Step 2: Safe Delete (Git)
```bash
# Using git, so we can recover if needed
git rm app/test.py
git rm "Economic Analysis/test.py"
git rm "Fundamental Analysis/test.py"
# ... etc for all test.py placeholders

git commit -m "Remove empty placeholder test files"
```

### Step 3: Verify System Still Works
```bash
pytest tests/ -v
python scripts/run_pipeline.py --help
```

---

## App Folder Evaluation

The `app/` folder contains web app scaffolding:
```
app/
├── __pycache__/
├── results/
├── statement_images/
├── templates/
└── uploads/
```

**Action**: EVALUATE
- If this is used for a web UI: KEEP and document
- If this is unused/experimental: MOVE to deprecated/
- If this is for future use: KEEP but mark as "future"

**Decision**: Move to `deprecated/web_app_stub/` unless actively used.

---

## Summary

### Immediate Actions (Safe):
1. ✅ Create `deprecated/` folder
2. ✅ Create `deprecated/README.md`
3. ⚠️ Move `src/pdf/page_locator.py` → `deprecated/page_locator_old.py`
4. ⚠️ Delete empty test.py placeholders (after grep verification)

### After New Pipeline is Tested:
5. ⚠️ Move old pipeline files to deprecated/
6. ⚠️ Move old ML components to deprecated/
7. ⚠️ Evaluate and move app/ folder if unused

### After 2-3 Months in Production:
8. ⚠️ Permanently delete deprecated/ folder

---

## Risk Mitigation

**Why not delete immediately?**
1. May need to reference old logic
2. May need to compare outputs
3. May need to revert if issues found
4. Team may need time to review

**Safety measures:**
1. Use git (can always recover)
2. Move to deprecated/ first (don't delete)
3. Keep deprecated/ for 2-3 months
4. Document why each file was deprecated
5. Verify no imports before moving

**Rollback plan:**
If new pipeline has issues:
1. Old files are in deprecated/ or git history
2. Can temporarily revert imports
3. Can compare outputs side-by-side
4. Can cherry-pick useful logic
