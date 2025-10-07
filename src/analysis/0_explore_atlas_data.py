#!/usr/bin/env python3
"""
Atlas Data Exploration & Quality Assessment
==========================================

This script performs comprehensive analysis of individual Atlas datasets before fusion:
1. Data structure and completeness analysis
2. Statistical summaries and distributions
3. Anomaly detection (outliers, missing values, duplicates)
4. Geographic coverage assessment
5. Data quality recommendations

Run this BEFORE the fusion script to understand data characteristics.
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter

# Add src to path for imports
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from config import Config

def analyze_dataset_structure(df, dataset_name):
    """Analyze basic structure and completeness of a dataset."""
    print(f"\n📊 {dataset_name.upper()} DATASET ANALYSIS")
    print("="*60)
    
    # Basic info
    print(f"📈 Shape: {df.shape[0]:,} rows × {df.shape[1]} columns")
    print(f"📂 Columns: {list(df.columns)}")
    print(f"💾 Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
    
    # Data types
    print(f"\n🔧 Data Types:")
    for col, dtype in df.dtypes.items():
        print(f"   {col}: {dtype}")
    
    # Missing values
    print(f"\n❓ Missing Values:")
    missing = df.isnull().sum()
    for col in missing.index:
        if missing[col] > 0:
            pct = (missing[col] / len(df)) * 100
            print(f"   {col}: {missing[col]:,} ({pct:.1f}%)")
        else:
            print(f"   {col}: 0 (0.0%)")
    
    # Unique values in key columns
    if 'admin0_name' in df.columns:
        print(f"\n🌍 Geographic Coverage:")
        print(f"   Countries: {df['admin0_name'].nunique()}")
        print(f"   Regions (Admin1): {df['admin1_name'].nunique()}")
        print(f"   Sub-regions (Admin2): {df['admin2_name'].nunique()}")
        
        # Top countries by record count
        top_countries = df['admin0_name'].value_counts().head(5)
        print(f"\n🔝 Top 5 Countries by Record Count:")
        for country, count in top_countries.items():
            print(f"   {country}: {count:,} records")
    
    return {
        'shape': df.shape,
        'missing_values': missing.to_dict(),
        'dtypes': df.dtypes.to_dict(),
        'countries': df['admin0_name'].nunique() if 'admin0_name' in df.columns else 0
    }

def analyze_value_distribution(df, dataset_name, value_col='value'):
    """Analyze the distribution of the main value column."""
    if value_col not in df.columns:
        print(f"⚠️ No '{value_col}' column found in {dataset_name}")
        return None
    
    values = df[value_col].dropna()
    
    print(f"\n📊 {value_col.upper()} DISTRIBUTION ANALYSIS")
    print("-"*40)
    print(f"📈 Count: {len(values):,}")
    print(f"📉 Missing: {df[value_col].isnull().sum():,}")
    print(f"🎯 Mean: {values.mean():.3f}")
    print(f"📊 Median: {values.median():.3f}")
    print(f"📏 Std Dev: {values.std():.3f}")
    print(f"🔻 Min: {values.min():.3f}")
    print(f"🔺 Max: {values.max():.3f}")
    
    # Percentiles
    percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
    print(f"\n📊 Percentiles:")
    for p in percentiles:
        val = np.percentile(values, p)
        print(f"   {p:2d}%: {val:.3f}")
    
    # Detect potential outliers using IQR method
    Q1 = values.quantile(0.25)
    Q3 = values.quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    
    outliers = values[(values < lower_bound) | (values > upper_bound)]
    print(f"\n🚨 Potential Outliers (IQR method):")
    print(f"   Count: {len(outliers):,} ({len(outliers)/len(values)*100:.1f}%)")
    print(f"   Range: [{lower_bound:.3f}, {upper_bound:.3f}]")
    
    if len(outliers) > 0:
        print(f"   Extreme values: {outliers.min():.3f} to {outliers.max():.3f}")
    
    return {
        'count': len(values),
        'mean': values.mean(),
        'median': values.median(),
        'std': values.std(),
        'min': values.min(),
        'max': values.max(),
        'outlier_count': len(outliers),
        'outlier_percentage': len(outliers)/len(values)*100 if len(values) > 0 else 0
    }

def analyze_categorical_columns(df, dataset_name):
    """Analyze categorical columns for unique values and potential issues."""
    categorical_cols = df.select_dtypes(include=['object']).columns
    
    print(f"\n🏷️ CATEGORICAL COLUMN ANALYSIS")
    print("-"*40)
    
    for col in categorical_cols:
        unique_count = df[col].nunique()
        print(f"\n📂 {col}:")
        print(f"   Unique values: {unique_count:,}")
        
        if unique_count <= 20:  # Show all values if not too many
            value_counts = df[col].value_counts()
            print(f"   Value distribution:")
            for val, count in value_counts.head(10).items():
                print(f"     '{val}': {count:,}")
            if len(value_counts) > 10:
                print(f"     ... and {len(value_counts) - 10} more")
        else:
            # Show top values
            value_counts = df[col].value_counts()
            print(f"   Top 5 values:")
            for val, count in value_counts.head(5).items():
                print(f"     '{val}': {count:,}")

def detect_duplicates(df, dataset_name):
    """Detect and analyze duplicate records."""
    print(f"\n🔍 DUPLICATE DETECTION")
    print("-"*40)
    
    # Check for complete duplicates
    total_duplicates = df.duplicated().sum()
    print(f"Complete duplicates: {total_duplicates:,} ({total_duplicates/len(df)*100:.1f}%)")
    
    # Check for duplicates based on administrative boundaries
    if all(col in df.columns for col in ['admin0_name', 'admin1_name', 'admin2_name']):
        admin_cols = ['admin0_name', 'admin1_name', 'admin2_name']
        admin_duplicates = df.duplicated(subset=admin_cols).sum()
        print(f"Admin boundary duplicates: {admin_duplicates:,} ({admin_duplicates/len(df)*100:.1f}%)")
        
        if admin_duplicates > 0:
            print(f"⚠️ Multiple records per sub-region detected!")
            
            # Show examples of duplicate admin boundaries
            duplicate_admins = df[df.duplicated(subset=admin_cols, keep=False)].sort_values(admin_cols)
            if len(duplicate_admins) > 0:
                print(f"\nExample duplicate sub-regions:")
                sample_duplicates = duplicate_admins.head(10)[admin_cols + (['variable'] if 'variable' in df.columns else []) + (['crop'] if 'crop' in df.columns else [])]
                print(sample_duplicates.to_string(index=False))

def analyze_geographic_coverage(df, dataset_name):
    """Analyze geographic coverage and potential gaps."""
    if not all(col in df.columns for col in ['admin0_name', 'admin1_name', 'admin2_name']):
        print(f"⚠️ Cannot analyze geographic coverage - missing admin columns")
        return
    
    print(f"\n🌍 GEOGRAPHIC COVERAGE ANALYSIS")
    print("-"*40)
    
    # Country-level analysis
    countries = df['admin0_name'].unique()
    print(f"Countries covered: {len(countries)}")
    
    # Sub-Saharan Africa countries (rough list for validation)
    ssa_countries = {
        'Angola', 'Benin', 'Botswana', 'Burkina Faso', 'Burundi', 'Cameroon', 'Cape Verde',
        'Central African Republic', 'Chad', 'Comoros', 'Democratic Republic of the Congo',
        'Republic of the Congo', 'Cote d\'Ivoire', 'Djibouti', 'Equatorial Guinea', 'Eritrea',
        'Eswatini', 'Ethiopia', 'Gabon', 'Gambia', 'Ghana', 'Guinea', 'Guinea-Bissau',
        'Kenya', 'Lesotho', 'Liberia', 'Madagascar', 'Malawi', 'Mali', 'Mauritania',
        'Mauritius', 'Mozambique', 'Namibia', 'Niger', 'Nigeria', 'Rwanda', 'Sao Tome and Principe',
        'Senegal', 'Seychelles', 'Sierra Leone', 'Somalia', 'South Africa', 'South Sudan',
        'Sudan', 'Tanzania', 'Togo', 'Uganda', 'Zambia', 'Zimbabwe'
    }
    
    ssa_in_data = set(countries) & ssa_countries
    non_ssa_in_data = set(countries) - ssa_countries
    
    print(f"SSA countries in data: {len(ssa_in_data)}")
    print(f"Non-SSA countries in data: {len(non_ssa_in_data)}")
    
    if non_ssa_in_data:
        print(f"Non-SSA countries: {sorted(non_ssa_in_data)}")
    
    # Records per country
    country_counts = df['admin0_name'].value_counts()
    print(f"\nRecords per country (top 10):")
    for country, count in country_counts.head(10).items():
        print(f"  {country}: {count:,}")

def create_summary_report(all_stats, output_path):
    """Create a summary report of all dataset analyses."""
    print(f"\n📋 COMPREHENSIVE SUMMARY REPORT")
    print("="*60)
    
    total_records = sum(stats['shape'][0] for stats in all_stats.values())
    total_countries = max(stats['countries'] for stats in all_stats.values())
    
    print(f"🌍 Overall Statistics:")
    print(f"   Total records across all datasets: {total_records:,}")
    print(f"   Maximum countries covered: {total_countries}")
    
    print(f"\n📊 Dataset Comparison:")
    print(f"{'Dataset':<15} {'Records':<10} {'Countries':<10} {'Missing %':<10}")
    print("-" * 50)
    
    for name, stats in all_stats.items():
        missing_pct = sum(stats['missing_values'].values()) / (stats['shape'][0] * stats['shape'][1]) * 100
        print(f"{name:<15} {stats['shape'][0]:<10,} {stats['countries']:<10} {missing_pct:<10.1f}")
    
    # Save summary to file
    with open(output_path, 'w') as f:
        f.write("ATLAS DATASETS QUALITY ASSESSMENT SUMMARY\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Analysis Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for name, stats in all_stats.items():
            f.write(f"{name.upper()} DATASET\n")
            f.write("-" * 30 + "\n")
            f.write(f"Records: {stats['shape'][0]:,}\n")
            f.write(f"Columns: {stats['shape'][1]}\n")
            f.write(f"Countries: {stats['countries']}\n")
            f.write(f"Missing values: {sum(stats['missing_values'].values()):,}\n\n")

def main():
    """Main analysis function."""
    config = Config()
    RAW_DATA_PATH = config.RAW_DATA_PATH
    PROCESSED_DATA_PATH = config.PROCESSED_DATA_PATH
    
    print("🔍 ATLAS DATASETS COMPREHENSIVE ANALYSIS")
    print("="*60)
    print("📋 Analyzing individual datasets before fusion")
    print("🎯 Goal: Identify data quality issues and anomalies")
    print("="*60)
    
    # Define datasets to analyze
    datasets = {
        'hazard': RAW_DATA_PATH / "atlas_hazard_ndws_future.csv",
        'poverty': RAW_DATA_PATH / "atlas_adaptive_capacity_poverty.csv",
        'population': RAW_DATA_PATH / "atlas_exposure_population.csv",
        'vop_crops': RAW_DATA_PATH / "atlas_exposure_vop_crops.csv"
    }
    
    all_stats = {}
    
    # Analyze each dataset
    for name, filepath in datasets.items():
        if not filepath.exists():
            print(f"❌ File not found: {filepath}")
            continue
        
        print(f"\n" + "="*80)
        print(f"ANALYZING: {name.upper()}")
        print("="*80)
        
        # Load dataset
        try:
            df = pd.read_csv(filepath)
            print(f"✅ Successfully loaded {name} dataset")
        except Exception as e:
            print(f"❌ Error loading {name}: {e}")
            continue
        
        # Perform analyses
        stats = analyze_dataset_structure(df, name)
        analyze_value_distribution(df, name, 'value')
        analyze_categorical_columns(df, name)
        detect_duplicates(df, name)
        analyze_geographic_coverage(df, name)
        
        all_stats[name] = stats
    
    # Create summary report
    summary_path = PROCESSED_DATA_PATH / "atlas_data_quality_report.txt"
    create_summary_report(all_stats, summary_path)
    
    print(f"\n✅ ANALYSIS COMPLETE!")
    print(f"📁 Summary report saved to: {summary_path}")
    print(f"\n🔄 NEXT STEPS:")
    print("1. Review the analysis results above")
    print("2. Address any data quality issues if needed")
    print("3. Run: python src/analysis/1_fuse_atlas_data.py")

if __name__ == "__main__":
    main()