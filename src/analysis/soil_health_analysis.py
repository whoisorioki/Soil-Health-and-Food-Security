"""
Soil health analysis functions for the Soil Health and Food Security project.
"""

import numpy as np
import pandas as pd
import geopandas as gpd
import xarray as xr
import rasterio
from rasterio.mask import mask
from rasterio.warp import calculate_default_transform, reproject, Resampling
from pathlib import Path
import logging
import sys
from typing import Dict, List, Tuple, Optional, Union

# Add src to path for imports
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from config import Config, RISK_THRESHOLDS, SSA_COUNTRIES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SoilHealthAnalyzer:
    """Analyzes soil health conditions across Sub-Saharan Africa."""
    
    def __init__(self):
        self.config = Config()
        self.config.ensure_directories()
        
    def load_soil_data(self, variable: str, depth: str = "0_5cm") -> xr.DataArray:
        """Load SoilGrids soil data for a specific variable and depth."""
        soil_dir = self.config.RAW_DATA_PATH / 'soil' / 'soilgrids'
        filename = f"{variable}_{depth}_ssa.tif"
        filepath = soil_dir / filename
        
        if not filepath.exists():
            raise FileNotFoundError(f"Soil data file not found: {filepath}")
        
        # Load using xarray for better integration with climate data
        da = xr.open_rasterio(filepath)
        
        # Add metadata
        da.attrs['variable'] = variable
        da.attrs['depth'] = depth
        da.attrs['source'] = 'SoilGrids250m v2.0'
        
        return da.squeeze()  # Remove band dimension if present
    
    def classify_soil_ph(self, ph_data: xr.DataArray) -> xr.DataArray:
        """Classify soil pH into acidity categories."""
        # pH classification based on agricultural standards
        conditions = [
            ph_data < 4.5,          # Extremely acid
            (ph_data >= 4.5) & (ph_data < 5.5),  # Very strongly acid
            (ph_data >= 5.5) & (ph_data < 6.0),  # Strongly acid
            (ph_data >= 6.0) & (ph_data < 6.5),  # Moderately acid
            (ph_data >= 6.5) & (ph_data < 7.3),  # Slightly acid to neutral
            (ph_data >= 7.3) & (ph_data < 7.8),  # Slightly alkaline
            ph_data >= 7.8,         # Moderately to strongly alkaline
        ]
        
        categories = [1, 2, 3, 4, 5, 6, 7]  # 1 = most problematic, 7 = optimal
        
        ph_classes = xr.where(conditions[0], categories[0], 0)
        for i, condition in enumerate(conditions[1:], 1):
            ph_classes = xr.where(condition, categories[i], ph_classes)
        
        # Create risk score (inverse of class, normalized)
        ph_risk = (8 - ph_classes) / 7.0  # Scale 0-1, where 1 = highest risk
        
        ph_risk.attrs.update({
            'long_name': 'Soil pH Acidity Risk',
            'units': 'risk_score',
            'scale': '0-1 (0=low risk, 1=high risk)',
            'threshold': self.config.SOIL_PH_THRESHOLD
        })
        
        return ph_risk
    
    def assess_soc_content(self, soc_data: xr.DataArray) -> xr.DataArray:
        """Assess soil organic carbon content and create risk score."""
        # Convert from g/kg to percentage if needed
        if soc_data.max() > 100:  # Likely in g/kg
            soc_percent = soc_data / 10.0
        else:
            soc_percent = soc_data
        
        # SOC risk assessment (lower SOC = higher risk)
        # Critical threshold: 1% (10 g/kg)
        soc_risk = xr.where(
            soc_percent < self.config.SOC_THRESHOLD,
            1.0 - (soc_percent / self.config.SOC_THRESHOLD),  # Scale 0-1
            0.0
        )
        
        # Cap at 1.0 for very low SOC values
        soc_risk = xr.where(soc_risk > 1.0, 1.0, soc_risk)
        
        soc_risk.attrs.update({
            'long_name': 'Soil Organic Carbon Depletion Risk',
            'units': 'risk_score',
            'scale': '0-1 (0=low risk, 1=high risk)',
            'threshold': f'{self.config.SOC_THRESHOLD}%'
        })
        
        return soc_risk
    
    def classify_soil_texture(self, sand: xr.DataArray, silt: xr.DataArray, 
                            clay: xr.DataArray) -> xr.DataArray:
        """Classify soil texture and assess erosion susceptibility."""
        # Normalize to percentages if needed
        total = sand + silt + clay
        sand_pct = (sand / total) * 100
        silt_pct = (silt / total) * 100
        clay_pct = (clay / total) * 100
        
        # Simplified texture classification focusing on erosion risk
        # Sandy soils (>70% sand): High erosion risk
        # Clayey soils (>35% clay): Low erosion risk (but other issues)
        # Balanced soils: Moderate erosion risk
        
        texture_risk = xr.where(
            sand_pct > 70,  # Sandy soils
            0.8,  # High erosion risk
            xr.where(
                clay_pct > 35,  # Clayey soils
                0.3,  # Lower erosion risk but other constraints
                0.5   # Balanced soils - moderate risk
            )
        )
        
        texture_risk.attrs.update({
            'long_name': 'Soil Texture Erosion Risk',
            'units': 'risk_score',
            'scale': '0-1 (0=low risk, 1=high risk)',
            'description': 'Based on sand content and erosion susceptibility'
        })
        
        return texture_risk
    
    def assess_erosion_risk(self, erosion_data: xr.DataArray) -> xr.DataArray:
        """Assess soil erosion risk from GloSEM data."""
        # GloSEM provides soil loss in tonnes/ha/year
        # Classify based on USDA soil loss tolerance levels
        
        # Normalize erosion rates to risk score
        # Using log transformation due to wide range of erosion values
        erosion_log = xr.where(erosion_data > 0, np.log10(erosion_data + 1), 0)
        
        # Severe erosion threshold: 50 t/ha/year (log10(51) ≈ 1.7)
        severe_threshold_log = np.log10(self.config.EROSION_SEVERE_THRESHOLD + 1)
        
        erosion_risk = erosion_log / severe_threshold_log
        erosion_risk = xr.where(erosion_risk > 1.0, 1.0, erosion_risk)  # Cap at 1.0
        erosion_risk = xr.where(erosion_risk < 0.0, 0.0, erosion_risk)  # Floor at 0.0
        
        erosion_risk.attrs.update({
            'long_name': 'Water Erosion Risk',
            'units': 'risk_score',
            'scale': '0-1 (0=low risk, 1=high risk)',
            'severe_threshold': f'{self.config.EROSION_SEVERE_THRESHOLD} t/ha/year',
            'source': 'GloSEM v1.3'
        })
        
        return erosion_risk
    
    def create_soil_health_index(self, ph_risk: xr.DataArray, soc_risk: xr.DataArray,
                               texture_risk: xr.DataArray, erosion_risk: xr.DataArray) -> xr.DataArray:
        """Create composite soil health index from individual risk components."""
        
        # Weights based on FAO SWSR importance ranking for SSA
        weights = {
            'erosion': 0.35,      # Most important threat
            'soc': 0.30,          # Second most important
            'texture': 0.20,      # Influences erosion and water retention
            'ph': 0.15            # Important but more manageable
        }
        
        # Calculate weighted composite index
        soil_health_index = (
            weights['erosion'] * erosion_risk +
            weights['soc'] * soc_risk +
            weights['texture'] * texture_risk +
            weights['ph'] * ph_risk
        )
        
        # Ensure index is between 0 and 1
        soil_health_index = xr.where(soil_health_index > 1.0, 1.0, soil_health_index)
        soil_health_index = xr.where(soil_health_index < 0.0, 0.0, soil_health_index)
        
        soil_health_index.attrs.update({
            'long_name': 'Composite Soil Health Risk Index',
            'units': 'risk_score',
            'scale': '0-1 (0=low risk, 1=high risk)',
            'weights': str(weights),
            'components': 'erosion, soc_depletion, texture, ph_acidity'
        })
        
        return soil_health_index
    
    def classify_risk_levels(self, risk_index: xr.DataArray) -> xr.DataArray:
        """Classify continuous risk index into categorical risk levels."""
        
        conditions = [
            risk_index < RISK_THRESHOLDS['low'],
            (risk_index >= RISK_THRESHOLDS['low']) & (risk_index < RISK_THRESHOLDS['moderate']),
            (risk_index >= RISK_THRESHOLDS['moderate']) & (risk_index < RISK_THRESHOLDS['high']),
            risk_index >= RISK_THRESHOLDS['high']
        ]
        
        categories = [1, 2, 3, 4]  # Low, Moderate, High, Very High
        category_names = ['Low', 'Moderate', 'High', 'Very High']
        
        risk_classes = xr.where(conditions[0], categories[0], 0)
        for i, condition in enumerate(conditions[1:], 1):
            risk_classes = xr.where(condition, categories[i], risk_classes)
        
        risk_classes.attrs.update({
            'long_name': 'Soil Health Risk Classification',
            'units': 'category',
            'categories': {i+1: name for i, name in enumerate(category_names)},
            'thresholds': RISK_THRESHOLDS
        })
        
        return risk_classes
    
    def analyze_soil_health(self, depth: str = "0_5cm") -> Dict[str, xr.DataArray]:
        """Complete soil health analysis workflow."""
        logger.info(f"Starting soil health analysis for depth: {depth}")
        
        # Load soil data
        logger.info("Loading soil data...")
        ph_data = self.load_soil_data('phh2o', depth)
        soc_data = self.load_soil_data('soc', depth)
        sand_data = self.load_soil_data('sand', depth)
        silt_data = self.load_soil_data('silt', depth)
        clay_data = self.load_soil_data('clay', depth)
        
        # Load erosion data (separate resolution, needs resampling)
        logger.info("Loading erosion data...")
        try:
            erosion_path = self.config.RAW_DATA_PATH / 'soil' / 'glosem' / 'glosem_ssa.tif'
            erosion_data = xr.open_rasterio(erosion_path).squeeze()
        except FileNotFoundError:
            logger.warning("GloSEM erosion data not found. Using placeholder.")
            erosion_data = xr.zeros_like(ph_data)
        
        # Align all datasets to the same grid
        logger.info("Aligning datasets...")
        # Resample erosion data to match SoilGrids resolution if needed
        if erosion_data.sizes != ph_data.sizes:
            erosion_data = erosion_data.interp_like(ph_data, method='linear')
        
        # Calculate risk indices
        logger.info("Calculating risk indices...")
        ph_risk = self.classify_soil_ph(ph_data)
        soc_risk = self.assess_soc_content(soc_data)
        texture_risk = self.classify_soil_texture(sand_data, silt_data, clay_data)
        erosion_risk = self.assess_erosion_risk(erosion_data)
        
        # Create composite index
        logger.info("Creating composite soil health index...")
        soil_health_index = self.create_soil_health_index(
            ph_risk, soc_risk, texture_risk, erosion_risk
        )
        
        # Classify risk levels
        risk_classes = self.classify_risk_levels(soil_health_index)
        
        results = {
            'ph_risk': ph_risk,
            'soc_risk': soc_risk,
            'texture_risk': texture_risk,
            'erosion_risk': erosion_risk,
            'soil_health_index': soil_health_index,
            'risk_classes': risk_classes,
            'raw_data': {
                'ph': ph_data,
                'soc': soc_data,
                'sand': sand_data,
                'silt': silt_data,
                'clay': clay_data,
                'erosion': erosion_data
            }
        }
        
        logger.info("Soil health analysis completed successfully!")
        return results
    
    def save_results(self, results: Dict[str, xr.DataArray], output_dir: Optional[Path] = None):
        """Save analysis results to disk."""
        if output_dir is None:
            output_dir = self.config.PROCESSED_DATA_PATH / 'soil_health'
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save main results
        for name, data in results.items():
            if name != 'raw_data':  # Skip raw data for space efficiency
                output_path = output_dir / f"{name}.nc"
                data.to_netcdf(output_path)
                logger.info(f"Saved {name} to {output_path}")
        
        # Save summary statistics
        summary_stats = {}
        for name, data in results.items():
            if name != 'raw_data':
                summary_stats[name] = {
                    'mean': float(data.mean().values),
                    'std': float(data.std().values),
                    'min': float(data.min().values),
                    'max': float(data.max().values),
                    'count_valid': int((~data.isnull()).sum().values)
                }
        
        # Save summary as JSON
        import json
        summary_path = output_dir / 'summary_statistics.json'
        with open(summary_path, 'w') as f:
            json.dump(summary_stats, f, indent=2)
        
        logger.info(f"Summary statistics saved to {summary_path}")

def main():
    """Main function for command-line usage."""
    analyzer = SoilHealthAnalyzer()
    results = analyzer.analyze_soil_health()
    analyzer.save_results(results)
    
    print("\nSoil Health Analysis Summary:")
    print(f"Soil Health Index - Mean: {results['soil_health_index'].mean().values:.3f}")
    print(f"High/Very High Risk Areas: {(results['risk_classes'] >= 3).sum().values} pixels")

if __name__ == "__main__":
    main()