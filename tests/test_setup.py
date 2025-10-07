#!/usr/bin/env python3
"""
Test script to verify the Soil Health and Food Security project setup.
This script tests the environment without requiring any API keys.
"""

import sys
import os
from pathlib import Path
import traceback

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_imports():
    """Test that all core modules can be imported."""
    print("🧪 Testing module imports...")
    
    try:
        # Test core scientific libraries
        import numpy as np
        import pandas as pd
        import geopandas as gpd
        import xarray as xr
        import matplotlib.pyplot as plt
        print("✅ Core scientific libraries: OK")
        
        # Test geospatial libraries
        import rasterio
        import fiona
        from shapely.geometry import Point
        print("✅ Geospatial libraries: OK")
        
        # Test project modules
        from config import Config
        from analysis.soil_health_analysis import SoilHealthAnalyzer
        from data_processing.download_datasets import DataDownloader
        print("✅ Project modules: OK")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_configuration():
    """Test that configuration is working."""
    print("\n⚙️  Testing configuration...")
    
    try:
        from config import Config, SSA_COUNTRIES, DATA_SOURCES
        
        config = Config()
        print(f"✅ Project root: {config.PROJECT_ROOT}")
        print(f"✅ Data root: {config.DATA_ROOT}")
        print(f"✅ Default CRS: {config.DEFAULT_CRS}")
        print(f"✅ SSA countries: {len(SSA_COUNTRIES)} countries")
        print(f"✅ Data sources: {len(DATA_SOURCES)} sources configured")
        
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_data_directories():
    """Test that data directories exist."""
    print("\n📁 Testing data directories...")
    
    try:
        from config import Config
        config = Config()
        
        directories = [
            config.DATA_ROOT,
            config.RAW_DATA_PATH,
            config.PROCESSED_DATA_PATH,
            config.CACHE_PATH
        ]
        
        for directory in directories:
            if directory.exists():
                print(f"✅ {directory.name}: exists")
            else:
                print(f"❌ {directory.name}: missing")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Directory test error: {e}")
        return False

def test_analysis_workflow():
    """Test basic analysis workflow with sample data."""
    print("\n🔬 Testing analysis workflow...")
    
    try:
        import numpy as np
        import xarray as xr
        from analysis.soil_health_analysis import SoilHealthAnalyzer
        
        # Create sample data
        sample_ph = xr.DataArray(
            np.random.uniform(4.0, 8.0, (10, 10)),
            dims=['y', 'x'],
            coords={'y': range(10), 'x': range(10)}
        )
        
        # Test analysis
        analyzer = SoilHealthAnalyzer()
        ph_risk = analyzer.classify_soil_ph(sample_ph)
        
        print(f"✅ Sample pH data shape: {sample_ph.shape}")
        print(f"✅ pH risk analysis: min={ph_risk.min().values:.3f}, max={ph_risk.max().values:.3f}")
        print("✅ Analysis workflow: OK")
        
        return True
    except Exception as e:
        print(f"❌ Analysis workflow error: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Soil Health and Food Security Project - Setup Test")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_configuration, 
        test_data_directories,
        test_analysis_workflow
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print(f"✅ Passed: {sum(results)}/{len(results)}")
    print(f"❌ Failed: {len(results) - sum(results)}/{len(results)}")
    
    if all(results):
        print("\n🎉 All tests passed! Your environment is ready for development.")
        print("\nNext steps:")
        print("1. Start Jupyter Lab: jupyter lab")
        print("2. Open: notebooks/soil_health_analysis_starter.ipynb")
        print("3. Begin data download: python src/data_processing/download_datasets.py")
    else:
        print("\n⚠️  Some tests failed. Please check the error messages above.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())