#!/usr/bin/env python3
"""
Atlas Data Cleaning & Issue Resolution
=====================================

This script addresses the issues found during validation:
1. Handle missing values in critical columns
2. Standardize country names
3. Re-validate the cleaned dataset

Run this AFTER validation to fix identified issues.
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from config import Config

def handle_missing_values(df):
    """Handle missing values in critical columns."""
    print("\n🔧 HANDLING MISSING VALUES")
    print("="*40)
    
    original_count = len(df)
    
    # Check missing values before cleaning
    ndws_missing = df['ndws_future_days'].isnull().sum()
    poverty_missing = df['poverty_headcount_ratio'].isnull().sum()
    
    print(f"📊 Missing values before cleaning:")
    print(f"   NDWS (water stress): {ndws_missing}")
    print(f"   Poverty headcount: {poverty_missing}")
    
    # Option 1: Remove records with missing critical values
    print(f"\n🗑️ Removing records with missing critical values...")
    df_cleaned = df.dropna(subset=['ndws_future_days', 'poverty_headcount_ratio'])
    
    removed_count = original_count - len(df_cleaned)
    print(f"   Removed {removed_count} records ({removed_count/original_count*100:.1f}%)")
    print(f"   Remaining: {len(df_cleaned):,} records")
    
    # Recalculate risk scores for remaining data
    print(f"\n⚡ Recalculating risk scores...")
    df_cleaned['hazard_score'] = df_cleaned['ndws_future_days'] / df_cleaned['ndws_future_days'].max()
    df_cleaned['social_vulnerability_score'] = df_cleaned['poverty_headcount_ratio'] / df_cleaned['poverty_headcount_ratio'].max()
    df_cleaned['preliminary_risk_score'] = df_cleaned['hazard_score'] * df_cleaned['social_vulnerability_score']
    
    print(f"   ✅ Risk scores recalculated for clean dataset")
    
    return df_cleaned

def standardize_country_names(df):
    """Standardize country names for consistency."""
    print(f"\n🌍 STANDARDIZING COUNTRY NAMES")
    print("="*40)
    
    # Country name standardization mapping
    country_mapping = {
        'Côte d\'Ivoire': 'Cote d\'Ivoire',  # Remove special characters
        'Congo - Kinshasa': 'Democratic Republic of the Congo',
        'Congo - Brazzaville': 'Republic of the Congo'
    }
    
    changes_made = 0
    for old_name, new_name in country_mapping.items():
        if old_name in df['country'].values:
            count = (df['country'] == old_name).sum()
            df.loc[df['country'] == old_name, 'country'] = new_name
            changes_made += count
            print(f"   📝 Changed '{old_name}' → '{new_name}' ({count} records)")
    
    if changes_made == 0:
        print(f"   ✅ No country name changes needed")
    else:
        print(f"   ✅ Standardized {changes_made} country name entries")
    
    return df

def validate_cleaned_data(df):
    """Quick validation of the cleaned dataset."""
    print(f"\n🔍 VALIDATING CLEANED DATASET")
    print("="*40)
    
    issues = []
    
    # Check for missing values in critical columns
    critical_missing = {
        'ndws_future_days': df['ndws_future_days'].isnull().sum(),
        'poverty_headcount_ratio': df['poverty_headcount_ratio'].isnull().sum()
    }
    
    for col, missing_count in critical_missing.items():
        if missing_count > 0:
            issues.append(f"Still have missing {col}: {missing_count}")
        else:
            print(f"   ✅ No missing values in {col}")
    
    # Check risk score calculation
    calculated_risk = df['hazard_score'] * df['social_vulnerability_score']
    risk_diff = abs(calculated_risk - df['preliminary_risk_score'])
    max_diff = risk_diff.max()
    
    if max_diff > 0.001:
        issues.append(f"Risk calculation error: {max_diff:.6f}")
    else:
        print(f"   ✅ Risk scores correctly calculated")
    
    # Check data ranges
    range_issues = []
    if (df['hazard_score'] < 0).any() or (df['hazard_score'] > 1).any():
        range_issues.append("hazard_score out of 0-1 range")
    if (df['social_vulnerability_score'] < 0).any() or (df['social_vulnerability_score'] > 1).any():
        range_issues.append("social_vulnerability_score out of 0-1 range")
    
    if range_issues:
        issues.extend(range_issues)
    else:
        print(f"   ✅ All scores within expected ranges")
    
    # Summary statistics
    print(f"\n📊 Cleaned Dataset Summary:")
    print(f"   Records: {len(df):,}")
    print(f"   Countries: {df['country'].nunique()}")
    print(f"   Sub-regions: {df['sub_region'].nunique()}")
    print(f"   Completeness: {((df.notna().sum().sum()) / (len(df) * len(df.columns)) * 100):.1f}%")
    
    return issues

def create_cleaning_report(original_df, cleaned_df, output_path):
    """Create a report of cleaning operations performed."""
    print(f"\n📋 DATA CLEANING SUMMARY")
    print("="*40)
    
    original_count = len(original_df)
    cleaned_count = len(cleaned_df)
    removed_count = original_count - cleaned_count
    
    print(f"📊 Cleaning Results:")
    print(f"   Original records: {original_count:,}")
    print(f"   Cleaned records: {cleaned_count:,}")
    print(f"   Removed records: {removed_count:,} ({removed_count/original_count*100:.1f}%)")
    print(f"   Data retention: {cleaned_count/original_count*100:.1f}%")
    
    # Top risk areas comparison
    print(f"\n🔥 Top 5 Risk Areas (After Cleaning):")
    top_risk = cleaned_df.nlargest(5, 'preliminary_risk_score')
    for idx, (_, row) in enumerate(top_risk.iterrows(), 1):
        print(f"   {idx}. {row['country']}, {row['sub_region']} (Risk: {row['preliminary_risk_score']:.3f})")
    
    # Save detailed report
    with open(output_path, 'w') as f:
        f.write("ATLAS DATASET CLEANING REPORT\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Cleaning Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("CLEANING OPERATIONS\n")
        f.write("-" * 20 + "\n")
        f.write(f"Original Records: {original_count:,}\n")
        f.write(f"Records Removed: {removed_count:,}\n")
        f.write(f"Final Records: {cleaned_count:,}\n")
        f.write(f"Data Retention Rate: {cleaned_count/original_count*100:.1f}%\n\n")
        
        f.write("OPERATIONS PERFORMED\n")
        f.write("-" * 20 + "\n")
        f.write("1. Removed records with missing NDWS or poverty data\n")
        f.write("2. Standardized country names\n")
        f.write("3. Recalculated risk scores on clean data\n")
        f.write("4. Validated cleaned dataset\n\n")
        
        f.write("QUALITY METRICS\n")
        f.write("-" * 20 + "\n")
        f.write(f"Countries: {cleaned_df['country'].nunique()}\n")
        f.write(f"Regions: {cleaned_df['region'].nunique()}\n")
        f.write(f"Sub-regions: {cleaned_df['sub_region'].nunique()}\n")
        f.write(f"Completeness: {((cleaned_df.notna().sum().sum()) / (len(cleaned_df) * len(cleaned_df.columns)) * 100):.1f}%\n")

def main():
    """Main cleaning function."""
    config = Config()
    PROCESSED_DATA_PATH = config.PROCESSED_DATA_PATH
    
    print("🧹 ATLAS DATASET CLEANING & ISSUE RESOLUTION")
    print("="*60)
    print("🔧 Addressing issues found during validation")
    print("🎯 Goal: Create a clean, analysis-ready dataset")
    print("="*60)
    
    # Load the original fused dataset
    master_file = PROCESSED_DATA_PATH / "master_atlas_data.csv"
    
    if not master_file.exists():
        print(f"❌ Master dataset not found: {master_file}")
        return False
    
    try:
        df_original = pd.read_csv(master_file)
        print(f"✅ Loaded original dataset: {len(df_original):,} records")
    except Exception as e:
        print(f"❌ Error loading dataset: {e}")
        return False
    
    # Perform cleaning operations
    df_cleaned = handle_missing_values(df_original.copy())
    df_cleaned = standardize_country_names(df_cleaned)
    
    # Validate cleaned dataset
    validation_issues = validate_cleaned_data(df_cleaned)
    
    if validation_issues:
        print(f"\n❌ Cleaning validation failed:")
        for issue in validation_issues:
            print(f"   - {issue}")
        return False
    
    # Save cleaned dataset
    cleaned_file = PROCESSED_DATA_PATH / "master_atlas_data_cleaned.csv"
    df_cleaned.to_csv(cleaned_file, index=False)
    print(f"\n💾 Cleaned dataset saved: {cleaned_file}")
    
    # Create cleaning report
    report_path = PROCESSED_DATA_PATH / "atlas_data_cleaning_report.txt"
    create_cleaning_report(df_original, df_cleaned, report_path)
    print(f"📁 Cleaning report saved: {report_path}")
    
    print(f"\n✅ DATA CLEANING COMPLETED SUCCESSFULLY!")
    print(f"🚀 Clean dataset ready for geospatial processing")
    print(f"📁 Use: {cleaned_file}")
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎯 Cleaning completed successfully!")
    else:
        print("\n❌ Cleaning failed. Please check errors and retry.")