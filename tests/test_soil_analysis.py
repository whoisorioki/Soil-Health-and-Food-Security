"""
Basic test for soil health analysis functionality.
"""

import pytest
import numpy as np
import xarray as xr
from pathlib import Path
import tempfile

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from analysis.soil_health_analysis import SoilHealthAnalyzer
from config import Config

class TestSoilHealthAnalyzer:
    """Test cases for SoilHealthAnalyzer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = SoilHealthAnalyzer()
        
        # Create sample data
        self.sample_ph = xr.DataArray(
            np.array([[4.0, 5.5, 6.5], [7.0, 8.0, 5.0]]),
            dims=['y', 'x'],
            coords={'y': [0, 1], 'x': [0, 1, 2]}
        )
        
        self.sample_soc = xr.DataArray(
            np.array([[0.5, 1.5, 2.0], [3.0, 0.8, 1.2]]),
            dims=['y', 'x'],
            coords={'y': [0, 1], 'x': [0, 1, 2]}
        )
        
    def test_classify_soil_ph(self):
        """Test pH classification functionality."""
        ph_risk = self.analyzer.classify_soil_ph(self.sample_ph)
        
        # Check output properties
        assert isinstance(ph_risk, xr.DataArray)
        assert ph_risk.min() >= 0.0
        assert ph_risk.max() <= 1.0
        assert ph_risk.shape == self.sample_ph.shape
        
        # Check risk ranking (lower pH should have higher risk)
        assert ph_risk.isel(y=0, x=0) > ph_risk.isel(y=0, x=2)  # pH 4.0 > pH 6.5
        
    def test_assess_soc_content(self):
        """Test SOC assessment functionality."""
        soc_risk = self.analyzer.assess_soc_content(self.sample_soc)
        
        # Check output properties
        assert isinstance(soc_risk, xr.DataArray)
        assert soc_risk.min() >= 0.0
        assert soc_risk.max() <= 1.0
        assert soc_risk.shape == self.sample_soc.shape
        
        # Check risk ranking (lower SOC should have higher risk)
        assert soc_risk.isel(y=0, x=0) > soc_risk.isel(y=0, x=2)  # 0.5% > 2.0%
        
    def test_classify_soil_texture(self):
        """Test soil texture classification."""
        # Create sample texture data
        sand = xr.DataArray(np.array([[80, 30, 40], [20, 70, 50]]), dims=['y', 'x'])
        silt = xr.DataArray(np.array([[15, 40, 35], [30, 20, 30]]), dims=['y', 'x'])
        clay = xr.DataArray(np.array([[5, 30, 25], [50, 10, 20]]), dims=['y', 'x'])
        
        texture_risk = self.analyzer.classify_soil_texture(sand, silt, clay)
        
        # Check output properties
        assert isinstance(texture_risk, xr.DataArray)
        assert texture_risk.min() >= 0.0
        assert texture_risk.max() <= 1.0
        assert texture_risk.shape == sand.shape
        
    def test_assess_erosion_risk(self):
        """Test erosion risk assessment."""
        # Create sample erosion data (t/ha/year)
        erosion_data = xr.DataArray(
            np.array([[10, 50, 100], [5, 25, 75]]),
            dims=['y', 'x']
        )
        
        erosion_risk = self.analyzer.assess_erosion_risk(erosion_data)
        
        # Check output properties
        assert isinstance(erosion_risk, xr.DataArray)
        assert erosion_risk.min() >= 0.0
        assert erosion_risk.max() <= 1.0
        assert erosion_risk.shape == erosion_data.shape
        
        # Check risk ranking (higher erosion should have higher risk)
        assert erosion_risk.isel(y=0, x=2) > erosion_risk.isel(y=0, x=0)  # 100 > 10
        
    def test_create_soil_health_index(self):
        """Test composite soil health index creation."""
        # Create sample risk data
        ph_risk = xr.DataArray(np.array([[0.8, 0.2], [0.5, 0.3]]), dims=['y', 'x'])
        soc_risk = xr.DataArray(np.array([[0.7, 0.1], [0.4, 0.2]]), dims=['y', 'x'])
        texture_risk = xr.DataArray(np.array([[0.6, 0.3], [0.5, 0.4]]), dims=['y', 'x'])
        erosion_risk = xr.DataArray(np.array([[0.9, 0.2], [0.3, 0.1]]), dims=['y', 'x'])
        
        soil_index = self.analyzer.create_soil_health_index(
            ph_risk, soc_risk, texture_risk, erosion_risk
        )
        
        # Check output properties
        assert isinstance(soil_index, xr.DataArray)
        assert soil_index.min() >= 0.0
        assert soil_index.max() <= 1.0
        assert soil_index.shape == ph_risk.shape
        
        # Check that composite reflects input risks
        assert soil_index.isel(y=0, x=0) > soil_index.isel(y=0, x=1)  # Higher risk pixel
        
    def test_classify_risk_levels(self):
        """Test risk level classification."""
        # Create sample continuous risk data
        risk_data = xr.DataArray(
            np.array([[0.1, 0.3, 0.6], [0.8, 0.9, 0.4]]),
            dims=['y', 'x']
        )
        
        risk_classes = self.analyzer.classify_risk_levels(risk_data)
        
        # Check output properties
        assert isinstance(risk_classes, xr.DataArray)
        assert risk_classes.min() >= 1
        assert risk_classes.max() <= 4
        assert risk_classes.shape == risk_data.shape
        
        # Check classification logic
        assert risk_classes.isel(y=0, x=0) == 1  # Low risk (0.1)
        assert risk_classes.isel(y=1, x=0) == 4  # Very high risk (0.8)

def test_config_validation():
    """Test configuration validation."""
    config = Config()
    assert config.validate_config() == True
    assert hasattr(config, 'DEFAULT_CRS')
    assert hasattr(config, 'TARGET_RESOLUTION')

if __name__ == "__main__":
    pytest.main([__file__])