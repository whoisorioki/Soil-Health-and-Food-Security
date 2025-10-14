#!/usr/bin/env python3
"""
Step 2: Geospatial Processing & Risk Calculation
==============================================

This script integrates SoilGrids environmental data with Atlas socio-economic data
to create a comprehensive compound risk assessment for Sub-Saharan Africa.

Following the PRD narrative structure:
1. Load Atlas master data (from Step 1)
2. Process SoilGrids raster data via zonal statistics
3. Calculate environmental vulnerability scores
4. Compute final compound risk scores
5. Export visualization-ready datasets

Risk Formula: Risk = Hazard × Combined_Vulnerability
Where: Combined_Vulnerability = f(Social_Poverty, Environmental_Soil_Degradation)
"""

import pandas as pd
import geopandas as gpd
from rasterstats import zonal_stats
from pathlib import Path
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
import tempfile
import numpy as np
import sys
import warnings
warnings.filterwarnings('ignore')

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from config import Config

def setup_paths():
    """Configure all data paths and verify required files exist."""
    config = Config()
    
    # Configure paths
    paths = {
        'data_root': config.DATA_ROOT,
        'raw_data': config.RAW_DATA_PATH,
        'processed_data': config.PROCESSED_DATA_PATH,
    }
    
    # Ensure processed data directory exists
    paths['processed_data'].mkdir(exist_ok=True)
    
    # Input files
    paths['atlas_data'] = paths['processed_data'] / "master_atlas_data_cleaned.csv"
    paths['boundaries'] = paths['raw_data'] / "atlas_admin2_boundaries.json"
    
    # SoilGrids raster files (2017 baseline)
    soil_dir = paths['raw_data'] / "soil" / "soilgrids"
    glosem_dir = paths['raw_data'] / "soil" / "GloSEM_25km" / "Data_25km"
    glosem_13_dir = paths['raw_data'] / "soil" / "GloSEM_1.3"  # For upcoming GloSEM 1.3 data
    
    raster_files = {
        # SoilGrids 2017 data (EPSG:4326, good coverage for land areas)
        'soil_ph': soil_dir / "soilgrids_ph_0-5cm_ssa.tif",
        'soil_soc': soil_dir / "soilgrids_soc_0-30cm_ssa.tif",      # ✅ GOOD DATA - 43.9% valid coverage
        'soil_sand': soil_dir / "soilgrids_sand_0-5cm_ssa.tif",
        'soil_clay': soil_dir / "soilgrids_clay_0-5cm_ssa.tif",
        
        # GloSEM erosion data - prefer 1.3 (2019) if available, fallback to 1.1 (2012)
        'erosion_2019': glosem_13_dir / "RUSLE_SoilLoss_v1.3_yr2019_250m.tif",      # Preferred - GloSEM 1.3
        'erosion_2012': glosem_dir / "RUSLE_SoilLoss_v1.1_yr2012_25km.tif",        # Fallback - GloSEM 1.1
        'erosion_cfactor': glosem_dir / "RUSLE_CFactor_yr2012_v1.1_25km.tif",      # Current available
        'erosion_rfactor': glosem_dir / "RUSLE_RFactor_v1.1_25km.tif"              # Current available
    }
    
    return paths, raster_files

def load_base_data(paths):
    """Load Atlas master data and administrative boundaries."""
    print("📊 Loading Atlas master data and administrative boundaries...")
    
    try:
        # Load cleaned Atlas data
        df = pd.read_csv(paths['atlas_data'])
        print(f"   ✅ Loaded Atlas data: {len(df):,} records")
        
        # Load administrative boundaries if available
        try:
            boundaries = gpd.read_file(paths['boundaries'])
            print(f"   ✅ Loaded admin boundaries: {len(boundaries):,} features")
            print(f"   📋 Boundary columns: {list(boundaries.columns)}")
            return df, boundaries
        except FileNotFoundError:
            print(f"   ⚠️  Admin boundaries not found: {paths['boundaries']}")
            print(f"   � Will use placeholder environmental data instead")
            return df, None
        
    except FileNotFoundError as e:
        print(f"❌ ERROR: Could not find required Atlas data file.")
        print(f"   Missing file: {e.filename}")
        print(f"   Please ensure you've run the Atlas data pipeline first.")
        raise

