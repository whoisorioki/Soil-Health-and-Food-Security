# Soil Health and Food Security: Climate Risk Assessment for Sub-Saharan Africa

## Project Overview

**🎯 Zindi Climate Adaptation Challenge - Data Storytelling Platform**

This project creates an interactive risk assessment platform analyzing climate impacts on soil health across Sub-Saharan Africa. Using the Atlas Explorer framework, we transform complex geospatial data into actionable insights for adaptation planners through a structured narrative approach.

## Current Status: Complete Geospatial Integration ✅ PHASE 2 COMPLETE

**Phase 1: Atlas Data Integration** - **✅ COMPLETE**
- ✅ Individual dataset exploration and quality assessment
- ✅ Strategic data fusion with proper filtering (SSP245, $3.65 poverty line, total population)
- ✅ Data cleaning and standardization (4,444 validated records across 44 countries)
- ✅ Comprehensive validation pipeline with 100% data completeness

**Phase 2: Geospatial Integration** - **✅ COMPLETE**
- ✅ SoilGrids environmental data integration (pH, SOC, sand, clay)
- ✅ GloSEM erosion data integration (2012 baseline)
- ✅ Admin boundaries spatial processing (4,596 features)
- ✅ Compound risk assessment: 4,444 sub-regions analyzed
- ✅ Risk hotspots identified: 281 high-risk areas (42.4M people at risk)
- ✅ Complete coordinate system harmonization and zonal statistics

**Phase 3: Observable Framework Visualization** - **🚧 READY TO START**
- 🎯 Interactive risk assessment dashboard
- 🎯 Narrative-driven data storytelling (5-question structure)
- 🎯 Observable Framework deployment

## Risk Assessment Framework

**Formula**: `Risk = Hazard × Vulnerability`
- **Hazard**: Future water stress projections (NDWS 2041-2060)
- **Exposure**: Agricultural value + Population at risk
- **Vulnerability**: Poverty indicators + Soil degradation factors

## Target Audience

- **Primary**: Adaptation planners, scientists, and proposal writers
- **Key Institutions**: African Group of Negotiators Experts Support (AGNES), African Transformation Initiative (ATI)
- **Secondary**: Government bodies, healthcare providers, NGOs, and community groups

## Project Architecture

### Data Pipeline Structure
```
├── data/
│   ├── raw/                      # Original datasets
│   │   ├── atlas_hazard_ndws_future.csv      # Water stress projections
│   │   ├── atlas_exposure_vop_crops.csv      # Agricultural value
│   │   ├── atlas_exposure_population.csv     # Population exposure
│   │   ├── atlas_adaptive_capacity_poverty.csv # Vulnerability data
│   │   └── soil/soilgrids/                   # Environmental soil data
│   ├── processed/                # Clean, validated datasets
│   │   └── master_atlas_data_cleaned.csv     # 4,444 validated records
│   └── cache/                    # Intermediate processing results
├── src/
│   ├── analysis/                 # Data processing pipeline
│   │   ├── 0_explore_atlas_data.py           # Individual dataset analysis
│   │   ├── 1_fuse_atlas_data.py              # Strategic data fusion
│   │   ├── 1_clean_atlas_data.py             # Data cleaning
│   │   ├── 1_validate_atlas_data.py          # Quality assurance
│   │   └── soil_health_analysis.py           # Geospatial integration
│   ├── data_processing/          # Data acquisition
│   └── config.py                 # Central configuration
├── notebooks/                    # Interactive analysis
└── .github/copilot-instructions.md # AI agent guidance
```

## Key Deliverables

1. **Interactive Observable Notebook** - Main storytelling platform
2. **Compound Risk Assessment Tool** - Hotspot identification system
3. **Solutions Explorer** - Evidence-based intervention recommendations
4. **Policy Integration Framework** - Connection to regional and national policies

## Getting Started

See the [Product Requirements Document](docs/PRD.md) for detailed specifications and implementation guidelines.

## Quick Links

- [Project Setup Guide](docs/setup.md)
- [Data Sources Inventory](docs/data-inventory.md)
- [Development Roadmap](docs/roadmap.md)
- [Contribution Guidelines](docs/contributing.md)

## Atlas Explorer Risk Assessment Framework

Our analysis follows the three-pillar risk assessment structure:

### 🔥 **Hazard** (Climate Threat)
- **Water Stress Projections**: Number of Days of Water Stress (NDWS) for 2041-2060
- **Scenario**: SSP245 (moderate climate pathway)
- **Coverage**: Sub-region level across Sub-Saharan Africa

### 🎯 **Exposure** (What's at Stake)
- **Agricultural Value**: Total crop value of production (USD)
- **Population**: Total population in exposed areas
- **Aggregation**: Sum of all crop types and total population

### 🛡️ **Vulnerability** (Adaptive Capacity)
- **Socio-Economic**: Poverty headcount ratio ($3.65/day threshold)
- **Environmental**: Soil degradation indicators (pH, SOC, texture)
- **Integration**: Combined social and environmental vulnerability

### 📊 **Risk Calculation**
**Risk = Hazard × Vulnerability** where higher values indicate greater climate risk

## Technology Stack

- **Primary Platform**: Observable Framework (target)
- **Data Processing**: Python (pandas, geopandas, rasterio, xarray)
- **Geographic Analysis**: Africa Albers Equal Area projection (EPSG:102022)
- **Data Sources**: Atlas Explorer + SoilGrids integration
- **Validation**: Comprehensive quality assurance pipeline
- **Visualization**: D3.js, Vega-Lite (planned)

## Quick Start

### Prerequisites
```powershell
# Activate virtual environment
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Run Data Pipeline
```powershell
# Validate current data
python src/analysis/1_validate_atlas_data.py

# Check setup
python test_setup.py
python test_datasets.py
```

### Data Status
- ✅ **Atlas Data**: 4,444 validated records ready
- ⏳ **SoilGrids Data**: Manual download required (see `data/raw/soil/soilgrids/MANUAL_DOWNLOAD_INSTRUCTIONS.txt`)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
