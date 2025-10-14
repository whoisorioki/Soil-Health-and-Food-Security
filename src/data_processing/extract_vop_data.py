#!/usr/bin/env python3
"""
Atlas VOP Data Extractor
========================

This script extracts Value of Production (VOP) data from the combined 
atlas_exposure_ha_vop_crops.csv file and saves it as a clean atlas_exposure_vop_crops.csv.

The combined file contains both hectares (ha) and value of production (vop) data.
We need only the VOP data for our risk assessment analysis.

Author: Atlas Data Processing Pipeline
Date: October 2025
"""

import pandas as pd
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_vop_data():
    """Extract VOP data from combined exposure file"""
    
    logger.info("🚀 Starting VOP data extraction...")
    
    # File paths
    input_file = Path("data/raw/atlas_exposure_ha_vop_crops.csv")
    output_file = Path("data/raw/atlas_exposure_vop_crops.csv")
    
    # Check if input file exists
    if not input_file.exists():
        logger.error(f"❌ Input file not found: {input_file}")
        raise FileNotFoundError(f"Required file not found: {input_file}")
    
    # Load the combined data
    logger.info(f"📂 Loading combined exposure data from {input_file}")
    df_combined = pd.read_csv(input_file)
    logger.info(f"✅ Loaded {len(df_combined):,} total records")
    
    # Check exposure types
    exposure_types = df_combined['exposure'].unique()
    logger.info(f"📊 Exposure types found: {list(exposure_types)}")
    
    exposure_counts = df_combined['exposure'].value_counts()
    for exp_type, count in exposure_counts.items():
        logger.info(f"   {exp_type}: {count:,} records")
    
    # Filter for VOP data only
    logger.info("🔍 Filtering for VOP (Value of Production) data...")
    df_vop = df_combined[df_combined['exposure'] == 'vop'].copy()
    logger.info(f"✅ VOP data extracted: {len(df_vop):,} records")
    
    # Validate the filtered data
    logger.info("🔍 Validating VOP data structure...")
    
    # Check columns
    expected_columns = ['admin0_name', 'admin1_name', 'admin2_name', 'exposure', 'crop', 'value', 'group']
    missing_columns = set(expected_columns) - set(df_vop.columns)
    if missing_columns:
        logger.warning(f"⚠️ Missing expected columns: {missing_columns}")
    
    # Check for any non-VOP exposure types (should be none)
    non_vop_types = df_vop['exposure'].unique()
    if len(non_vop_types) != 1 or non_vop_types[0] != 'vop':
        logger.warning(f"⚠️ Unexpected exposure types in VOP data: {non_vop_types}")
    else:
        logger.info("✅ All records confirmed as VOP type")
    
    # Check geographic coverage
    countries = df_vop['admin0_name'].nunique()
    regions = df_vop[['admin0_name', 'admin1_name', 'admin2_name']].drop_duplicates()
    logger.info(f"🌍 Geographic coverage: {countries} countries, {len(regions):,} unique regions")
    
    # Check crop types
    crops = df_vop['crop'].nunique()
    logger.info(f"🌾 Crop coverage: {crops} different crop types")
    
    # Show sample of top crops by total value
    crop_totals = df_vop.groupby('crop')['value'].sum().sort_values(ascending=False)
    logger.info("📈 Top 10 crops by total VOP value:")
    for crop, total_value in crop_totals.head(10).items():
        logger.info(f"   {crop}: ${total_value:,.0f}")
    
    # Check for missing values
    missing_values = df_vop.isnull().sum()
    total_missing = missing_values.sum()
    if total_missing > 0:
        logger.info(f"⚠️ Missing values found:")
        for col, missing_count in missing_values.items():
            if missing_count > 0:
                logger.info(f"   {col}: {missing_count:,} missing ({missing_count/len(df_vop)*100:.1f}%)")
    else:
        logger.info("✅ No missing values found")
    
    # Save the VOP data
    logger.info(f"💾 Saving VOP data to {output_file}")
    df_vop.to_csv(output_file, index=False)
    logger.info(f"✅ VOP data saved successfully")
    
    # Verify the saved file
    logger.info("🔍 Verifying saved file...")
    df_verify = pd.read_csv(output_file)
    if len(df_verify) == len(df_vop):
        logger.info(f"✅ File verification successful: {len(df_verify):,} records")
    else:
        logger.error(f"❌ File verification failed: Expected {len(df_vop):,}, got {len(df_verify):,}")
    
    # Summary statistics
    logger.info("\n📊 EXTRACTION SUMMARY:")
    logger.info("=" * 40)
    logger.info(f"Input file: {input_file}")
    logger.info(f"Output file: {output_file}")
    logger.info(f"Total input records: {len(df_combined):,}")
    logger.info(f"VOP records extracted: {len(df_vop):,}")
    logger.info(f"Extraction rate: {len(df_vop)/len(df_combined)*100:.1f}%")
    logger.info(f"Countries covered: {countries}")
    logger.info(f"Administrative regions: {len(regions):,}")
    logger.info(f"Crop types: {crops}")
    logger.info(f"Total VOP value: ${df_vop['value'].sum():,.0f}")
    
    return df_vop

def main():
    """Main execution function"""
    
    try:
        # Extract VOP data
        vop_data = extract_vop_data()
        
        print("\n" + "="*60)
        print("VOP DATA EXTRACTION COMPLETE!")
        print("="*60)
        print(f"✅ Successfully extracted {len(vop_data):,} VOP records")
        print(f"📁 Saved to: data/raw/atlas_exposure_vop_crops.csv")
        print(f"🌍 Coverage: {vop_data['admin0_name'].nunique()} countries")
        print(f"🌾 Crops: {vop_data['crop'].nunique()} types")
        print(f"💰 Total Value: ${vop_data['value'].sum():,.0f}")
        print("\n✅ Ready for Atlas fusion analysis!")
        
    except Exception as e:
        logger.error(f"❌ VOP extraction failed: {str(e)}")
        print(f"\n❌ ERROR: {str(e)}")
        raise

if __name__ == "__main__":
    main()