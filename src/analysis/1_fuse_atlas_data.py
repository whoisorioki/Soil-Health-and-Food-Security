#!/usr/bin/env python3
"""
Step 1: Fuse Atlas Socio-Economic Data
=====================================

This script loads and merges the four core Atlas Explorer datasets:
1. Hazard: Number of Days of Water Stress (NDWS) future projections
2. Exposure: Agricultural Value of Production + Population data  
3. Adaptive Capacity: Poverty headcount ratios

Creates the foundational dataset for Risk = Hazard × Vulnerability analysis.
"""

import pandas as pd
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from config import Config

def fuse_atlas_socioeconomic_data():
    """
    Loads, cleans, and merges the four core socio-economic datasets from the Atlas Explorer.
    This creates the foundational data frame for our analysis.
    """
    config = Config()
    config.ensure_directories()
    
    print("🌍 STEP 1: FUSING ATLAS SOCIO-ECONOMIC DATA")
    print("="*60)
    print("📊 Atlas Explorer → Risk Assessment Pipeline")
    print("🎯 Goal: Create master dataset for Risk = Hazard × Vulnerability")
    print("="*60)

    # File paths for the four exported CSVs from the Atlas Explorer
    RAW_DATA_PATH = config.RAW_DATA_PATH
    PROCESSED_DATA_PATH = config.PROCESSED_DATA_PATH
    
    HAZARD_FILE = RAW_DATA_PATH / "atlas_hazard_ndws_future.csv"
    VOP_FILE = RAW_DATA_PATH / "atlas_exposure_vop_crops.csv"
    POP_FILE = RAW_DATA_PATH / "atlas_exposure_population.csv"
    POVERTY_FILE = RAW_DATA_PATH / "atlas_adaptive_capacity_poverty.csv"

    # --- 1. Load Datasets ---
    print("\n📂 Loading Atlas Explorer datasets...")
    try:
        hazard_df = pd.read_csv(HAZARD_FILE)
        vop_df = pd.read_csv(VOP_FILE)
        pop_df = pd.read_csv(POP_FILE)
        poverty_df = pd.read_csv(POVERTY_FILE)
        print("✅ All 4 Atlas datasets loaded successfully")
        
        # Display dataset sizes
        print(f"   📊 Hazard (NDWS): {len(hazard_df):,} sub-regions")
        print(f"   🌾 VOP Crops: {len(vop_df):,} sub-regions") 
        print(f"   👥 Population: {len(pop_df):,} sub-regions")
        print(f"   💰 Poverty: {len(poverty_df):,} sub-regions")
        
    except FileNotFoundError as e:
        print(f"❌ ERROR: Missing Atlas data file")
        print(f"   File not found: {e.filename}")
        print(f"   Please ensure all 4 CSV files are downloaded from Atlas Explorer")
        return None

    # --- 2. Data Quality Check ---
    print("\n🔍 Performing data quality checks...")
    
    # Check for required columns - Atlas uses admin0_name, admin1_name, admin2_name
    atlas_cols = ['admin0_name', 'admin1_name', 'admin2_name', 'value']
    for name, df in [("Hazard", hazard_df), ("VOP", vop_df), ("Population", pop_df), ("Poverty", poverty_df)]:
        missing_cols = [col for col in atlas_cols if col not in df.columns]
        if missing_cols:
            print(f"❌ ERROR: {name} dataset missing columns: {missing_cols}")
            print(f"   Available columns: {list(df.columns)}")
            return None
    
    print("✅ All datasets have required Atlas columns")

    # --- 3. Standardize Column Names ---
    print("\n🏷️ Standardizing administrative boundary column names...")
    
    # Rename admin columns to consistent format
    column_mapping = {
        'admin0_name': 'country',
        'admin1_name': 'region', 
        'admin2_name': 'sub_region'
    }
    
    hazard_df = hazard_df.rename(columns=column_mapping)
    vop_df = vop_df.rename(columns=column_mapping)
    pop_df = pop_df.rename(columns=column_mapping) 
    poverty_df = poverty_df.rename(columns=column_mapping)

    # --- 4. Filter and Prepare Datasets ---
    print("\n🔧 Filtering and preparing datasets...")
    print("   📊 Based on data exploration findings:")
    
    # Hazard: Filter to SSP245 scenario (moderate climate change scenario)
    print("   🌡️ Filtering hazard data: Using SSP245 scenario (moderate climate projection)")
    hazard_filtered = hazard_df[hazard_df['scenario'] == 'ssp245'].copy()
    print(f"      Hazard data: {len(hazard_filtered):,} sub-regions (filtered from {len(hazard_df):,})")
    
    # Poverty: Use the $3.65/day poverty line (GSAP_poor365) as the standard indicator
    print("   💰 Filtering poverty data: Using $3.65/day poverty line (GSAP_poor365)")
    poverty_filtered = poverty_df[poverty_df['variable'] == 'GSAP_poor365'].copy()
    print(f"      Poverty data: {len(poverty_filtered):,} sub-regions (filtered from {len(poverty_df):,})")
    
    # Population: Use total population instead of rural population
    print("   👥 Filtering population data: Using total population")
    population_filtered = pop_df[pop_df['crop'] == 'total_pop'].copy()
    print(f"      Population data: {len(population_filtered):,} sub-regions (filtered from {len(pop_df):,})")
    
    # VOP: Sum all crop values per sub-region to get total agricultural value
    print("   🌾 Aggregating crop values: Summing VOP (Value of Production) across all crops per sub-region")
    # Filter to VOP values only (not hectares)
    vop_values = vop_df[vop_df['exposure'] == 'vop'].copy()
    vop_filtered = vop_values.groupby(['country', 'region', 'sub_region'], as_index=False)['value'].sum()
    vop_filtered.columns = ['country', 'region', 'sub_region', 'vop_crops_usd']
    print(f"      VOP data: {len(vop_filtered):,} sub-regions (aggregated from {len(vop_values):,} crop records)")

    # --- 5. Rename Value Columns for Clarity ---
    print("\n🏷️ Renaming value columns for clarity...")
    hazard_filtered = hazard_filtered.rename(columns={'value': 'ndws_future_days'})
    population_filtered = population_filtered.rename(columns={'value': 'population'})
    poverty_filtered = poverty_filtered.rename(columns={'value': 'poverty_headcount_ratio'})

    # --- 6. Merge into a Master DataFrame ---
    merge_cols = ['country', 'region', 'sub_region']
    print(f"\n🔗 Merging datasets on administrative boundaries: {merge_cols}")
    
    # Start with the core risk components: Hazard and Adaptive Capacity (Poverty)
    print("   1️⃣ Merging Hazard (NDWS) + Adaptive Capacity (Poverty)...")
    master_df = pd.merge(
        hazard_filtered[merge_cols + ['ndws_future_days']], 
        poverty_filtered[merge_cols + ['poverty_headcount_ratio']], 
        on=merge_cols, 
        how='inner'  # Inner join to ensure we have both hazard and vulnerability data
    )
    print(f"      Core dataset: {len(master_df):,} sub-regions with both hazard and poverty data")
    
    # Add the exposure layers (use left join to preserve core risk data)
    print("   2️⃣ Adding Exposure: Agricultural Value of Production...")
    master_df = pd.merge(master_df, vop_filtered[merge_cols + ['vop_crops_usd']], on=merge_cols, how='left')
    vop_coverage = master_df['vop_crops_usd'].notna().sum()
    print(f"      VOP coverage: {vop_coverage:,}/{len(master_df):,} sub-regions ({vop_coverage/len(master_df)*100:.1f}%)")
    
    print("   3️⃣ Adding Exposure: Population...")
    master_df = pd.merge(master_df, population_filtered[merge_cols + ['population']], on=merge_cols, how='left')
    pop_coverage = master_df['population'].notna().sum()
    print(f"      Population coverage: {pop_coverage:,}/{len(master_df):,} sub-regions ({pop_coverage/len(master_df)*100:.1f}%)")

    # --- 7. Calculate Intermediate Risk Scores ---
    print("\n📊 Calculating intermediate risk scores...")
    print("   🌡️ Hazard Score: NDWS future days (normalized 0-1, where 1 = more water stress)")
    master_df['hazard_score'] = master_df['ndws_future_days'] / master_df['ndws_future_days'].max()
    
    print("   💔 Social Vulnerability Score: Poverty headcount ratio (normalized 0-1, where 1 = more poverty)")
    master_df['social_vulnerability_score'] = master_df['poverty_headcount_ratio'] / master_df['poverty_headcount_ratio'].max()
    
    # Add preliminary risk score (will be enhanced with soil data in Step 2)
    print("   ⚡ Preliminary Risk Score: Hazard × Social Vulnerability")
    master_df['preliminary_risk_score'] = master_df['hazard_score'] * master_df['social_vulnerability_score']

    # --- 8. Summary Statistics ---
    print("\n📈 DATASET SUMMARY")
    print("="*40)
    print(f"Total sub-regions: {len(master_df):,}")
    print(f"Countries covered: {master_df['country'].nunique()}")
    print(f"Regions covered: {master_df['region'].nunique()}")
    
    print(f"\nHazard (NDWS future days):")
    print(f"  Min: {master_df['ndws_future_days'].min():.1f} days")
    print(f"  Max: {master_df['ndws_future_days'].max():.1f} days") 
    print(f"  Mean: {master_df['ndws_future_days'].mean():.1f} days")
    
    print(f"\nPoverty (headcount ratio):")
    print(f"  Min: {master_df['poverty_headcount_ratio'].min():.1f}%")
    print(f"  Max: {master_df['poverty_headcount_ratio'].max():.1f}%")
    print(f"  Mean: {master_df['poverty_headcount_ratio'].mean():.1f}%")

    # --- 9. Identify Top Risk Areas (Preview) ---
    print(f"\n🔥 TOP 10 PRELIMINARY RISK HOTSPOTS")
    print("="*50)
    print("(Based on Climate Hazard × Social Vulnerability only)")
    
    top_risk = master_df.nlargest(10, 'preliminary_risk_score')[
        ['country', 'sub_region', 'ndws_future_days', 'poverty_headcount_ratio', 'preliminary_risk_score']
    ]
    
    for idx, (i, row) in enumerate(top_risk.iterrows(), 1):
        print(f"{idx:2d}. {row['country']}, {row['sub_region']}")
        print(f"    💧 Water stress: {row['ndws_future_days']:.0f} days/year")
        print(f"    💰 Poverty rate: {row['poverty_headcount_ratio']:.1f}%")
        print(f"    ⚡ Risk score: {row['preliminary_risk_score']:.3f}")

    # --- 10. Save Processed Data ---
    output_path = PROCESSED_DATA_PATH / "master_atlas_data.csv"
    master_df.to_csv(output_path, index=False)
    
    print(f"\n✅ FUSION COMPLETE!")
    print(f"📁 Master dataset saved: {output_path}")
    print(f"📊 Ready for Step 2: Geospatial processing with soil data")
    print("\n🌱 NEXT STEPS:")
    print("1. Complete SoilGrids data download (see manual instructions)")
    print("2. Run: python src/analysis/2_process_geospatial_data.py")
    
    return master_df

if __name__ == "__main__":
    result = fuse_atlas_socioeconomic_data()
    if result is not None:
        print("\n🎯 Step 1 completed successfully!")
    else:
        print("\n❌ Step 1 failed. Please fix errors and retry.")