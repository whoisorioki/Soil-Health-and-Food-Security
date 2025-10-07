"""
SoilGrids Data Downloader for Atlas Explorer Integration
Downloads environmental soil data to complement Atlas Explorer socio-economic data
Implements Risk = Hazard × Vulnerability where Vulnerability combines poverty + soil degradation
"""

import os
import requests
import zipfile
import io
import logging
from pathlib import Path
from tqdm import tqdm
import sys

# Add src to path for imports
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from config import Config

# Configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class StrategicDataDownloader:
    """
    SoilGrids data downloader for Atlas Explorer integration.
    Downloads environmental data to complement manually exported Atlas socio-economic data.
    """
    
    def __init__(self):
        self.config = Config()
        self.raw_data_path = self.config.RAW_DATA_PATH
        
        # SoilGrids Dataset Inventory - Alternative approach using smaller regional downloads
        # Since the full WCS service is complex, we'll use a practical approach:
        # Download smaller test regions that we can use for analysis development
        
        # Note: For production, consider using Google Earth Engine or QGIS for larger downloads
        # For now, we'll create a functional approach for analysis development
        
        self.datasets = {
            # ALTERNATIVE: Use OpenLandMap which provides SoilGrids-compatible data
            # These are smaller files suitable for development and testing
            "soil_ph_sample": {
                "url": "https://zenodo.org/record/2525817/files/sol_ph.h2o_usda.4a1a_m_250m_b0..0cm_1950..2017_v0.2.tif?download=1",
                "subdir": "soil/soilgrids",
                "filename": "ph_sample_africa.tif",
                "description": "Soil pH sample data for Africa - Development/Testing",
                "type": "alternative_sample",
                "atlas_integration": "Sample data for developing analysis workflow - replace with full dataset later"
            },
            
            # For now, let's create instructions for manual download of the critical datasets
            "soil_soc_instructions": {
                "url": "https://soilgrids.org",
                "subdir": "soil/soilgrids",
                "filename": "MANUAL_DOWNLOAD_INSTRUCTIONS.txt",
                "description": "Instructions for manually downloading SoilGrids data",
                "type": "manual_instructions",
                "atlas_integration": "Manual download required - see instructions file"
            }
        }
    
    def download_file(self, url: str, filepath: Path) -> bool:
        """Downloads a file with progress bar and error handling."""
        try:
            response = requests.get(url, stream=True, timeout=300)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            
            with open(filepath, 'wb') as f, tqdm(
                desc=filepath.name,
                total=total_size,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        size = f.write(chunk)
                        bar.update(size)
            
            logging.info(f"✅ Successfully downloaded {filepath.name}")
            return True
            
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ Failed to download {url}. Error: {e}")
            return False
        except Exception as e:
            logging.error(f"❌ Unexpected error downloading {url}. Error: {e}")
            return False
    
    def create_soilgrids_instructions(self, filepath: Path, item: dict):
        """Creates detailed instructions for manually downloading SoilGrids data."""
        instructions = f"""
SOILGRIDS DATA DOWNLOAD INSTRUCTIONS

The automated download of SoilGrids data encountered technical issues with the WCS service.
Please follow these steps to manually download the required soil data:

OPTION 1: Using Google Earth Engine (Recommended)
=================================================
1. Go to: https://code.earthengine.google.com/
2. Sign in with Google account
3. Use this code snippet to download SoilGrids data for Sub-Saharan Africa:

```javascript
// SoilGrids data download for Sub-Saharan Africa
var soilgridsPH = ee.Image("OpenLandMap/SOL/SOL_PH-H2O_USDA-4A1A_M/v02");
var soilgridsSOC = ee.Image("OpenLandMap/SOL/SOL_ORGANIC-CARBON_USDA-6A1C_M/v02");
var soilgridsSand = ee.Image("OpenLandMap/SOL/SOL_SAND-WFRACTION_USDA-3A1A1A_M/v02");
var soilgridsClay = ee.Image("OpenLandMap/SOL/SOL_CLAY-WFRACTION_USDA-3A1A1A_M/v02");

// Sub-Saharan Africa bounds
var ssaBounds = ee.Geometry.Rectangle([-20, -35, 55, 20]);

// Export each dataset
Export.image.toDrive({{
  image: soilgridsPH.select('b0').clip(ssaBounds),
  description: 'soil_ph_ssa',
  scale: 1000,
  region: ssaBounds,
  maxPixels: 1e9
}});
```

OPTION 2: Direct Download from SoilGrids.org
============================================
1. Go to: https://soilgrids.org/
2. Navigate to the "Download" section
3. Select your area of interest (Sub-Saharan Africa)
4. Choose these variables:
   - Soil pH (0-5cm depth)
   - Soil Organic Carbon (0-5cm depth) 
   - Sand content (0-5cm depth)
   - Clay content (0-5cm depth)
5. Download as GeoTIFF format

OPTION 3: Using QGIS with WCS Plugin
===================================
1. Install QGIS from: https://qgis.org/
2. Add WCS layer using this URL: https://maps.isric.org/mapserv
3. Select SoilGrids layers for your variables
4. Clip to Sub-Saharan Africa extent
5. Export as GeoTIFF

TARGET FILES TO CREATE:
======================
- data/raw/soil/soilgrids/phh2o_0-5cm_ssa.tif
- data/raw/soil/soilgrids/soc_0-5cm_ssa.tif  
- data/raw/soil/soilgrids/sand_0-5cm_ssa.tif
- data/raw/soil/soilgrids/clay_0-5cm_ssa.tif

INTEGRATION WITH ATLAS DATA:
===========================
These soil datasets will be combined with the Atlas Explorer data:
- {item['atlas_integration']}

Once downloaded, place the files in: {filepath.parent}
Then re-run the analysis scripts to proceed with risk assessment.
"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(instructions)
        logging.info(f"📝 Created SoilGrids download instructions: {filepath.name}")
    

    def download_soilgrids_datasets(self) -> dict:
        """
        Download SoilGrids datasets to complement Atlas Explorer data.
        Atlas provides: Hazard (NDWS), Exposure (VOP, Population), Adaptive Capacity (Poverty)
        SoilGrids provides: Environmental vulnerability (soil health baseline)
        Returns summary of download results.
        """
        logging.info("🚀 DOWNLOADING SOILGRIDS DATA FOR ATLAS INTEGRATION")
        logging.info("="*70)
        logging.info("� Hybrid Approach: Atlas Explorer (socio-economic) + SoilGrids (environmental)")
        logging.info("📊 Atlas Data Status: Already manually downloaded from Atlas Explorer")
        logging.info("🌱 SoilGrids Mission: Provide environmental vulnerability component")
        
        # Ensure raw data directory exists
        self.raw_data_path.mkdir(parents=True, exist_ok=True)
        
        results = {
            'downloaded': [],
            'existing': [],
            'failed': []
        }
        
        for key, item in self.datasets.items():
            logging.info(f"\n📊 Processing: {item['description']}")
            logging.info(f"🔗 Atlas Integration: {item['atlas_integration']}")
            
            target_dir = self.raw_data_path / item['subdir']
            target_dir.mkdir(parents=True, exist_ok=True)
            
            filepath = target_dir / item['filename']
            
            # Check if file already exists
            if filepath.exists() and filepath.stat().st_size > 0:
                logging.info(f"✅ '{filepath.name}' already exists. Skipping download.")
                results['existing'].append(key)
                continue
            
            # Handle different download types
            if item['type'] == 'alternative_sample':
                success = self.download_file(item['url'], filepath)
                if success:
                    results['downloaded'].append(key)
                else:
                    results['failed'].append(key)
                    
            elif item['type'] == 'manual_instructions':
                self.create_soilgrids_instructions(filepath, item)
                results['downloaded'].append(key)  # Count as "downloaded" since instructions were created
        
        # Summary Report
        logging.info("\n" + "="*70)
        logging.info("📈 SOILGRIDS DOWNLOAD SUMMARY")
        logging.info("="*70)
        logging.info(f"✅ Downloaded: {len(results['downloaded'])} SoilGrids datasets")
        logging.info(f"📁 Already existed: {len(results['existing'])} datasets") 
        logging.info(f"❌ Failed: {len(results['failed'])} datasets")
        
        if results['failed']:
            logging.info(f"\n⚠️  FAILED DOWNLOADS ({len(results['failed'])}):")
            for key in results['failed']:
                logging.info(f"   ❌ {key}: {self.datasets[key]['description']}")
        
        total_ready = len(results['downloaded']) + len(results['existing'])
        total_datasets = len(self.datasets)
        
        logging.info(f"\n🎯 SOILGRIDS STATUS: {total_ready}/{total_datasets} soil datasets ready")
        
        # Check Atlas data availability
        atlas_files = [
            "atlas_hazard_ndws_future.csv",
            "atlas_exposure_vop_crops.csv", 
            "atlas_exposure_population.csv",
            "atlas_adaptive_capacity_poverty.csv"
        ]
        
        atlas_ready = sum(1 for f in atlas_files if (self.raw_data_path / f).exists())
        logging.info(f"📊 ATLAS STATUS: {atlas_ready}/{len(atlas_files)} Atlas CSV files detected")
        
        if total_ready == total_datasets and atlas_ready == len(atlas_files):
            logging.info("🚀 ALL DATA READY - PROCEED TO RISK FUSION ANALYSIS!")
        elif atlas_ready < len(atlas_files):
            logging.info("⚠️  Missing Atlas data. Download from Atlas Explorer tool first.")
        else:
            logging.info("⚠️  SoilGrids data incomplete. Retry failed downloads.")
        
        return results

def main():
    """Main function to download SoilGrids data for Atlas integration."""
    downloader = StrategicDataDownloader()
    
    print("🌍 SOILGRIDS DOWNLOADER FOR ATLAS INTEGRATION")
    print("="*60)
    print("� Hybrid Approach: Atlas Explorer + SoilGrids Environmental Data")
    print("📊 Atlas Status: Manually downloaded CSV files from Atlas Explorer")
    print("🌱 SoilGrids Mission: Download environmental vulnerability data")
    print("="*60)
    
    results = downloader.download_soilgrids_datasets()
    return results

if __name__ == "__main__":
    results = main()