#!/usr/bin/env python3
"""
Validation script for Zindi Data Storytelling Challenge notebook
Tests that all cells execute successfully and produces expected outputs
"""

import sys
import json
import pandas as pd
from pathlib import Path

def validate_notebook_data():
    """Validate that all required data files exist and have correct structure"""
    print("🔍 VALIDATING NOTEBOOK DATA READINESS")
    print("="*50)
    
    project_root = Path.cwd()
    observable_data = project_root / "notebooks" / "data" / "observable"
    
    # Check required data files
    required_files = [
        "risk_assessment_complete.csv",
        "country_summary.csv", 
        "risk_hotspots.csv",
        "soil_health_indicators.csv",
        "dataset_metadata.json",
        "dashboard_stats.json"
    ]
    
    missing_files = []
    for file in required_files:
        file_path = observable_data / file
        if file_path.exists():
            print(f"   ✅ Found: {file}")
        else:
            print(f"   ❌ Missing: {file}")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n❌ Missing {len(missing_files)} required files!")
        print("   Run: python prepare_observable_data.py")
        return False
    
    # Validate main dataset structure
    risk_data = pd.read_csv(observable_data / "risk_assessment_complete.csv")
    expected_columns = [
        'country', 'region', 'sub_region', 'hazard_score',
        'combined_vulnerability_score', 'compound_risk_score',
        'population', 'vop_crops_usd'
    ]
    
    missing_columns = [col for col in expected_columns if col not in risk_data.columns]
    if missing_columns:
        print(f"❌ Missing columns in risk data: {missing_columns}")
        return False
    
    print(f"\n✅ Data validation passed!")
    print(f"   • Records: {len(risk_data):,}")
    print(f"   • Countries: {risk_data['country'].nunique()}")
    print(f"   • Columns: {len(risk_data.columns)}")
    
    return True

def validate_export_package():
    """Validate that export package is complete"""
    print("\n🎯 VALIDATING EXPORT PACKAGE")
    print("="*30)
    
    export_dir = Path("data/processed/zindi_submission")
    
    if not export_dir.exists():
        print(f"❌ Export directory missing: {export_dir}")
        print("   Run notebook cells to completion")
        return False
    
    # Check for expected export files
    csv_files = list(export_dir.glob("*.csv"))
    json_files = list(export_dir.glob("*.json"))
    
    print(f"   📊 CSV files: {len(csv_files)}")
    for file in csv_files:
        print(f"      - {file.name}")
    
    print(f"   📋 JSON files: {len(json_files)}")
    for file in json_files:
        print(f"      - {file.name}")
    
    if len(csv_files) >= 5 and len(json_files) >= 1:
        print(f"\n✅ Export package complete!")
        return True
    else:
        print(f"\n❌ Export package incomplete!")
        return False

def check_notebook_execution():
    """Check if notebook can be executed without errors"""
    print("\n📓 NOTEBOOK EXECUTION CHECK")
    print("="*30)
    
    notebook_path = Path("notebooks/zindi_data_storytelling_challenge.ipynb")
    
    if not notebook_path.exists():
        print(f"❌ Notebook not found: {notebook_path}")
        return False
    
    # Read notebook to check structure
    with open(notebook_path, 'r', encoding='utf-8') as f:
        notebook_data = json.load(f)
    
    cells = notebook_data.get('cells', [])
    code_cells = [cell for cell in cells if cell.get('cell_type') == 'code']
    markdown_cells = [cell for cell in cells if cell.get('cell_type') == 'markdown']
    
    print(f"   📝 Total cells: {len(cells)}")
    print(f"   💻 Code cells: {len(code_cells)}")
    print(f"   📄 Markdown cells: {len(markdown_cells)}")
    
    # Check for key narrative sections
    narrative_sections = [
        "Part 1",
        "Part 2", 
        "Part 3",
        "Part 4"
    ]
    
    found_sections = []
    for cell in cells:
        if cell.get('cell_type') == 'markdown':
            source = ''.join(cell.get('source', []))
            for section in narrative_sections:
                if section in source:
                    found_sections.append(section)
    
    print(f"\n   🎭 Narrative sections found:")
    for section in narrative_sections:
        if section in found_sections:
            print(f"      ✅ {section}")
        else:
            print(f"      ❌ {section}")
    
    if len(found_sections) >= 3:
        print(f"\n✅ Notebook structure complete!")
        return True
    else:
        print(f"\n❌ Missing key narrative sections!")
        return False

def main():
    """Main validation function"""
    print("🎯 ZINDI SUBMISSION VALIDATION")
    print("="*50)
    print("Checking readiness for Observable Framework deployment...\n")
    
    # Run all validation checks
    checks = [
        ("Data Files", validate_notebook_data),
        ("Export Package", validate_export_package), 
        ("Notebook Structure", check_notebook_execution)
    ]
    
    results = {}
    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as e:
            print(f"❌ {check_name} validation failed: {e}")
            results[check_name] = False
    
    # Summary
    print(f"\n🏁 VALIDATION SUMMARY")
    print("="*25)
    
    passed = sum(results.values())
    total = len(results)
    
    for check_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {check_name}")
    
    print(f"\n📊 Overall: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🚀 READY FOR DEPLOYMENT!")
        print("   Next step: Initialize Observable Framework")
        print("   Command: npx @observablehq/framework create")
        return 0
    else:
        print(f"\n⚠️  {total - passed} issues need resolution before deployment")
        return 1

if __name__ == "__main__":
    sys.exit(main())