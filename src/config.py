"""
Configuration management for Soil Health and Food Security project.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration settings for the project."""
    
    # Project paths
    PROJECT_ROOT = Path(__file__).parent.parent
    DATA_ROOT = Path(os.getenv('DATA_ROOT', PROJECT_ROOT / 'data'))
    RAW_DATA_PATH = Path(os.getenv('RAW_DATA_PATH', DATA_ROOT / 'raw'))
    PROCESSED_DATA_PATH = Path(os.getenv('PROCESSED_DATA_PATH', DATA_ROOT / 'processed'))
    CACHE_PATH = Path(os.getenv('CACHE_PATH', DATA_ROOT / 'cache'))
    
    # Environment settings
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    DEBUG = os.getenv('DEBUG', 'true').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Data processing settings
    DEFAULT_CRS = os.getenv('DEFAULT_CRS', 'EPSG:102022')  # Africa Albers Equal Area
    TARGET_RESOLUTION = int(os.getenv('TARGET_RESOLUTION', '1000').strip().split()[0])  # meters
    CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '1000').strip().split()[0])
    
    # Analysis thresholds
    SOIL_PH_THRESHOLD = float(os.getenv('SOIL_PH_THRESHOLD', '5.5').strip().split()[0])
    SOC_THRESHOLD = float(os.getenv('SOC_THRESHOLD', '1.0').strip().split()[0])  # percent
    EROSION_SEVERE_THRESHOLD = float(os.getenv('EROSION_SEVERE_THRESHOLD', '50').strip().split()[0])  # tonnes/ha/year
    
    # API credentials
    GOOGLE_EARTH_ENGINE_SERVICE_ACCOUNT = os.getenv('GOOGLE_EARTH_ENGINE_SERVICE_ACCOUNT')
    GOOGLE_EARTH_ENGINE_PRIVATE_KEY = os.getenv('GOOGLE_EARTH_ENGINE_PRIVATE_KEY')
    ISIMIP_USERNAME = os.getenv('ISIMIP_USERNAME')
    ISIMIP_PASSWORD = os.getenv('ISIMIP_PASSWORD')
    WORLDBANK_API_KEY = os.getenv('WORLDBANK_API_KEY')
    
    # External service URLs
    SOILGRIDS_WCS_URL = os.getenv('SOILGRIDS_WCS_URL', 'https://maps.isric.org/mapserv')
    ISIMIP_DATA_URL = os.getenv('ISIMIP_DATA_URL', 'https://files.isimip.org')
    WOCAT_API_URL = os.getenv('WOCAT_API_URL', 'https://qcat.wocat.net/api')
    
    # Web service configuration
    API_PORT = int(os.getenv('API_PORT', '8000').strip().split()[0])
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')
    RATE_LIMIT = int(os.getenv('RATE_LIMIT', '100').strip().split()[0])
    
    # Observable configuration
    OBSERVABLE_WORKSPACE = os.getenv('OBSERVABLE_WORKSPACE', 'soil-health-ssa')
    OBSERVABLE_TOKEN = os.getenv('OBSERVABLE_TOKEN')
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they don't exist."""
        for path in [cls.DATA_ROOT, cls.RAW_DATA_PATH, cls.PROCESSED_DATA_PATH, cls.CACHE_PATH]:
            path.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate essential configuration settings."""
        required_vars = [
            'DEFAULT_CRS',
            'TARGET_RESOLUTION',
        ]
        
        missing_vars = []
        for var in required_vars:
            if not hasattr(cls, var) or getattr(cls, var) is None:
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required configuration variables: {missing_vars}")
        
        return True

# Data source configurations
DATA_SOURCES = {
    'soilgrids': {
        'name': 'SoilGrids250m v2.0',
        'variables': ['phh2o', 'soc', 'sand', 'silt', 'clay', 'bdod'],
        'depths': ['0-5cm', '5-15cm', '15-30cm'],
        'resolution': '250m',
        'crs': 'EPSG:4326',
        'url_template': 'https://maps.isric.org/mapserv'
    },
    'glosem': {
        'name': 'Global Soil Erosion Modelling v1.3',
        'variables': ['rill_inter_rill_erosion'],
        'resolution': '100m',
        'crs': 'EPSG:4326',
        'download_url': 'https://esdac.jrc.ec.europa.eu/resource-type/european-soil-database-derived-data'
    },
    'isimip': {
        'name': 'ISIMIP Climate Projections',
        'variables': ['mrso', 'pr', 'tas', 'evspsbl'],
        'scenarios': ['ssp126', 'ssp245', 'ssp370', 'ssp585'],
        'models': ['GFDL-ESM4', 'IPSL-CM6A-LR', 'MPI-ESM1-2-HR', 'MRI-ESM2-0', 'UKESM1-0-LL'],
        'resolution': '0.5deg',
        'temporal_resolution': 'monthly',
        'base_url': 'https://files.isimip.org/ISIMIP3b/OutputData/climate'
    },
    'mapspam': {
        'name': 'MapSPAM 2017',
        'variables': ['area', 'production', 'yield'],
        'crops': ['maize', 'rice', 'wheat', 'sorghum', 'millet', 'cassava', 'yams', 'cowpea'],
        'systems': ['irrigated', 'rainfed_high', 'rainfed_low', 'subsistence'],
        'resolution': '10km',
        'base_url': 'https://mapspam.info/data'
    },
    'livestock': {
        'name': 'Gridded Livestock of the World v4',
        'variables': ['cattle', 'sheep', 'goats', 'pigs', 'chickens'],
        'resolution': '10km',
        'base_url': 'http://www.fao.org/livestock-systems/global-distributions'
    }
}

# Regional boundaries for Sub-Saharan Africa
SSA_COUNTRIES = [
    'AGO', 'BDI', 'BEN', 'BFA', 'BWA', 'CAF', 'CIV', 'CMR', 'COD', 'COG',
    'COM', 'CPV', 'DJI', 'ERI', 'ETH', 'GAB', 'GHA', 'GIN', 'GMB', 'GNB',
    'GNQ', 'KEN', 'LBR', 'LSO', 'MDG', 'MLI', 'MOZ', 'MRT', 'MUS', 'MWI',
    'NAM', 'NER', 'NGA', 'RWA', 'SEN', 'SLE', 'SOM', 'SSD', 'STP', 'SWZ',
    'SYC', 'TCD', 'TGO', 'TZA', 'UGA', 'ZAF', 'ZMB', 'ZWE'
]

# Analysis parameters
RISK_WEIGHTS = {
    'erosion': 0.3,
    'soc_loss': 0.3,
    'acidity': 0.2,
    'moisture_stress': 0.2
}

RISK_THRESHOLDS = {
    'low': 0.25,
    'moderate': 0.5,
    'high': 0.75,
    'very_high': 1.0
}

# Atlas Data Processing Configuration
ATLAS_MERGE_KEYS = ['country', 'region', 'sub_region']

# Strategic filtering parameters for Atlas data fusion
ATLAS_FILTERS = {
    'scenario': 'ssp245',  # Moderate climate pathway
    'poverty_line': 3.65,  # USD per day
    'population_type': 'total'  # Total population (not just vulnerable)
}

# Data validation thresholds
VALIDATION_THRESHOLDS = {
    'ndws_future_days': {'min': 0, 'max': 365},
    'poverty_headcount_ratio': {'min': 0, 'max': 1},
    'vop_crops_usd': {'min': 0, 'max': float('inf')},
    'population': {'min': 0, 'max': float('inf')},
    'hazard_score': {'min': 0, 'max': 1},
    'social_vulnerability_score': {'min': 0, 'max': 1},
    'preliminary_risk_score': {'min': 0, 'max': 1}
}