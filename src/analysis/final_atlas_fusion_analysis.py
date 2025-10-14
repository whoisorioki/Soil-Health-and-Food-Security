#!/usr/bin/env python3
"""
FINAL ATLAS FUSION ANALYSIS
===========================

This is the definitive, all-in-one script for the Soil Health and Food Security project.
It implements a 100% Atlas-based workflow using only clean, pre-harmonized CSV data
from the Adaptation Atlas Explorer.

Data Sources (5 Atlas CSV files):
1. atlas_hazard_ndws_future.csv - Number of Days of Water Stress (future)
2. atlas_hazard_erosion_proxy.csv - Thornthwaite's Aridity Index (TAI) as erosion proxy
3. atlas_exposure_population.csv - Population exposure data
4. atlas_exposure_vop_crops.csv - Value of Production (crops)
5. atlas_adaptive_capacity_poverty.csv - Poverty headcount ratios

Risk Formula: Risk = Hazard × Vulnerability
Where: Vulnerability = f(Social_Vulnerability, Environmental_Vulnerability)

Author: Atlas Data Fusion Pipeline
Date: October 2025
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
import json
from typing import Dict, Tuple, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AtlasFusionPipeline:
    """Complete Atlas data fusion and risk assessment pipeline"""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize the fusion pipeline"""
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        self.processed_dir.mkdir(exist_ok=True)
        
        # Administrative boundary columns for joining
        self.admin_cols = ['admin0_name', 'admin1_name', 'admin2_name']
        
        # Standardized output columns
        self.output_cols = ['country', 'region', 'sub_region']
        
        logger.info("Atlas Fusion Pipeline initialized")
    
    def load_atlas_datasets(self) -> Dict[str, pd.DataFrame]:
        """Load all five Atlas CSV datasets"""
        
        datasets = {}
        
        # Define the five core Atlas datasets
        atlas_files = {
            'hazard_ndws': 'atlas_hazard_ndws_future.csv',
            'hazard_erosion': 'atlas_hazard_erosion_proxy.csv', 
            'exposure_population': 'atlas_exposure_population.csv',
            'exposure_vop': 'atlas_exposure_vop_crops.csv',
            'adaptive_capacity': 'atlas_adaptive_capacity_poverty.csv'
        }
        
        logger.info("Loading Atlas datasets...")
        
        for name, filename in atlas_files.items():
            file_path = self.raw_dir / filename
            if file_path.exists():
                df = pd.read_csv(file_path)
                datasets[name] = df
                logger.info(f"✅ Loaded {name}: {len(df):,} records from {filename}")
            else:
                logger.error(f"❌ Missing file: {filename}")
                raise FileNotFoundError(f"Required Atlas file not found: {filename}")
        
        return datasets
    
    def standardize_admin_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize administrative boundary column names"""
        
        # Rename admin columns to standard output format
        rename_map = {
            'admin0_name': 'country',
            'admin1_name': 'region', 
            'admin2_name': 'sub_region'
        }
        
        df_std = df.copy()
        for old_col, new_col in rename_map.items():
            if old_col in df_std.columns:
                df_std = df_std.rename(columns={old_col: new_col})
        
        return df_std
    
    def process_hazard_ndws(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process Number of Days of Water Stress data"""
        
        logger.info("Processing NDWS hazard data...")
        
        # Filter for moderate future projections (ssp245 recommended over rcp45)
        df_filtered = df[
            (df['scenario'] == 'ssp245') & 
            (df['timeframe'] == '2041_2060')
        ].copy()
        
        logger.info(f"Filtered NDWS data: {len(df_filtered):,} records from {len(df):,} total")
        
        # Select and rename columns
        result = df_filtered[self.admin_cols + ['value']].copy()
        result = result.rename(columns={'value': 'ndws_future_days'})
        
        # Standardize admin columns
        result = self.standardize_admin_columns(result)
        
        logger.info(f"✅ NDWS processed: {len(result):,} regions")
        return result
    
    def process_hazard_erosion(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process Thornthwaite's Aridity Index as erosion proxy"""
        
        logger.info("Processing TAI erosion proxy data...")
        
        # Filter for baseline/historic data
        df_filtered = df[
            (df['scenario'] == 'historic') & 
            (df['timeframe'] == 'historic') &
            (df['hazard'] == 'TAI')
        ].copy()
        
        # Select and rename columns
        result = df_filtered[self.admin_cols + ['value']].copy()
        result = result.rename(columns={'value': 'tai_erosion_proxy'})
        
        # Standardize admin columns
        result = self.standardize_admin_columns(result)
        
        logger.info(f"✅ TAI erosion proxy processed: {len(result):,} regions")
        return result
    
    def process_exposure_population(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process population exposure data with scenario filtering"""
        
        logger.info("Processing population exposure data...")
        
        # Check if we need to filter by scenario (some datasets have multiple scenarios)
        if 'scenario' in df.columns:
            scenarios = df['scenario'].unique()
            logger.info(f"Population scenarios available: {list(scenarios)}")
            
            # Prefer ssp245 scenario if available, otherwise use first available
            if 'ssp245' in scenarios:
                df_filtered = df[df['scenario'] == 'ssp245'].copy()
                logger.info(f"Using ssp245 scenario: {len(df_filtered):,} records")
            else:
                # Use most common scenario
                most_common_scenario = df['scenario'].value_counts().index[0]
                df_filtered = df[df['scenario'] == most_common_scenario].copy()
                logger.info(f"Using {most_common_scenario} scenario: {len(df_filtered):,} records")
        else:
            df_filtered = df.copy()
            logger.info("No scenario filtering needed")
        
        # Select relevant columns
        result = df_filtered[self.admin_cols + ['value']].copy()
        result = result.rename(columns={'value': 'population_total'})
        
        # Standardize admin columns
        result = self.standardize_admin_columns(result)
        
        logger.info(f"✅ Population processed: {len(result):,} regions")
        return result
    
    def process_exposure_vop(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process Value of Production (crops) data with aggregation"""
        
        logger.info("Processing VOP crops exposure data...")
        logger.info(f"Input VOP data: {len(df):,} records across {df['crop'].nunique()} crop types")
        
        # Aggregate VOP across all crops by region (sum total agricultural value)
        vop_aggregated = df.groupby(self.admin_cols)['value'].sum().reset_index()
        vop_aggregated = vop_aggregated.rename(columns={'value': 'vop_crops_usd'})
        
        logger.info(f"Aggregated VOP data: {len(vop_aggregated):,} regions")
        
        # Standardize admin columns
        result = self.standardize_admin_columns(vop_aggregated)
        
        logger.info(f"✅ VOP crops processed: {len(result):,} regions")
        return result
    
    def process_adaptive_capacity(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process poverty headcount ratio data with missing value handling"""
        
        logger.info("Processing adaptive capacity (poverty) data...")
        
        # Check for scenarios and filter if needed
        if 'scenario' in df.columns:
            scenarios = df['scenario'].unique()
            logger.info(f"Poverty scenarios available: {list(scenarios)}")
            
            # Use baseline/historic scenario if available
            if 'baseline' in scenarios:
                df_filtered = df[df['scenario'] == 'baseline'].copy()
            elif 'historic' in scenarios:
                df_filtered = df[df['scenario'] == 'historic'].copy()
            else:
                # Use most complete scenario (fewest missing values)
                scenario_completeness = {}
                for scenario in scenarios:
                    scenario_data = df[df['scenario'] == scenario]
                    completeness = scenario_data['value'].notna().sum() / len(scenario_data)
                    scenario_completeness[scenario] = completeness
                
                best_scenario = max(scenario_completeness.keys(), key=lambda x: scenario_completeness[x])
                df_filtered = df[df['scenario'] == best_scenario].copy()
                logger.info(f"Using most complete scenario '{best_scenario}': {scenario_completeness[best_scenario]:.1%} completeness")
        else:
            df_filtered = df.copy()
        
        # Select relevant columns
        result = df_filtered[self.admin_cols + ['value']].copy()
        result = result.rename(columns={'value': 'poverty_headcount_ratio'})
        
        # Standardize admin columns
        result = self.standardize_admin_columns(result)
        
        # Log missing data information
        missing_count = result['poverty_headcount_ratio'].isnull().sum()
        missing_pct = missing_count / len(result) * 100
        logger.info(f"Poverty data missing: {missing_count:,} regions ({missing_pct:.1f}%)")
        
        logger.info(f"✅ Poverty data processed: {len(result):,} regions")
        return result
    
    def fuse_all_datasets(self, datasets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Fuse all processed datasets using smart merging strategy"""
        
        logger.info("Fusing all Atlas datasets with missing data handling...")
        
        # Process each dataset
        processed = {}
        processed['ndws'] = self.process_hazard_ndws(datasets['hazard_ndws'])
        processed['erosion'] = self.process_hazard_erosion(datasets['hazard_erosion'])
        processed['population'] = self.process_exposure_population(datasets['exposure_population'])
        processed['vop'] = self.process_exposure_vop(datasets['exposure_vop'])
        processed['poverty'] = self.process_adaptive_capacity(datasets['adaptive_capacity'])
        
        # Log dataset sizes before fusion
        logger.info("Dataset sizes before fusion:")
        for name, df in processed.items():
            logger.info(f"  {name}: {len(df):,} regions")
        
        # Strategy: Use INNER joins to ensure complete data for risk calculation
        # Start with the datasets that have the cleanest 1:1 mapping
        
        # Step 1: Start with TAI erosion data (cleanest 1:1 mapping)
        master = processed['erosion'].copy()
        logger.info(f"Base dataset (TAI erosion): {len(master):,} regions")
        
        # Step 2: Inner join with NDWS (should have same regions)
        master = master.merge(
            processed['ndws'], 
            on=self.output_cols, 
            how='inner',
            suffixes=('', '_ndws')
        )
        logger.info(f"After NDWS inner join: {len(master):,} regions")
        
        # Step 3: Inner join with VOP (aggregated data)
        master = master.merge(
            processed['vop'], 
            on=self.output_cols, 
            how='inner',
            suffixes=('', '_vop')
        )
        logger.info(f"After VOP inner join: {len(master):,} regions")
        
        # Step 4: Left join with population (keep all, fill missing with 0)
        master = master.merge(
            processed['population'], 
            on=self.output_cols, 
            how='left',
            suffixes=('', '_pop')
        )
        # Fill missing population with 0 (uninhabited areas)
        master['population_total'] = master['population_total'].fillna(0)
        logger.info(f"After population left join: {len(master):,} regions")
        
        # Step 5: Left join with poverty data (handle missing values)
        master = master.merge(
            processed['poverty'], 
            on=self.output_cols, 
            how='left',
            suffixes=('', '_poverty')
        )
        
        # Handle missing poverty data strategically
        initial_missing = master['poverty_headcount_ratio'].isnull().sum()
        logger.info(f"Missing poverty data before handling: {initial_missing:,} regions")
        
        if initial_missing > 0:
            # Mark which rows had missing poverty data before imputation
            missing_poverty_mask = master['poverty_headcount_ratio'].isnull()
            
            # Fill missing poverty data with country median, then regional median, then global median
            logger.info("Applying hierarchical imputation for missing poverty data...")
            
            # Country-level imputation
            country_medians = master.groupby('country')['poverty_headcount_ratio'].median()
            master['poverty_headcount_ratio'] = master.groupby('country')['poverty_headcount_ratio'].transform(
                lambda x: x.fillna(x.median())
            )
            
            # Still missing? Use global median
            global_median = master['poverty_headcount_ratio'].median()
            master['poverty_headcount_ratio'] = master['poverty_headcount_ratio'].fillna(global_median)
            
            final_missing = master['poverty_headcount_ratio'].isnull().sum()
            logger.info(f"Missing poverty data after imputation: {final_missing:,} regions")
            
            # Add imputation flag - mark specific rows that were imputed
            master['poverty_imputed'] = missing_poverty_mask
        else:
            # No imputation needed
            master['poverty_imputed'] = False
        
        logger.info(f"✅ Master dataset created: {len(master):,} regions with complete data")
        
        # Final data quality check
        critical_cols = ['ndws_future_days', 'tai_erosion_proxy', 'vop_crops_usd', 'population_total', 'poverty_headcount_ratio']
        missing_summary = {}
        for col in critical_cols:
            if col in master.columns:
                missing_count = master[col].isnull().sum()
                missing_summary[col] = missing_count
                if missing_count > 0:
                    logger.warning(f"⚠️ {col}: {missing_count:,} missing values remain")
                else:
                    logger.info(f"✅ {col}: Complete data")
        
        return master
    
    def calculate_risk_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate comprehensive risk scores"""
        
        logger.info("Calculating risk scores...")
        
        result = df.copy()
        
        # 1. Normalize hazard indicators (0-1 scale, higher = more hazardous)
        if 'ndws_future_days' in result.columns:
            result['hazard_water_stress'] = self._normalize_to_risk(result['ndws_future_days'])
        
        if 'tai_erosion_proxy' in result.columns:
            # Higher TAI = more arid = higher erosion risk
            result['hazard_erosion_risk'] = self._normalize_to_risk(result['tai_erosion_proxy'])
        
        # 2. Combine hazards into composite score
        hazard_cols = [col for col in result.columns if col.startswith('hazard_')]
        if hazard_cols:
            result['hazard_score_composite'] = result[hazard_cols].mean(axis=1, skipna=True)
        
        # 3. Normalize vulnerability indicators (0-1 scale, higher = more vulnerable)
        if 'poverty_headcount_ratio' in result.columns:
            result['social_vulnerability'] = result['poverty_headcount_ratio']  # Already 0-1
        
        # 4. Environmental vulnerability (erosion proxy)
        if 'hazard_erosion_risk' in result.columns:
            result['environmental_vulnerability'] = result['hazard_erosion_risk']
        
        # 5. Combined vulnerability score
        vuln_cols = ['social_vulnerability', 'environmental_vulnerability']
        vuln_cols = [col for col in vuln_cols if col in result.columns]
        if vuln_cols:
            result['vulnerability_composite'] = result[vuln_cols].mean(axis=1, skipna=True)
        
        # 6. Final compound risk score: Risk = Hazard × Vulnerability
        if 'hazard_score_composite' in result.columns and 'vulnerability_composite' in result.columns:
            result['compound_risk_score'] = (
                result['hazard_score_composite'] * result['vulnerability_composite']
            )
        
        # 7. Risk categorization
        if 'compound_risk_score' in result.columns:
            result['risk_category'] = pd.cut(
                result['compound_risk_score'],
                bins=[0, 0.25, 0.5, 0.75, 1.0],
                labels=['Low', 'Moderate', 'High', 'Very High'],
                include_lowest=True
            )
        
        logger.info("✅ Risk scores calculated")
        return result
    
    def _normalize_to_risk(self, series: pd.Series) -> pd.Series:
        """Normalize a series to 0-1 risk scale (higher = more risky)"""
        
        clean_series = series.dropna()
        if len(clean_series) == 0:
            return series
        
        min_val = clean_series.min()
        max_val = clean_series.max()
        
        if max_val == min_val:
            return pd.Series(0.5, index=series.index)  # Constant value
        
        # Linear normalization to 0-1
        normalized = (series - min_val) / (max_val - min_val)
        return normalized.clip(0, 1)
    
    def add_metadata_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add useful metadata columns"""
        
        logger.info("Adding metadata columns...")
        
        result = df.copy()
        
        # Country statistics
        if 'population_total' in result.columns:
            country_pop = result.groupby('country')['population_total'].sum()
            result['country_population'] = result['country'].map(country_pop)
            result['population_share'] = (
                result['population_total'] / result['country_population']
            ).round(4)
        
        if 'vop_crops_usd' in result.columns:
            country_vop = result.groupby('country')['vop_crops_usd'].sum()
            result['country_vop_total'] = result['country'].map(country_vop)
            result['vop_share'] = (
                result['vop_crops_usd'] / result['country_vop_total']
            ).round(4)
        
        # Regional rankings (handle NaN values properly)
        if 'compound_risk_score' in result.columns:
            result['risk_rank_national'] = (
                result.groupby('country')['compound_risk_score']
                .rank(method='dense', ascending=False, na_option='bottom')
                .fillna(999)  # Assign high rank number to missing values
                .astype(int)
            )
            
            result['risk_rank_continental'] = (
                result['compound_risk_score']
                .rank(method='dense', ascending=False, na_option='bottom')
                .fillna(999)  # Assign high rank number to missing values
                .astype(int)
            )
        
        logger.info("✅ Metadata columns added")
        return result
    
    def generate_summary_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate comprehensive summary statistics"""
        
        logger.info("Generating summary statistics...")
        
        stats: Dict[str, Any] = {
            'dataset_info': {
                'total_regions': len(df),
                'total_countries': df['country'].nunique(),
                'processing_date': pd.Timestamp.now().isoformat(),
                'data_sources': [
                    'atlas_hazard_ndws_future.csv',
                    'atlas_hazard_erosion_proxy.csv',
                    'atlas_exposure_population.csv', 
                    'atlas_exposure_vop_crops.csv',
                    'atlas_adaptive_capacity_poverty.csv'
                ]
            }
        }
        
        # Coverage statistics
        key_columns = [
            'ndws_future_days', 'tai_erosion_proxy', 'population_total',
            'vop_crops_usd', 'poverty_headcount_ratio', 'compound_risk_score'
        ]
        
        coverage = {}
        for col in key_columns:
            if col in df.columns:
                coverage[col] = {
                    'total_records': len(df),
                    'non_null_records': df[col].notna().sum(),
                    'coverage_percentage': round(df[col].notna().sum() / len(df) * 100, 1),
                    'missing_records': df[col].isna().sum()
                }
        
        stats['data_coverage'] = coverage
        
        # Risk distribution
        if 'risk_category' in df.columns:
            risk_dist = df['risk_category'].value_counts().to_dict()
            stats['risk_distribution'] = risk_dist
        
        # Top risk regions
        if 'compound_risk_score' in df.columns:
            top_risk_df = df.nlargest(20, 'compound_risk_score')[
                ['country', 'region', 'sub_region', 'compound_risk_score']
            ]
            # Convert to list of dictionaries for JSON serialization
            stats['top_risk_regions'] = top_risk_df.to_dict('records')
        
        # Country-level summaries
        country_summary = []
        for country in df['country'].unique():
            country_data = df[df['country'] == country]
            
            summary = {
                'country': country,
                'total_regions': len(country_data),
                'total_population': float(country_data['population_total'].sum()) if 'population_total' in df.columns else None,
                'total_vop': float(country_data['vop_crops_usd'].sum()) if 'vop_crops_usd' in df.columns else None,
                'avg_risk_score': float(country_data['compound_risk_score'].mean()) if 'compound_risk_score' in df.columns else None,
                'high_risk_regions': len(country_data[
                    country_data['risk_category'].isin(['High', 'Very High'])
                ]) if 'risk_category' in df.columns else None
            }
            
            country_summary.append(summary)
        
        # Sort by average risk score (handle None values)
        stats['country_summaries'] = sorted(
            country_summary, 
            key=lambda x: x['avg_risk_score'] if x['avg_risk_score'] is not None else 0, 
            reverse=True
        )
        
        logger.info("✅ Summary statistics generated")
        return stats
    
    def create_multi_level_aggregations(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Create separate datasets for country, region, and sub-region levels"""
        
        logger.info("Creating multi-level aggregations for visualization...")
        
        # Ensure we have the required columns
        required_cols = ['country', 'region', 'sub_region', 'compound_risk_score']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.warning(f"Missing columns for aggregation: {missing_cols}")
            return df, df, df
        
        # Sub-region level (original data with admin_level column)
        sub_region_df = df.copy()
        sub_region_df['admin_level'] = 'sub_region'
        sub_region_df['admin_name'] = sub_region_df['sub_region']
        
        # Region level aggregation
        logger.info("Aggregating to region level...")
        region_agg = df.groupby(['country', 'region']).agg({
            'population_total': 'sum',
            'vop_crops_usd': 'sum',  # Fixed column name
            'compound_risk_score': lambda x: np.average(x, weights=df.loc[x.index, 'population_total']) if 'population_total' in df.columns else x.mean(),
            'hazard_water_stress': 'mean',
            'hazard_erosion_risk': 'mean',
            'social_vulnerability': lambda x: np.average(x, weights=df.loc[x.index, 'population_total']) if 'population_total' in df.columns else x.mean(),
            'environmental_vulnerability': 'mean',
            'vulnerability_composite': lambda x: np.average(x, weights=df.loc[x.index, 'population_total']) if 'population_total' in df.columns else x.mean()
        }).reset_index()
        
        region_agg['sub_region'] = region_agg['region']  # For consistency
        region_agg['admin_level'] = 'region'
        region_agg['admin_name'] = region_agg['region']
        
        # Add risk categorization for regions
        if 'compound_risk_score' in region_agg.columns:
            region_agg['risk_category'] = pd.cut(
                region_agg['compound_risk_score'],
                bins=[0, 0.25, 0.5, 0.75, 1.0],
                labels=['Low', 'Moderate', 'High', 'Very High'],
                include_lowest=True
            )
        
        logger.info(f"✅ Region aggregation: {len(region_agg):,} regions")
        
        # Country level aggregation
        logger.info("Aggregating to country level...")
        country_agg = df.groupby(['country']).agg({
            'population_total': 'sum',
            'vop_crops_usd': 'sum',  # Fixed column name
            'compound_risk_score': lambda x: np.average(x, weights=df.loc[x.index, 'population_total']) if 'population_total' in df.columns else x.mean(),
            'hazard_water_stress': 'mean',
            'hazard_erosion_risk': 'mean',
            'social_vulnerability': lambda x: np.average(x, weights=df.loc[x.index, 'population_total']) if 'population_total' in df.columns else x.mean(),
            'environmental_vulnerability': 'mean',
            'vulnerability_composite': lambda x: np.average(x, weights=df.loc[x.index, 'population_total']) if 'population_total' in df.columns else x.mean()
        }).reset_index()
        
        country_agg['region'] = country_agg['country']  # For consistency
        country_agg['sub_region'] = country_agg['country']  # For consistency
        country_agg['admin_level'] = 'country'
        country_agg['admin_name'] = country_agg['country']
        
        # Add risk categorization for countries
        if 'compound_risk_score' in country_agg.columns:
            country_agg['risk_category'] = pd.cut(
                country_agg['compound_risk_score'],
                bins=[0, 0.25, 0.5, 0.75, 1.0],
                labels=['Low', 'Moderate', 'High', 'Very High'],
                include_lowest=True
            )
        
        logger.info(f"✅ Country aggregation: {len(country_agg):,} countries")
        
        return country_agg, region_agg, sub_region_df

    def save_outputs(self, df: pd.DataFrame, stats: Dict) -> None:
        """Save all outputs to processed directory with multi-level aggregations"""
        
        logger.info("Saving final outputs with multi-level aggregations...")
        
        # Create multi-level aggregations
        country_df, region_df, sub_region_df = self.create_multi_level_aggregations(df)
        
        # Save sub-region level (most detailed)
        sub_region_file = self.processed_dir / "atlas_sub_region_risk_assessment.csv"
        sub_region_df.to_csv(sub_region_file, index=False)
        logger.info(f"✅ Sub-region dataset saved: {sub_region_file} ({len(sub_region_df):,} records)")
        
        # Save region level
        region_file = self.processed_dir / "atlas_region_risk_assessment.csv"
        region_df.to_csv(region_file, index=False)
        logger.info(f"✅ Region dataset saved: {region_file} ({len(region_df):,} records)")
        
        # Save country level
        country_file = self.processed_dir / "atlas_country_risk_assessment.csv"
        country_df.to_csv(country_file, index=False)
        logger.info(f"✅ Country dataset saved: {country_file} ({len(country_df):,} records)")
        
        # Main combined dataset for reference
        output_file = self.processed_dir / "atlas_complete_risk_assessment.csv"
        df.to_csv(output_file, index=False)
        logger.info(f"✅ Complete dataset saved: {output_file} ({len(df):,} records)")
        
        # Summary statistics
        stats_file = self.processed_dir / "atlas_risk_assessment_summary.json"
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2, default=str)
        logger.info(f"✅ Summary statistics saved: {stats_file}")
        
        # High-risk regions for quick access
        if 'risk_category' in df.columns:
            high_risk = df[df['risk_category'].isin(['High', 'Very High'])].copy()
            high_risk_file = self.processed_dir / "atlas_high_risk_regions.csv"
            high_risk.to_csv(high_risk_file, index=False)
            logger.info(f"✅ High-risk regions saved: {high_risk_file} ({len(high_risk):,} records)")
        
        # Enhanced country summary with realistic figures
        if len(country_df) > 0:
            country_summary = country_df[['country', 'population_total', 'vop_crops_usd', 'compound_risk_score', 'risk_category']].copy()
            country_summary = country_summary.rename(columns={
                'population_total': 'total_population',
                'vop_crops_usd': 'total_ag_value_usd',  # Fixed column name
                'compound_risk_score': 'avg_risk_score'
            })
            country_summary_file = self.processed_dir / "atlas_country_summary.csv"
            country_summary.to_csv(country_summary_file, index=False)
            logger.info(f"✅ Country summary saved: {country_summary_file}")
    
    def run_complete_analysis(self) -> Tuple[pd.DataFrame, Dict]:
        """Execute the complete Atlas fusion and risk assessment pipeline"""
        
        logger.info("🚀 STARTING COMPLETE ATLAS FUSION ANALYSIS")
        logger.info("=" * 60)
        
        try:
            # Step 1: Load all datasets
            datasets = self.load_atlas_datasets()
            
            # Step 2: Fuse datasets
            master_df = self.fuse_all_datasets(datasets)
            
            # Validate we have data after fusion
            if len(master_df) == 0:
                logger.error("❌ No data after fusion - check dataset compatibility")
                raise ValueError("Fusion resulted in empty dataset")
            
            # Step 3: Calculate risk scores
            risk_df = self.calculate_risk_scores(master_df)
            
            # Step 4: Add metadata
            final_df = self.add_metadata_columns(risk_df)
            
            # Step 5: Validate realistic figures
            self.validate_realistic_figures(final_df)
            
            # Step 6: Generate statistics
            summary_stats = self.generate_summary_statistics(final_df)
            
            # Step 7: Save outputs with multi-level aggregations
            self.save_outputs(final_df, summary_stats)
            
            logger.info("🎉 ATLAS FUSION ANALYSIS COMPLETE!")
            logger.info("=" * 60)
            logger.info(f"Final dataset: {len(final_df):,} regions across {final_df['country'].nunique()} countries")
            logger.info("Multi-level outputs saved to data/processed/:")
            logger.info("  • atlas_country_risk_assessment.csv")
            logger.info("  • atlas_region_risk_assessment.csv") 
            logger.info("  • atlas_sub_region_risk_assessment.csv")
            logger.info("Ready for Observable Framework visualization!")
            
            return final_df, summary_stats
            
        except Exception as e:
            logger.error(f"❌ Analysis failed: {str(e)}")
            raise
    
    def validate_realistic_figures(self, df: pd.DataFrame) -> None:
        """Validate that figures are realistic and not showing N/A or unrealistic values"""
        
        logger.info("🔍 Validating realistic figures...")
        
        # Check for missing critical values
        critical_cols = ['compound_risk_score', 'population_total', 'vop_crops_usd']
        for col in critical_cols:
            if col in df.columns:
                missing_count = df[col].isnull().sum()
                missing_pct = missing_count / len(df) * 100
                
                if missing_pct > 10:
                    logger.warning(f"⚠️ High missing rate in {col}: {missing_pct:.1f}%")
                else:
                    logger.info(f"✅ {col}: {missing_pct:.1f}% missing (acceptable)")
        
        # Validate value ranges
        if 'compound_risk_score' in df.columns:
            risk_values = df['compound_risk_score'].dropna()
            if len(risk_values) > 0:
                logger.info(f"Risk score range: [{risk_values.min():.3f}, {risk_values.max():.3f}]")
                if risk_values.min() < 0 or risk_values.max() > 1:
                    logger.warning("⚠️ Risk scores outside expected [0,1] range")
        
        if 'population_total' in df.columns:
            pop_values = df['population_total'].dropna()
            if len(pop_values) > 0:
                logger.info(f"Population range: [{pop_values.min():,.0f}, {pop_values.max():,.0f}]")
                total_pop = pop_values.sum()
                logger.info(f"Total SSA population: {total_pop:,.0f}")
        
        if 'vop_crops_usd' in df.columns:
            vop_values = df['vop_crops_usd'].dropna()
            if len(vop_values) > 0:
                logger.info(f"VOP range: [${vop_values.min():,.0f}, ${vop_values.max():,.0f}]")
                total_vop = vop_values.sum()
                logger.info(f"Total SSA agricultural value: ${total_vop:,.0f}")
        
        logger.info("✅ Realistic figures validation complete")


def main():
    """Main execution function"""
    
    # Initialize and run the complete analysis
    pipeline = AtlasFusionPipeline()
    final_dataset, summary_statistics = pipeline.run_complete_analysis()
    
    # Display key results
    print("\n" + "="*60)
    print("FINAL RESULTS SUMMARY")
    print("="*60)
    
    print(f"📊 Total regions processed: {len(final_dataset):,}")
    print(f"🌍 Countries covered: {final_dataset['country'].nunique()}")
    
    if 'compound_risk_score' in final_dataset.columns:
        print(f"⚠️  Average risk score: {final_dataset['compound_risk_score'].mean():.3f}")
        print(f"🔺 Highest risk region: {final_dataset.loc[final_dataset['compound_risk_score'].idxmax(), 'sub_region']}")
    
    if 'risk_category' in final_dataset.columns:
        risk_counts = final_dataset['risk_category'].value_counts()
        print(f"\n📈 Risk Distribution:")
        for category, count in risk_counts.items():
            print(f"   {category}: {count:,} regions ({count/len(final_dataset)*100:.1f}%)")
    
    print("\n✅ Analysis complete! Check data/processed/ for output files.")


if __name__ == "__main__":
    main()