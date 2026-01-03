"""
Explanation of deprecated code and migration path.
This folder contains code replaced by the new two-stage pipeline architecture.
"""

DEPRECATED_MODULES = {
    "extract_ml.py": {
        "deprecated_date": "2026-01-03",
        "replaced_by": "src/pipeline/two_stage_pipeline.py",
        "reason": "Monolithic design replaced by modular two-stage approach",
        "timeline": "Delete after 3 months of production use"
    },
    "ml_extractor.py": {
        "deprecated_date": "2026-01-03",
        "replaced_by": ["src/extractor/", "src/mapper/"],
        "reason": "Split into specialized components for better maintainability",
        "timeline": "Delete after 3 months of production use"
    },
    "document_classifier.py": {
        "deprecated_date": "2026-01-03",
        "replaced_by": "src/locator/page_locator.py",
        "reason": "Integrated into new page location strategy",
        "timeline": "Delete after 3 months of production use"
    },
    "intelligent_field_matcher.py": {
        "deprecated_date": "2026-01-03",
        "replaced_by": "src/mapper/mapping_engine.py",
        "reason": "New cascading strategy with better confidence scoring",
        "timeline": "Delete after 3 months of production use"
    },
    "page_locator_old.py": {
        "deprecated_date": "2026-01-03",
        "replaced_by": "src/locator/page_locator.py",
        "reason": "Complete rewrite with ToC detection and layout analysis",
        "timeline": "Delete after new version is validated"
    }
}


def print_deprecation_info():
    """Print information about deprecated modules."""
    print("\n" + "="*80)
    print("DEPRECATED MODULES")
    print("="*80 + "\n")
    
    for module, info in DEPRECATED_MODULES.items():
        print(f"📦 {module}")
        print(f"   Deprecated: {info['deprecated_date']}")
        print(f"   Replaced by: {info['replaced_by']}")
        print(f"   Reason: {info['reason']}")
        print(f"   Timeline: {info['timeline']}")
        print()
    
    print("="*80)
    print("⚠️  DO NOT USE THESE MODULES IN NEW CODE")
    print("✅ Refer to ARCHITECTURE.md for the new design")
    print("="*80 + "\n")


if __name__ == "__main__":
    print_deprecation_info()