def process_raster_data(df, boundaries, paths):
    """
    Process SoilGrids and GloSEM raster data using proper zonal statistics.
    
    Note: This processes actual environmental data with coordinate system handling.
    """
    print("🌍 Processing environmental raster data...")
    
    # Check which raster files are available
    available_rasters = {}
    for key, filepath in paths['raster_files'].items():
        if filepath.exists():
            available_rasters[key] = filepath
            print(f"   ✅ Found: {key} - {filepath.name}")
        else:
            print(f"   ⚠️  Missing: {key} - {filepath.name}")
    
    if not available_rasters:
        print("   ❌ No environmental raster files found!")
        print("   Please ensure SoilGrids and GloSEM data is downloaded")
        return add_placeholder_environmental_data(df)
    
    # Use zonal statistics if boundaries are available
    if boundaries is not None:
        return process_raster_with_boundaries(df, boundaries, available_rasters)
    else:
        print("   ⚠️  No admin boundaries - using simulated environmental data")
        return add_placeholder_environmental_data(df)

def add_placeholder_environmental_data(df):
    """Add placeholder environmental data when raster processing isn't available."""
    print("   📊 Adding placeholder environmental indicators...")
    
    # Add placeholder soil health indicators based on 2017 SoilGrids ranges
    np.random.seed(42)  # For reproducible placeholder data
    n_records = len(df)
    
    # Simulate soil health indicators based on actual SoilGrids data ranges
    df['soil_ph_mean'] = np.random.normal(29.7, 10.0, n_records).clip(10.0, 80.0)    # pH*10 scale
    df['soil_soc_mean'] = np.random.normal(116.3, 40.0, n_records).clip(20.0, 500.0) # SOC g/kg
    df['soil_sand_mean'] = np.random.normal(238, 50, n_records).clip(50, 600)        # Sand content
    df['soil_clay_mean'] = np.random.normal(105, 30, n_records).clip(20, 400)       # Clay content
    df['erosion_2012_mean'] = np.random.exponential(2.8, n_records).clip(0.1, 50.0) # Soil loss t/ha/yr
    
    # Add erosion factors for comprehensive analysis
    df['erosion_cfactor_mean'] = np.random.beta(2, 10, n_records) * 0.5  # Cover factor 0-0.5
    df['erosion_rfactor_mean'] = np.random.exponential(2300, n_records).clip(100, 20000)  # Rainfall erosivity
    
    print(f"   ✅ Added placeholder soil indicators to {len(df):,} records")
    print(f"   📋 Variables: pH, SOC, Sand%, Clay%, Erosion Rate, Cover Factor, Rainfall Erosivity")
    return df

