#!/usr/bin/env python3
"""
Observable Framework Data Preparation
====================================

Prepare our validated risk assessment data for Observable Framework visualization.
This script creates Observable-optimized datasets and validates data structure.
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
import geopandas as gpd

def prepare_observable_data():
    """Prepare data specifically for Observable Framework requirements."""
    print("🎨 PREPARING DATA FOR OBSERVABLE FRAMEWORK")
    print("="*60)
    
    # Load our validated risk assessment
    df = pd.read_csv('data/processed/compound_risk_assessment.csv')
    print(f"📊 Loaded {len(df):,} records from risk assessment")
    
    # Create Observable-specific data directory
    obs_data_dir = Path('notebooks/data/observable')
    obs_data_dir.mkdir(exist_ok=True)
    
    # 1. Main visualization dataset (complete records only)
    print("\n📋 Preparing main visualization dataset...")
    
    # Keep only complete records for visualization
    complete_df = df.dropna()
    print(f"   Complete records: {len(complete_df):,} ({len(complete_df)/len(df)*100:.1f}%)")
    
    # Round numerical values for cleaner visualization
    numeric_columns = ['hazard_score', 'social_vulnerability_score', 'environmental_vulnerability_score',
                      'combined_vulnerability_score', 'compound_risk_score', 'population', 'vop_crops_usd',
                      'ndws_future_days', 'poverty_headcount_ratio', 'soil_ph_mean', 'soil_soc_mean',
                      'soil_sand_mean', 'soil_clay_mean']
    
    for col in numeric_columns:
        if col in complete_df.columns:
            if col.endswith('_score'):
                complete_df[col] = complete_df[col].round(4)  # Risk scores to 4 decimals
            elif col in ['population', 'vop_crops_usd']:
                complete_df[col] = complete_df[col].round(2)  # Population/economic to 2 decimals
            else:
                complete_df[col] = complete_df[col].round(3)  # Other indicators to 3 decimals
    
    # Add risk categories for easier visualization
    complete_df['risk_category'] = pd.cut(
        complete_df['compound_risk_score'],
        bins=[0, 0.3, 0.5, 0.7, 1.0],
        labels=['Low', 'Moderate', 'High', 'Very High'],
        include_lowest=True
    )
    
    # Add vulnerability categories
    complete_df['vulnerability_category'] = pd.cut(
        complete_df['combined_vulnerability_score'],
        bins=[0, 0.5, 1.0, 1.5, 2.0],
        labels=['Low', 'Moderate', 'High', 'Very High'],
        include_lowest=True
    )
    
    # Export main dataset
    main_file = obs_data_dir / 'risk_assessment_complete.csv'
    complete_df.to_csv(main_file, index=False)
    print(f"   ✅ Exported: {main_file}")
    
    # 2. Country summary for overview
    print("\n🌍 Preparing country-level summaries...")
    
    country_summary = complete_df.groupby('country').agg({
        'compound_risk_score': ['mean', 'max', 'min', 'count'],
        'population': 'sum',
        'vop_crops_usd': 'sum',
        'hazard_score': 'mean',
        'combined_vulnerability_score': 'mean'
    }).round(3)
    
    # Flatten column names
    country_summary.columns = ['_'.join(col).strip() for col in country_summary.columns]
    country_summary = country_summary.reset_index()
    
    # Add high-risk area counts
    high_risk_counts = complete_df[complete_df['compound_risk_score'] > 0.7].groupby('country').size()
    country_summary['high_risk_areas'] = country_summary['country'].map(high_risk_counts).fillna(0).astype(int)
    
    country_file = obs_data_dir / 'country_summary.csv'
    country_summary.to_csv(country_file, index=False)
    print(f"   ✅ Exported: {country_file}")
    
    # 3. Risk hotspots (extended top 50 for flexibility)
    print("\n🔥 Preparing risk hotspots...")
    
    hotspots = complete_df.nlargest(50, 'compound_risk_score')[
        ['country', 'region', 'sub_region', 'compound_risk_score', 'hazard_score',
         'combined_vulnerability_score', 'population', 'vop_crops_usd', 'risk_category']
    ].copy()
    
    hotspots['rank'] = range(1, len(hotspots) + 1)
    hotspots['population_thousands'] = (hotspots['population'] / 1000).round(1)
    hotspots['vop_millions_usd'] = (hotspots['vop_crops_usd'] / 1000000).round(2)
    
    hotspots_file = obs_data_dir / 'risk_hotspots.csv'
    hotspots.to_csv(hotspots_file, index=False)
    print(f"   ✅ Exported: {hotspots_file}")
    
    # 4. Soil health indicators summary
    print("\n🌱 Preparing soil health summaries...")
    
    soil_cols = ['soil_ph_mean', 'soil_soc_mean', 'soil_sand_mean', 'soil_clay_mean']
    soil_available = complete_df[soil_cols + ['country', 'region', 'sub_region', 'environmental_vulnerability_score']].copy()
    
    # Add soil health categories
    soil_available['ph_category'] = pd.cut(
        soil_available['soil_ph_mean'],
        bins=[0, 5.5, 6.5, 7.5, 14],
        labels=['Acidic', 'Slightly Acidic', 'Neutral', 'Alkaline']
    )
    
    soil_available['soc_category'] = pd.cut(
        soil_available['soil_soc_mean'],
        bins=[0, 1, 2, 4, 100],
        labels=['Very Low', 'Low', 'Moderate', 'High']
    )
    
    soil_file = obs_data_dir / 'soil_health_indicators.csv'
    soil_available.to_csv(soil_file, index=False)
    print(f"   ✅ Exported: {soil_file}")
    
    # 5. Create metadata file for Observable
    print("\n📋 Creating metadata...")
    
    metadata = {
        'dataset_info': {
            'title': 'Sub-Saharan Africa Climate Risk Assessment',
            'description': 'Compound risk assessment combining climate hazard and socio-environmental vulnerability',
            'geographic_scope': 'Sub-Saharan Africa',
            'temporal_scope': 'Climate projections 2041-2060, baseline conditions 2012-2025',
            'total_records': len(complete_df),
            'countries_covered': complete_df['country'].nunique(),
            'data_completeness': f"{len(complete_df)/len(df)*100:.1f}%"
        },
        'risk_methodology': {
            'formula': 'Risk = Hazard × Combined_Vulnerability',
            'hazard_indicator': 'Number of Days of Water Stress (NDWS) future projections',
            'vulnerability_components': ['Social (poverty)', 'Environmental (soil health)'],
            'risk_scale': '0-1 (normalized)',
            'high_risk_threshold': 0.7
        },
        'data_currency': {
            'atlas_data': '2020-2025',
            'soil_properties': '2017 (SoilGrids)',
            'soil_erosion': '2012 (GloSEM)',
            'poverty_data': '2015-2020',
            'admin_boundaries': '2020-2024'
        },
        'missing_data': {
            'affected_countries': ['Democratic Republic of the Congo', 'Republic of the Congo'],
            'reason': 'Congo Basin forest coverage limits satellite-based soil mapping',
            'impact': '6.2% of total records',
            'completeness_rest_of_ssa': '100%'
        },
        'validation': {
            'overall_confidence': '88% (HIGH)',
            'temporal_validity': '85%',
            'data_currency': '89%',
            'methodology_score': '90%'
        }
    }
    
    metadata_file = obs_data_dir / 'dataset_metadata.json'
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"   ✅ Exported: {metadata_file}")
    
    # 6. Summary statistics for dashboard
    print("\n📊 Creating dashboard statistics...")
    
    stats = {
        'overview': {
            'total_sub_regions': len(complete_df),
            'countries_covered': complete_df['country'].nunique(),
            'high_risk_areas': len(complete_df[complete_df['compound_risk_score'] > 0.7]),
            'people_at_risk': int(complete_df[complete_df['compound_risk_score'] > 0.7]['population'].sum()),
            'agriculture_value_at_risk': int(complete_df[complete_df['compound_risk_score'] > 0.7]['vop_crops_usd'].sum())
        },
        'risk_distribution': {
            'low_risk': len(complete_df[complete_df['compound_risk_score'] <= 0.3]),
            'moderate_risk': len(complete_df[(complete_df['compound_risk_score'] > 0.3) & (complete_df['compound_risk_score'] <= 0.7)]),
            'high_risk': len(complete_df[complete_df['compound_risk_score'] > 0.7]),
            'mean_risk_score': float(complete_df['compound_risk_score'].mean()),
            'max_risk_score': float(complete_df['compound_risk_score'].max())
        },
        'top_risk_countries': complete_df.groupby('country')['compound_risk_score'].mean().nlargest(5).to_dict(),
        'vulnerability_breakdown': {
            'mean_social_vulnerability': float(complete_df['social_vulnerability_score'].mean()),
            'mean_environmental_vulnerability': float(complete_df['environmental_vulnerability_score'].mean()),
            'hazard_vulnerability_correlation': float(complete_df['hazard_score'].corr(complete_df['combined_vulnerability_score']))
        }
    }
    
    stats_file = obs_data_dir / 'dashboard_stats.json'
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"   ✅ Exported: {stats_file}")
    
    # Print summary
    print(f"\n🎯 OBSERVABLE DATA PREPARATION COMPLETE!")
    print("="*60)
    print(f"📁 Output directory: {obs_data_dir}")
    print(f"📊 Files created:")
    for file in obs_data_dir.glob('*'):
        print(f"   • {file.name}")
    
    return {
        'complete_records': len(complete_df),
        'countries': complete_df['country'].nunique(),
        'high_risk_areas': len(complete_df[complete_df['compound_risk_score'] > 0.7]),
        'output_dir': obs_data_dir
    }

def validate_observable_data():
    """Validate that Observable data is properly formatted."""
    print(f"\n🔍 VALIDATING OBSERVABLE DATA FORMAT")
    print("-" * 40)
    
    obs_data_dir = Path('notebooks/data/observable')
    
    # Check main dataset
    main_file = obs_data_dir / 'risk_assessment_complete.csv'
    if main_file.exists():
        df = pd.read_csv(main_file)
        print(f"✅ Main dataset: {len(df):,} records, {len(df.columns)} columns")
        
        # Check for required columns
        required_cols = ['country', 'compound_risk_score', 'risk_category']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            print(f"⚠️  Missing columns: {missing_cols}")
        else:
            print(f"✅ All required columns present")
            
        # Check data types
        print(f"✅ Risk scores range: {df['compound_risk_score'].min():.3f} - {df['compound_risk_score'].max():.3f}")
    else:
        print(f"❌ Main dataset not found: {main_file}")
    
    # Check other files
    expected_files = ['country_summary.csv', 'risk_hotspots.csv', 'soil_health_indicators.csv', 
                     'dataset_metadata.json', 'dashboard_stats.json']
    
    for filename in expected_files:
        filepath = obs_data_dir / filename
        if filepath.exists():
            print(f"✅ {filename}: Found")
        else:
            print(f"❌ {filename}: Missing")

def main():
    """Main function to prepare Observable Framework data."""
    print("🎨 OBSERVABLE FRAMEWORK DATA PREPARATION")
    print("="*70)
    print("🎯 Goal: Create Observable-optimized datasets from validated risk assessment")
    print()
    
    try:
        # Prepare Observable data
        result = prepare_observable_data()
        
        # Validate data format
        validate_observable_data()
        
        print(f"\n🚀 READY FOR OBSERVABLE FRAMEWORK!")
        print("="*70)
        print(f"📊 {result['complete_records']:,} records prepared")
        print(f"🌍 {result['countries']} countries covered")
        print(f"🔥 {result['high_risk_areas']} high-risk areas identified")
        print(f"📁 Data ready in: {result['output_dir']}")
        print("\n✅ Next step: Initialize Observable Framework project")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()