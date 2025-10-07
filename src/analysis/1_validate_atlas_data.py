#!/usr/bin/env python3
"""
Atlas Data Validation & Quality Assurance
=========================================

This script performs comprehensive validation of the fused Atlas dataset:
1. Data integrity checks (ranges, distributions, consistency)
2. Geographic validation (coverage, boundaries, completeness)
3. Statistical validation (outliers, correlations, logical relationships)
4. Risk assessment validation (formula verification, hotspot validation)
5. Data export validation (file integrity, format compliance)

Run this AFTER fusion to ensure data quality before proceeding to geospatial processing.
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

# Add src to path for imports
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from config import Config

def validate_data_integrity(df):
    """Validate basic data integrity and structure."""
    print("\n🔍 DATA INTEGRITY VALIDATION")
    print("="*50)
    
    issues = []
    
    # Check for required columns
    required_cols = [
        'country', 'region', 'sub_region', 
        'ndws_future_days', 'poverty_headcount_ratio', 
        'vop_crops_usd', 'population',
        'hazard_score', 'social_vulnerability_score', 'preliminary_risk_score'
    ]
    
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        issues.append(f"Missing required columns: {missing_cols}")
        print(f"❌ Missing columns: {missing_cols}")
    else:
        print("✅ All required columns present")
    
    # Check for duplicate sub-regions
    admin_cols = ['country', 'region', 'sub_region']
    duplicates = df.duplicated(subset=admin_cols).sum()
    if duplicates > 0:
        issues.append(f"Found {duplicates} duplicate sub-regions")
        print(f"❌ Duplicate sub-regions: {duplicates}")
        
        # Show examples
        duplicate_examples = df[df.duplicated(subset=admin_cols, keep=False)].head()
        print("   Example duplicates:")
        for _, row in duplicate_examples.iterrows():
            print(f"   - {row['country']}, {row['region']}, {row['sub_region']}")
    else:
        print("✅ No duplicate sub-regions found")
    
    # Check data types
    expected_types = {
        'ndws_future_days': 'float64',
        'poverty_headcount_ratio': 'float64',
        'vop_crops_usd': 'float64',
        'population': 'float64'
    }
    
    type_issues = []
    for col, expected_type in expected_types.items():
        if col in df.columns:
            actual_type = str(df[col].dtype)
            if not actual_type.startswith('float') and not actual_type.startswith('int'):
                type_issues.append(f"{col}: expected numeric, got {actual_type}")
    
    if type_issues:
        issues.append(f"Data type issues: {type_issues}")
        print(f"❌ Data type issues: {type_issues}")
    else:
        print("✅ All numeric columns have correct data types")
    
    # Check for missing values in critical columns
    critical_missing = {}
    for col in ['ndws_future_days', 'poverty_headcount_ratio']:
        missing_count = df[col].isnull().sum()
        if missing_count > 0:
            critical_missing[col] = missing_count
    
    if critical_missing:
        issues.append(f"Missing values in critical columns: {critical_missing}")
        print(f"❌ Missing values in critical columns: {critical_missing}")
    else:
        print("✅ No missing values in critical risk assessment columns")
    
    return issues

def validate_value_ranges(df):
    """Validate that values are within expected ranges."""
    print("\n📊 VALUE RANGE VALIDATION")
    print("="*50)
    
    issues = []
    
    # Define expected ranges
    range_checks = {
        'ndws_future_days': (0, 365, "Water stress days should be 0-365"),
        'poverty_headcount_ratio': (0, 1, "Poverty ratio should be 0-1 (0-100%)"),
        'vop_crops_usd': (0, float('inf'), "Agricultural value should be non-negative"),
        'population': (0, float('inf'), "Population should be non-negative"),
        'hazard_score': (0, 1, "Hazard score should be normalized 0-1"),
        'social_vulnerability_score': (0, 1, "Vulnerability score should be normalized 0-1"),
        'preliminary_risk_score': (0, 1, "Risk score should be normalized 0-1")
    }
    
    for col, (min_val, max_val, description) in range_checks.items():
        if col not in df.columns:
            continue
            
        values = df[col].dropna()
        if len(values) == 0:
            continue
            
        out_of_range = ((values < min_val) | (values > max_val)).sum()
        
        print(f"\n📏 {col}:")
        print(f"   Range: [{values.min():.3f}, {values.max():.3f}]")
        print(f"   Expected: [{min_val}, {max_val}]")
        
        if out_of_range > 0:
            issues.append(f"{col}: {out_of_range} values out of expected range")
            print(f"   ❌ {out_of_range} values out of range")
            
            # Show extreme values
            extreme_low = values[values < min_val]
            extreme_high = values[values > max_val]
            if len(extreme_low) > 0:
                print(f"   📉 Below range: {extreme_low.min():.3f} to {extreme_low.max():.3f}")
            if len(extreme_high) > 0:
                print(f"   📈 Above range: {extreme_high.min():.3f} to {extreme_high.max():.3f}")
        else:
            print(f"   ✅ All values within expected range")
    
    return issues

def validate_geographic_coverage(df):
    """Validate geographic coverage and administrative boundaries."""
    print("\n🌍 GEOGRAPHIC COVERAGE VALIDATION")
    print("="*50)
    
    issues = []
    
    # Expected Sub-Saharan Africa countries (comprehensive list)
    ssa_countries = {
        'Angola', 'Benin', 'Botswana', 'Burkina Faso', 'Burundi', 'Cameroon', 
        'Cape Verde', 'Central African Republic', 'Chad', 'Comoros', 
        'Democratic Republic of the Congo', 'Republic of the Congo', 'Congo - Kinshasa',
        'Congo - Brazzaville', 'Cote d\'Ivoire', 'Ivory Coast', 'Djibouti', 
        'Equatorial Guinea', 'Eritrea', 'Eswatini', 'Ethiopia', 'Gabon', 'Gambia', 
        'Ghana', 'Guinea', 'Guinea-Bissau', 'Kenya', 'Lesotho', 'Liberia', 
        'Madagascar', 'Malawi', 'Mali', 'Mauritania', 'Mauritius', 'Mozambique', 
        'Namibia', 'Niger', 'Nigeria', 'Rwanda', 'Sao Tome and Principe', 
        'Senegal', 'Seychelles', 'Sierra Leone', 'Somalia', 'South Africa', 
        'South Sudan', 'Sudan', 'Tanzania', 'Togo', 'Uganda', 'Zambia', 'Zimbabwe'
    }
    
    # Add the exact Côte d'Ivoire variant from the data (Unicode: 67, 244, 116, 101, 32, 100, 8217, 73, 118, 111, 105, 114, 101)
    exact_cote_divoire = ''.join([chr(c) for c in [67, 244, 116, 101, 32, 100, 8217, 73, 118, 111, 105, 114, 101]])
    ssa_countries.add(exact_cote_divoire)
    
    countries_in_data = set(df['country'].unique())
    
    # Check for non-SSA countries
    non_ssa = countries_in_data - ssa_countries
    if non_ssa:
        issues.append(f"Non-SSA countries found: {non_ssa}")
        print(f"⚠️  Non-SSA countries: {sorted(non_ssa)}")
        print("   (May be acceptable if using different country name variants)")
    else:
        print("✅ All countries appear to be in Sub-Saharan Africa")
    
    # Check coverage statistics
    print(f"\n📊 Coverage Statistics:")
    print(f"   Countries: {len(countries_in_data)}")
    print(f"   Regions: {df['region'].nunique()}")
    print(f"   Sub-regions: {df['sub_region'].nunique()}")
    print(f"   Total records: {len(df):,}")
    
    # Check for countries with very few sub-regions (potential data issues)
    country_counts = df['country'].value_counts()
    sparse_countries = country_counts[country_counts < 5]
    
    if len(sparse_countries) > 0:
        print(f"\n⚠️  Countries with <5 sub-regions (check for completeness):")
        for country, count in sparse_countries.items():
            print(f"   {country}: {count} sub-regions")
    
    # Check for missing administrative names
    admin_missing = {
        'country': df['country'].isnull().sum(),
        'region': df['region'].isnull().sum(), 
        'sub_region': df['sub_region'].isnull().sum()
    }
    
    for admin_level, missing_count in admin_missing.items():
        if missing_count > 0:
            issues.append(f"Missing {admin_level} names: {missing_count}")
            print(f"❌ Missing {admin_level}: {missing_count} records")
    
    return issues

def validate_statistical_relationships(df):
    """Validate statistical relationships and correlations."""
    print("\n📈 STATISTICAL RELATIONSHIP VALIDATION")
    print("="*50)
    
    issues = []
    
    # Check correlation between hazard and vulnerability scores
    if 'hazard_score' in df.columns and 'social_vulnerability_score' in df.columns:
        correlation = df['hazard_score'].corr(df['social_vulnerability_score'])
        print(f"🔗 Hazard vs Social Vulnerability correlation: {correlation:.3f}")
        
        if abs(correlation) > 0.8:
            issues.append(f"Very high correlation between hazard and vulnerability: {correlation:.3f}")
            print("   ⚠️  Unusually high correlation - check for data issues")
        elif abs(correlation) < 0.1:
            print("   ✅ Low correlation - good independence between hazard and vulnerability")
        else:
            print("   ✅ Moderate correlation - reasonable relationship")
    
    # Validate risk score calculation
    if all(col in df.columns for col in ['hazard_score', 'social_vulnerability_score', 'preliminary_risk_score']):
        calculated_risk = df['hazard_score'] * df['social_vulnerability_score']
        risk_diff = abs(calculated_risk - df['preliminary_risk_score'])
        max_diff = risk_diff.max()
        
        print(f"\n⚡ Risk Score Calculation Validation:")
        print(f"   Maximum difference from expected: {max_diff:.6f}")
        
        if max_diff > 0.001:  # Allow for small floating point errors
            issues.append(f"Risk score calculation error: max difference {max_diff:.6f}")
            print("   ❌ Risk score calculation appears incorrect")
        else:
            print("   ✅ Risk score calculation is correct")
    
    # Check for extreme outliers in key variables
    outlier_checks = ['ndws_future_days', 'poverty_headcount_ratio', 'vop_crops_usd', 'population']
    
    print(f"\n🔍 Outlier Analysis (IQR method):")
    for col in outlier_checks:
        if col not in df.columns:
            continue
            
        values = df[col].dropna()
        if len(values) == 0:
            continue
            
        Q1, Q3 = values.quantile([0.25, 0.75])
        IQR = Q3 - Q1
        lower_bound = Q1 - 3 * IQR  # Using 3*IQR for extreme outliers
        upper_bound = Q3 + 3 * IQR
        
        extreme_outliers = ((values < lower_bound) | (values > upper_bound)).sum()
        outlier_pct = (extreme_outliers / len(values)) * 100
        
        print(f"   {col}: {extreme_outliers} extreme outliers ({outlier_pct:.1f}%)")
        
        if outlier_pct > 10:  # More than 10% outliers is concerning
            issues.append(f"{col}: {outlier_pct:.1f}% extreme outliers")
            print(f"      ⚠️  High percentage of extreme outliers")
    
    return issues

def validate_risk_assessment_logic(df):
    """Validate the logic of risk assessment calculations."""
    print("\n⚡ RISK ASSESSMENT LOGIC VALIDATION")
    print("="*50)
    
    issues = []
    
    # Check top risk areas for logical consistency
    if 'preliminary_risk_score' in df.columns:
        top_risk = df.nlargest(10, 'preliminary_risk_score')
        
        print("🔥 Top 10 Risk Areas Validation:")
        print("   (Checking if high risk = high hazard × high vulnerability)")
        
        logical_issues = 0
        for idx, (_, row) in enumerate(top_risk.iterrows(), 1):
            hazard = row.get('hazard_score', 0)
            vulnerability = row.get('social_vulnerability_score', 0)
            risk = row.get('preliminary_risk_score', 0)
            
            # Check if either hazard or vulnerability is reasonably high
            if hazard < 0.3 and vulnerability < 0.3:
                logical_issues += 1
                print(f"   ⚠️  #{idx}: {row['country']}, {row['sub_region']}")
                print(f"       Risk: {risk:.3f}, but Hazard: {hazard:.3f}, Vulnerability: {vulnerability:.3f}")
        
        if logical_issues == 0:
            print("   ✅ All top risk areas have logical hazard/vulnerability combinations")
        else:
            issues.append(f"{logical_issues} top risk areas with questionable hazard/vulnerability scores")
    
    # Check for zero-risk areas (might indicate missing data)
    zero_risk = (df['preliminary_risk_score'] == 0).sum()
    zero_risk_pct = (zero_risk / len(df)) * 100
    
    print(f"\n🎯 Zero Risk Analysis:")
    print(f"   Records with zero risk: {zero_risk} ({zero_risk_pct:.1f}%)")
    
    if zero_risk_pct > 20:
        issues.append(f"High percentage of zero-risk areas: {zero_risk_pct:.1f}%")
        print("   ⚠️  High percentage of zero-risk areas - check for missing data")
    elif zero_risk_pct > 0:
        print("   ℹ️  Some zero-risk areas found - may be normal for low-hazard regions")
    else:
        print("   ✅ No zero-risk areas")
    
    return issues

def create_validation_report(all_issues, df, output_path):
    """Create comprehensive validation report."""
    print(f"\n📋 VALIDATION SUMMARY REPORT")
    print("="*60)
    
    total_issues = sum(len(issues) for issues in all_issues.values())
    
    if total_issues == 0:
        print("🎉 VALIDATION PASSED - No issues found!")
        status = "PASSED"
    else:
        print(f"⚠️  VALIDATION FOUND {total_issues} ISSUES")
        status = "ISSUES_FOUND"
    
    print(f"\n📊 Dataset Overview:")
    print(f"   Records: {len(df):,}")
    print(f"   Countries: {df['country'].nunique()}")
    print(f"   Sub-regions: {df['sub_region'].nunique()}")
    print(f"   Completeness: {((df.notna().sum().sum()) / (len(df) * len(df.columns)) * 100):.1f}%")
    
    # Issue breakdown
    print(f"\n🔍 Issue Breakdown:")
    for category, issues in all_issues.items():
        print(f"   {category}: {len(issues)} issues")
        for issue in issues:
            print(f"     - {issue}")
    
    # Save detailed report
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("ATLAS DATASET VALIDATION REPORT\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Validation Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Status: {status}\n")
        f.write(f"Total Issues Found: {total_issues}\n\n")
        
        f.write("DATASET SUMMARY\n")
        f.write("-" * 20 + "\n")
        f.write(f"Total Records: {len(df):,}\n")
        f.write(f"Countries: {df['country'].nunique()}\n")
        f.write(f"Regions: {df['region'].nunique()}\n")
        f.write(f"Sub-regions: {df['sub_region'].nunique()}\n\n")
        
        if total_issues > 0:
            f.write("ISSUES FOUND\n")
            f.write("-" * 20 + "\n")
            for category, issues in all_issues.items():
                if issues:
                    f.write(f"\n{category.upper()}:\n")
                    for issue in issues:
                        f.write(f"  - {issue}\n")
        else:
            f.write("✅ NO ISSUES FOUND - DATASET VALIDATION PASSED\n")
    
    return status

def main():
    """Main validation function."""
    config = Config()
    PROCESSED_DATA_PATH = config.PROCESSED_DATA_PATH
    
    print("🔍 ATLAS DATASET COMPREHENSIVE VALIDATION")
    print("="*60)
    print("📋 Validating fused Atlas dataset quality and integrity")
    print("🎯 Goal: Ensure data is ready for geospatial processing")
    print("="*60)
    
    # Load the fused dataset (try cleaned version first)
    cleaned_file = PROCESSED_DATA_PATH / "master_atlas_data_cleaned.csv"
    master_file = PROCESSED_DATA_PATH / "master_atlas_data.csv"
    
    if cleaned_file.exists():
        dataset_file = cleaned_file
        dataset_type = "cleaned"
    elif master_file.exists():
        dataset_file = master_file
        dataset_type = "original"
    else:
        print(f"❌ No dataset found. Please run fusion script first.")
        return False
    
    try:
        df = pd.read_csv(dataset_file)
        print(f"✅ Successfully loaded {dataset_type} dataset: {len(df):,} records")
    except Exception as e:
        print(f"❌ Error loading dataset: {e}")
        return False
    
    # Run all validation checks
    all_issues = {
        'data_integrity': validate_data_integrity(df),
        'value_ranges': validate_value_ranges(df),
        'geographic_coverage': validate_geographic_coverage(df),
        'statistical_relationships': validate_statistical_relationships(df),
        'risk_assessment_logic': validate_risk_assessment_logic(df)
    }
    
    # Create validation report
    report_path = PROCESSED_DATA_PATH / "atlas_data_validation_report.txt"
    status = create_validation_report(all_issues, df, report_path)
    
    print(f"\n📁 Detailed validation report saved: {report_path}")
    
    if status == "PASSED":
        print(f"\n✅ VALIDATION SUCCESSFUL!")
        print("🚀 Dataset is ready for Step 2: Geospatial processing")
        return True
    else:
        print(f"\n⚠️  VALIDATION FOUND ISSUES")
        print("🔧 Please review and address issues before proceeding")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎯 Validation completed successfully!")
    else:
        print("\n❌ Validation failed. Please fix issues and retry.")