def process_raster_with_boundaries(df, boundaries, raster_files):
    """Process raster data using zonal statistics with admin boundaries."""
    import rasterio
    from rasterstats import zonal_stats
    
    print("   🗺️  Processing raster data with zonal statistics...")
    
    # Ensure boundaries are in EPSG:4326 for consistency
    if boundaries.crs != 'EPSG:4326':
        print(f"   🔄 Reprojecting boundaries from {boundaries.crs} to EPSG:4326")
        boundaries = boundaries.to_crs('EPSG:4326')
    
    # Normalize country names for consistent merging (especially Congo)
    boundaries['admin0_name_normalized'] = boundaries['admin0_name'].replace({
        'Congo - Kinshasa': 'Democratic Republic of the Congo',
        'Congo - Brazzaville': 'Republic of the Congo'
    })
    
    # Create comprehensive admin identifier for robust merging
    boundaries['merge_key'] = (
        boundaries['admin0_name_normalized'].astype(str) + '|' + 
        boundaries['admin1_name'].astype(str) + '|' + 
        boundaries['admin2_name'].astype(str)
    )
    
    # Process each raster file
    for raster_key, raster_path in raster_files.items():
        print(f"   📈 Processing {raster_key}...")
        
        try:
            # Check if raster needs reprojection
            with rasterio.open(raster_path) as src:
                raster_crs = src.crs.to_string()
                print(f"      Raster CRS: {raster_crs}")
                
                # Handle coordinate system differences
                if raster_crs == 'EPSG:4326':
                    # Both in WGS84 - direct processing
                    boundaries_for_zonal = boundaries
                    print(f"      ✅ Using WGS84 coordinates for {raster_key}")
                elif 'ESRI:54009' in raster_crs:
                    print(f"      ⚠️  SoilGrids data in ESRI:54009 - reprojecting boundaries")
                    boundaries_for_zonal = boundaries.to_crs(raster_crs)
                else:
                    print(f"      🔄 Reprojecting boundaries to match {raster_crs}")
                    boundaries_for_zonal = boundaries.to_crs(raster_crs)
                
                # Calculate zonal statistics with error handling
                try:
                    stats = zonal_stats(
                        boundaries_for_zonal.geometry,
                        raster_path,
                        stats=['mean', 'min', 'max', 'std', 'count'],
                        nodata=src.nodata,
                        all_touched=True  # Include pixels that touch boundaries
                    )
                    
                    # Add statistics to boundaries
                    for stat_name in ['mean', 'min', 'max', 'std', 'count']:
                        col_name = f"{raster_key}_{stat_name}"
                        boundaries[col_name] = [s[stat_name] if s and s[stat_name] is not None else np.nan for s in stats]
                    
                    valid_stats = sum(1 for s in stats if s and s.get('mean') is not None)
                    print(f"      ✅ Added {raster_key} statistics ({valid_stats}/{len(stats)} valid)")
                    
                except Exception as e:
                    print(f"      ❌ Zonal statistics failed for {raster_key}: {str(e)}")
                    # Add NaN columns as placeholders
                    for stat_name in ['mean', 'min', 'max', 'std', 'count']:
                        col_name = f"{raster_key}_{stat_name}"
                        boundaries[col_name] = np.nan
                
        except Exception as e:
            print(f"      ❌ Error processing {raster_key}: {str(e)}")
            continue
    
    # Merge with atlas data using flexible matching
    print("   🔗 Merging environmental data with Atlas data...")
    
    # Create merge keys for both datasets
    df['atlas_merge_key'] = df['country'].astype(str) + '|' + df['region'].astype(str) + '|' + df['sub_region'].astype(str)
    
    # Get environmental columns
    env_cols = [col for col in boundaries.columns if any(
        raster_key in col for raster_key in raster_files.keys()
    )]
    
    # Prepare boundary data for merging
    boundary_merge_data = boundaries[['admin0_name', 'admin1_name', 'admin2_name', 'merge_key'] + env_cols].copy()
    boundary_merge_data['boundary_merge_key'] = boundary_merge_data['merge_key']
    
    # Try direct merge first
    df_merged = df.merge(
        boundary_merge_data[['boundary_merge_key'] + env_cols],
        left_on='atlas_merge_key',
        right_on='boundary_merge_key',
        how='left'
    )
    
    successful_merges = df_merged[env_cols[0]].notna().sum() if env_cols else 0
    print(f"   📊 Direct merge: {successful_merges}/{len(df)} records matched")
    
    # For unmatched records, try alternative matching strategies
    if successful_merges < len(df) * 0.9:  # If less than 90% matched
        print("   🔄 Applying fuzzy matching for remaining records...")
        
        # Alternative matching: just country + sub_region (skip region)
        unmatched_mask = df_merged[env_cols[0]].isna() if env_cols else pd.Series([True] * len(df_merged))
        unmatched_df = df[unmatched_mask]
        
        for idx, row in unmatched_df.iterrows():
            # Try matching on country and sub_region only
            country_matches = boundary_merge_data[
                boundary_merge_data['admin0_name'].str.contains(row['country'], case=False, na=False) |
                boundary_merge_data['admin0_name'].str.replace(' ', '').str.contains(row['country'].replace(' ', ''), case=False, na=False)
            ]
            
            if len(country_matches) > 0:
                subregion_matches = country_matches[
                    country_matches['admin2_name'].str.contains(row['sub_region'], case=False, na=False) |
                    country_matches['admin2_name'].str.replace(' ', '').str.contains(row['sub_region'].replace(' ', ''), case=False, na=False)
                ]
                
                if len(subregion_matches) > 0:
                    # Use first match
                    match = subregion_matches.iloc[0]
                    for col in env_cols:
                        if col in match:
                            df_merged.loc[idx, col] = match[col]
    
    final_matches = df_merged[env_cols[0]].notna().sum() if env_cols else len(df_merged)
    print(f"   ✅ Final merge: {final_matches}/{len(df)} records with environmental data ({final_matches/len(df)*100:.1f}%)")
    
    return df_merged

