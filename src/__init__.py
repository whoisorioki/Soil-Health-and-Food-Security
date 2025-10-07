# Package initialization for src module
"""
Soil Health and Food Security Analysis Package

This package provides tools for analyzing climate impacts on soil health
in Sub-Saharan Africa, including data processing, risk assessment, and
visualization capabilities.
"""

__version__ = "1.0.0"
__author__ = "Soil Health and Food Security Team"
__email__ = "contact@soilhealth-project.org"

# Import main classes for easy access
from .config import Config
from .analysis.soil_health_analysis import SoilHealthAnalyzer
from .data_processing.download_datasets import DataDownloader

__all__ = [
    'Config',
    'SoilHealthAnalyzer', 
    'DataDownloader',
]