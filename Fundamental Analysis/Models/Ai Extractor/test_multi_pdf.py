"""
Test extraction on multiple PDFs to verify all statements work.
"""
import json
from pathlib import Path
from src.pipeline.two_stage_pipeline import TwoStagePipeline

pdfs_to_test = [
    ("data/raw/pabc/pabc.pdf", "PABC"),
    ("data/raw/hnb/hnb.pdf", "HNB"),
    ("data/raw/commercial/Commerical.pdf", "Commercial"),
]

print("=" * 80)
print("MULTI-PDF EXTRACTION TEST")
print("=" * 80)

pipeline = TwoStagePipeline()

for pdf_path, name in pdfs_to_test:
    if not Path(pdf_path).exists():
        print(f"\n[SKIP] {name}: File not found at {pdf_path}")
        continue
    
    print(f"\n{'='*80}")
    print(f"Testing: {name}")
    print('=' * 80)
    
    try:
        result = pipeline.extract(pdf_path, save_intermediates=False)
        
        if result.get('status') == 'success':
            canonical = result['canonical_output']
            
            # Count fields per statement
            for entity in ['Bank', 'Group']:
                if entity in canonical and isinstance(canonical[entity], dict):
                    print(f"\n{entity}:")
                    for year_label in ['Year1', 'Year2']:
                        if year_label in canonical[entity]:
                            year_data = canonical[entity][year_label]
                            if isinstance(year_data, dict):
                                total = 0
                                details = []
                                for stmt_name, stmt_data in year_data.items():
                                    if isinstance(stmt_data, dict):
                                        count = len(stmt_data)
                                        total += count
                                        details.append(f"{stmt_name}: {count}")
                                
                                print(f"  {year_label} ({total} total fields):")
                                for detail in details:
                                    print(f"    - {detail}")
        else:
            print(f"[FAILED]: {result.get('error')}")
    
    except Exception as e:
        print(f"[ERROR]: {str(e)}")

print(f"\n{'='*80}")
print("TEST COMPLETE")
print('=' * 80)