def calculate_environmental_vulnerability(df):
    """Calculate environmental vulnerability scores from soil health indicators."""
    print("🧮 Calculating environmental vulnerability scores...")
    
    # Environmental vulnerability components (higher = more vulnerable)
    
    # 1. pH vulnerability (SoilGrids scale: 0-101, where ~65 = pH 6.5)
    if 'soil_ph_mean' in df.columns:
        # Convert SoilGrids pH scale to vulnerability (optimal pH ~65)
        df['ph_vulnerability'] = np.abs(df['soil_ph_mean'] - 65) / 50  # Distance from optimal
        df['ph_vulnerability'] = df['ph_vulnerability'].clip(0, 1)
    
    # 2. SOC vulnerability (low SOC = high vulnerability)
    if 'soil_soc_mean' in df.columns:
        # SOC in g/kg - lower values indicate poor soil fertility
        # Typical range: 17-2144 g/kg, optimal >100 g/kg
        df['soc_vulnerability'] = 1 - (df['soil_soc_mean'] / df['soil_soc_mean'].quantile(0.9))
        df['soc_vulnerability'] = df['soc_vulnerability'].clip(0, 1)
    
    # 3. Soil texture vulnerability (extreme sand or clay is problematic)
    if 'soil_sand_mean' in df.columns and 'soil_clay_mean' in df.columns:
        # Normalize to 0-100 scale (SoilGrids uses per-mille scale)
        sand_pct = (df['soil_sand_mean'] / 10).clip(0, 100)  
        clay_pct = (df['soil_clay_mean'] / 10).clip(0, 100)
        
        # Balanced texture vulnerability (extreme sand or clay is bad)
        df['texture_vulnerability'] = np.maximum(
            (sand_pct - 50).clip(0, 50) / 50,  # High sand penalty
            (clay_pct - 30).clip(0, 70) / 70   # High clay penalty
        )
    
    # 4. Erosion vulnerability (2012 soil loss rates)
    if 'erosion_2012_mean' in df.columns:
        # High erosion = high vulnerability (>5 t/ha/yr is concerning)
        df['erosion_vulnerability'] = (df['erosion_2012_mean'] / 10).clip(0, 1)
        print("   ✅ Erosion data included in vulnerability assessment")
    
    # 5. Cover management vulnerability (C-factor: higher = less protection)
    if 'erosion_cfactor_mean' in df.columns:
        df['cover_vulnerability'] = df['erosion_cfactor_mean'] * 2  # Scale 0-0.5 to 0-1
        print("   ✅ Land cover protection factor included")
    
    # Collect available vulnerability components
    env_components = []
    component_names = []
    
    if 'ph_vulnerability' in df.columns:
        env_components.append('ph_vulnerability')
        component_names.append('pH')
    if 'soc_vulnerability' in df.columns:
        env_components.append('soc_vulnerability')
        component_names.append('SOC')
    if 'texture_vulnerability' in df.columns:
        env_components.append('texture_vulnerability')
        component_names.append('Texture')
    if 'erosion_vulnerability' in df.columns:
        env_components.append('erosion_vulnerability')
        component_names.append('Erosion')
    if 'cover_vulnerability' in df.columns:
        env_components.append('cover_vulnerability')
        component_names.append('Cover')
    
    if env_components:
        # Combined environmental vulnerability (mean of available components)
        df['environmental_vulnerability_score'] = df[env_components].mean(axis=1)
        print(f"   ✅ Using {len(env_components)} vulnerability components: {', '.join(component_names)}")
    else:
        # Fallback if no soil data available
        print("   ⚠️  No soil data available - using uniform low vulnerability")
        df['environmental_vulnerability_score'] = 0.3
    
    vuln_range = df['environmental_vulnerability_score']
    print(f"   ✅ Environmental vulnerability range: {vuln_range.min():.3f} - {vuln_range.max():.3f}")
    return df

def calculate_compound_risk(df):
    """Calculate final compound risk scores combining all vulnerability factors."""
    print("⚡ Calculating compound risk scores...")
    
    # Combined vulnerability (social + environmental)
    df['combined_vulnerability_score'] = (
        df['social_vulnerability_score'] + 
        df['environmental_vulnerability_score']
    ) / 2
    
    # Final compound risk: Risk = Hazard × Combined_Vulnerability
    df['compound_risk_score'] = (
        df['hazard_score'] * df['combined_vulnerability_score']
    )
    
    # Normalize to 0-1 scale
    df['compound_risk_score'] = df['compound_risk_score'] / df['compound_risk_score'].max()
    
    print(f"   ✅ Compound risk range: {df['compound_risk_score'].min():.3f} - {df['compound_risk_score'].max():.3f}")
    return df

def identify_hotspots(df, top_n=20):
    """Identify and analyze top risk hotspots."""
    print(f"🔥 Identifying top {top_n} risk hotspots...")
    
    # Sort by compound risk score
    hotspots = df.nlargest(top_n, 'compound_risk_score')
    
    print("\n" + "="*80)
    print("🎯 TOP RISK HOTSPOTS")
    print("="*80)
    
    hotspot_summary = hotspots[[
        'country', 'region', 'sub_region', 
        'compound_risk_score', 'hazard_score', 'combined_vulnerability_score',
        'population', 'vop_crops_usd'
    ]].round(3)
    
    print(hotspot_summary.to_string(index=False))
    print("="*80)
    
    return hotspots

