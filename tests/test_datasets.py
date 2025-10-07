"""
Test script to validate all downloaded datasets and check data structure
"""

import os
import sys
from pathlib import Path
import xarray as xr
import pandas as pd
import json

# Add src to path for imports
src_path = Path(__file__).parent / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from config import Config

def test_all_datasets():
    """Test and validate all downloaded datasets."""
    config = Config()
    
    print("🔍 TESTING ALL DOWNLOADED DATASETS")
    print("="*50)
    
    # Check data structure
    raw_data_path = config.RAW_DATA_PATH
    
    datasets_found = {
        'climate': 0,
        'soil_properties': 0,
        'soil_erosion': 0,
        'crops': 0,
        'livestock': 0
    }
    
    # 1. Climate data (ISIMIP)
    climate_path = raw_data_path / 'climate' / 'isimip'
    if climate_path.exists():
        climate_files = list(climate_path.glob('*.nc'))
        datasets_found['climate'] = len(climate_files)
        print(f"✅ Climate (ISIMIP): {len(climate_files)} datasets")
        
        # Test one file
        if climate_files:
            try:
                ds = xr.open_dataset(climate_files[0])
                print(f"   📊 Sample climate data shape: {dict(ds.dims)}")
                print(f"   📊 Variables: {list(ds.data_vars.keys())}")
                ds.close()
            except Exception as e:
                print(f"   ❌ Error reading climate data: {e}")
    else:
        print("❌ Climate data not found")
    
    # 2. Soil properties (SoilGrids)
    soil_path = raw_data_path / 'soil' / 'soilgrids'
    if soil_path.exists():
        soil_files = list(soil_path.glob('*.nc'))
        datasets_found['soil_properties'] = len(soil_files)
        print(f"✅ Soil Properties (SoilGrids): {len(soil_files)} datasets")
        
        # Test one file
        if soil_files:
            try:
                ds = xr.open_dataset(soil_files[0])
                print(f"   📊 Sample soil data shape: {dict(ds.dims)}")
                print(f"   📊 Variables: {list(ds.data_vars.keys())}")
                ds.close()
            except Exception as e:
                print(f"   ❌ Error reading soil data: {e}")
    else:
        print("❌ Soil properties data not found")
    
    # 3. Soil erosion (GloSEM)
    erosion_path = raw_data_path / 'soil' / 'erosion' / 'glosem'
    if erosion_path.exists():
        erosion_files = list(erosion_path.glob('*.nc'))
        datasets_found['soil_erosion'] = len(erosion_files)
        print(f"✅ Soil Erosion (GloSEM): {len(erosion_files)} datasets")
        
        # Test one file
        if erosion_files:
            try:
                ds = xr.open_dataset(erosion_files[0])
                print(f"   📊 Sample erosion data shape: {dict(ds.dims)}")
                print(f"   📊 Variables: {list(ds.data_vars.keys())}")
                ds.close()
            except Exception as e:
                print(f"   ❌ Error reading erosion data: {e}")
    else:
        print("❌ Soil erosion data not found")
    
    # 4. Crop data (MapSPAM)
    crop_path = raw_data_path / 'agriculture' / 'mapspam'
    if crop_path.exists():
        crop_files = list(crop_path.glob('*.nc'))
        datasets_found['crops'] = len(crop_files)
        print(f"⚠️ Crop Data (MapSPAM): {len(crop_files)} datasets (some failed)")
    else:
        print("❌ Crop data not found")
    
    # 5. Livestock data (GLW)
    livestock_path = raw_data_path / 'agriculture' / 'livestock' / 'glw'
    if livestock_path.exists():
        livestock_files = list(livestock_path.glob('*.nc'))
        datasets_found['livestock'] = len(livestock_files)
        print(f"✅ Livestock (GLW): {len(livestock_files)} datasets")
        
        # Test one file
        if livestock_files:
            try:
                ds = xr.open_dataset(livestock_files[0])
                print(f"   📊 Sample livestock data shape: {dict(ds.dims)}")
                print(f"   📊 Variables: {list(ds.data_vars.keys())}")
                ds.close()
            except Exception as e:
                print(f"   ❌ Error reading livestock data: {e}")
    else:
        print("❌ Livestock data not found")
    
    # Summary
    print("\n" + "="*50)
    print("📊 DATASET SUMMARY")
    print("="*50)
    
    total_datasets = sum(datasets_found.values())
    print(f"Total datasets downloaded: {total_datasets}")
    
    for category, count in datasets_found.items():
        status = "✅" if count > 0 else "❌"
        print(f"{status} {category.replace('_', ' ').title()}: {count} files")
    
    # Data coverage assessment
    print("\n🎯 DATA COVERAGE FOR ANALYSIS:")
    
    required_for_analysis = {
        'Climate projections': datasets_found['climate'] >= 5,
        'Soil health indicators': datasets_found['soil_properties'] >= 4,
        'Erosion assessment': datasets_found['soil_erosion'] >= 3,
        'Food production': datasets_found['crops'] >= 5 or datasets_found['livestock'] >= 2,
        'Livestock systems': datasets_found['livestock'] >= 2
    }
    
    for component, available in required_for_analysis.items():
        status = "✅" if available else "⚠️"
        print(f"{status} {component}: {'Available' if available else 'Limited'}")
    
    # Analysis readiness
    ready_components = sum(required_for_analysis.values())
    total_components = len(required_for_analysis)
    
    print(f"\n🚀 ANALYSIS READINESS: {ready_components}/{total_components} components ready")
    
    if ready_components >= 4:
        print("🎉 EXCELLENT! Ready for comprehensive analysis")
    elif ready_components >= 3:
        print("✅ GOOD! Most analysis components available")
    elif ready_components >= 2:
        print("⚠️ LIMITED! Some analysis possible but missing key data")
    else:
        print("❌ INSUFFICIENT! Need more data for meaningful analysis")
    
    return datasets_found, ready_components, total_components

if __name__ == "__main__":
    datasets, ready, total = test_all_datasets()
    
    # Return appropriate exit code
    if ready >= 3:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Need more data