def export_results(df, hotspots, paths):
    """Export processed datasets for visualization and further analysis."""
    print("💾 Exporting processed datasets...")
    
    # Export main dataset
    viz_columns = [
        'country', 'region', 'sub_region',
        'hazard_score', 'social_vulnerability_score', 'environmental_vulnerability_score',
        'combined_vulnerability_score', 'compound_risk_score',
        'population', 'vop_crops_usd', 'ndws_future_days', 'poverty_headcount_ratio'
    ]
    
    # Add available soil indicators
    soil_columns = ['soil_ph_mean', 'soil_soc_mean', 'soil_sand_mean', 'soil_clay_mean', 
                   'erosion_2012_mean', 'erosion_cfactor_mean', 'erosion_rfactor_mean']
    available_soil_cols = [col for col in soil_columns if col in df.columns]
    viz_columns.extend(available_soil_cols)
    
    # Export main dataset
    output_file = paths['processed_data'] / "compound_risk_assessment.csv"
    df[viz_columns].to_csv(output_file, index=False)
    print(f"   ✅ Main dataset: {output_file}")
    
    # Export hotspots
    hotspots_file = paths['processed_data'] / "risk_hotspots_top20.csv"
    hotspots[viz_columns].to_csv(hotspots_file, index=False)
    print(f"   ✅ Risk hotspots: {hotspots_file}")
    
    # Export summary statistics
    summary_stats = {
        'total_records': len(df),
        'countries_covered': df['country'].nunique(),
        'regions_covered': df['region'].nunique(),
        'subregions_covered': df['sub_region'].nunique(),
        'mean_compound_risk': float(df['compound_risk_score'].mean()),
        'max_compound_risk': float(df['compound_risk_score'].max()),
        'high_risk_threshold': 0.7,
        'high_risk_areas': int((df['compound_risk_score'] > 0.7).sum()),
        'total_population_at_risk': int(df[df['compound_risk_score'] > 0.7]['population'].sum()),
        'total_agricultural_value_at_risk': float(df[df['compound_risk_score'] > 0.7]['vop_crops_usd'].sum())
    }
    
    summary_file = paths['processed_data'] / "risk_assessment_summary.json"
    import json
    with open(summary_file, 'w') as f:
        json.dump(summary_stats, f, indent=2)
    print(f"   ✅ Summary statistics: {summary_file}")
    
    return summary_stats

def main():
    """Main execution function for geospatial processing and risk calculation."""
    print("🌍 STEP 2: GEOSPATIAL PROCESSING & COMPOUND RISK CALCULATION")
    print("="*70)
    print("📋 Integrating Atlas socio-economic data with SoilGrids environmental data")
    print("🎯 Goal: Generate compound risk assessment for Sub-Saharan Africa")
    print()
    
    try:
        # Setup paths and verify files
        paths, raster_files = setup_paths()
        
        # Load base Atlas data
        df, boundaries = load_base_data(paths)
        
        # Process environmental raster data
        df = process_raster_data(df, boundaries, {'raster_files': raster_files, **paths})
        
        # Calculate environmental vulnerability
        df = calculate_environmental_vulnerability(df)
        
        # Calculate compound risk scores
        df = calculate_compound_risk(df)
        
        # Identify hotspots
        hotspots = identify_hotspots(df)
        
        # Export results
        summary_stats = export_results(df, hotspots, paths)
        
        # Final summary
        print("\n" + "🎉 GEOSPATIAL PROCESSING COMPLETE!")
        print("="*70)
        print(f"📊 Processed {summary_stats['total_records']:,} sub-regions")
        print(f"🌍 Coverage: {summary_stats['countries_covered']} countries")
        print(f"⚡ High-risk areas: {summary_stats['high_risk_areas']} (threshold > 0.7)")
        print(f"👥 Population at risk: {summary_stats['total_population_at_risk']:,}")
        print(f"💰 Agricultural value at risk: ${summary_stats['total_agricultural_value_at_risk']:,.0f}")
        print("\n🚀 Ready for Observable Framework visualization!")
        print("="*70)
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        print("Please check the error message above and ensure all prerequisites are met.")
        return False
    
    return True

if __name__ == "__main__":
    # Import numpy here to avoid issues if not available
    import numpy as np
    main()