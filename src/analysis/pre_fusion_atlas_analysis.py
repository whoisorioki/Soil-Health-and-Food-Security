#!/usr/bin/env python3
"""
PRE-FUSION ATLAS DATA ANALYSIS
=============================

This script provides comprehensive analysis of all Atlas datasets BEFORE fusion.
It examines data quality, coverage, structure, and compatibility across datasets.

Current Data Strategy:
- We are using 100% Atlas-based workflow (no SoilGrids)
- All data comes from Adaptation Atlas Explorer
- TAI (Thornthwaite's Aridity Index) serves as our environmental/erosion proxy
- This eliminates complex geometric issues from external raster data

Atlas Datasets to Analyze:
1. atlas_hazard_ndws_future.csv - Climate hazard (water stress)
2. atlas_hazard_erosion_proxy.csv - Environmental hazard (TAI)
3. atlas_exposure_population.csv - Social exposure (population)
4. atlas_exposure_vop_crops.csv - Economic exposure (agricultural value)
5. atlas_adaptive_capacity_poverty.csv - Vulnerability (poverty)

Author: Pre-Fusion Analysis Pipeline
Date: October 2025
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import logging
from pathlib import Path
import json
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AtlasDataAnalyzer:
    """Comprehensive Atlas data analysis before fusion"""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize the analyzer"""
        self.data_dir = Path(data_dir)
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        self.processed_dir.mkdir(exist_ok=True)
        
        # Define our Atlas datasets
        self.atlas_files = {
            'hazard_ndws': {
                'file': 'atlas_hazard_ndws_future.csv',
                'description': 'Number of Days of Water Stress (future climate projections)',
                'expected_cols': ['admin0_name', 'admin1_name', 'admin2_name', 'scenario', 'timeframe', 'hazard', 'value']
            },
            'hazard_erosion': {
                'file': 'atlas_hazard_erosion_proxy.csv', 
                'description': 'Thornthwaite Aridity Index (environmental degradation proxy)',
                'expected_cols': ['admin0_name', 'admin1_name', 'admin2_name', 'scenario', 'timeframe', 'hazard', 'value']
            },
            'exposure_population': {
                'file': 'atlas_exposure_population.csv',
                'description': 'Population exposure data',
                'expected_cols': ['admin0_name', 'admin1_name', 'admin2_name', 'value']
            },
            'exposure_vop': {
                'file': 'atlas_exposure_vop_crops.csv',
                'description': 'Value of Production (crops) - economic exposure',
                'expected_cols': ['admin0_name', 'admin1_name', 'admin2_name', 'exposure', 'crop', 'value', 'group']
            },
            'adaptive_capacity': {
                'file': 'atlas_adaptive_capacity_poverty.csv',
                'description': 'Poverty headcount ratio (adaptive capacity)',
                'expected_cols': ['admin0_name', 'admin1_name', 'admin2_name', 'value']
            }
        }
        
        logger.info("Atlas Data Analyzer initialized")
        logger.info("📍 DATA STRATEGY: 100% Atlas-based workflow (NO SoilGrids)")
        logger.info("🌿 Environmental proxy: TAI (Thornthwaite's Aridity Index)")
    
    def load_and_analyze_individual_datasets(self) -> Dict:
        """Load and analyze each Atlas dataset individually"""
        
        logger.info("🔍 ANALYZING INDIVIDUAL ATLAS DATASETS")
        logger.info("=" * 50)
        
        analysis_results = {}
        
        for dataset_name, info in self.atlas_files.items():
            logger.info(f"\n📊 ANALYZING: {dataset_name.upper()}")
            logger.info(f"📝 Description: {info['description']}")
            
            file_path = self.raw_dir / info['file']
            
            if not file_path.exists():
                logger.error(f"❌ File not found: {info['file']}")
                analysis_results[dataset_name] = {'status': 'missing', 'error': f"File not found: {info['file']}"}
                continue
            
            try:
                # Load dataset
                df = pd.read_csv(file_path)
                logger.info(f"✅ Loaded: {len(df):,} records")
                
                # Perform individual analysis
                analysis = self.analyze_single_dataset(df, dataset_name, info)
                analysis_results[dataset_name] = analysis
                
                # Print summary
                self.print_dataset_summary(dataset_name, analysis)
                
            except Exception as e:
                logger.error(f"❌ Error analyzing {dataset_name}: {str(e)}")
                analysis_results[dataset_name] = {'status': 'error', 'error': str(e)}
        
        return analysis_results
    
    def analyze_single_dataset(self, df: pd.DataFrame, dataset_name: str, info: Dict) -> Dict:
        """Analyze a single dataset comprehensively"""
        
        analysis = {
            'status': 'success',
            'basic_info': {},
            'columns': {},
            'geographic_coverage': {},
            'data_quality': {},
            'value_analysis': {},
            'special_analysis': {}
        }
        
        # Basic information
        analysis['basic_info'] = {
            'total_records': len(df),
            'total_columns': len(df.columns),
            'column_names': list(df.columns),
            'memory_usage_mb': df.memory_usage(deep=True).sum() / 1024**2
        }
        
        # Column analysis
        for col in df.columns:
            analysis['columns'][col] = {
                'dtype': str(df[col].dtype),
                'non_null_count': df[col].notna().sum(),
                'null_count': df[col].isna().sum(),
                'null_percentage': (df[col].isna().sum() / len(df)) * 100,
                'unique_values': df[col].nunique()
            }
            
            if df[col].dtype in ['int64', 'float64']:
                analysis['columns'][col].update({
                    'min': df[col].min(),
                    'max': df[col].max(),
                    'mean': df[col].mean(),
                    'median': df[col].median(),
                    'std': df[col].std()
                })
        
        # Geographic coverage (if has admin columns)
        admin_cols = ['admin0_name', 'admin1_name', 'admin2_name']
        if all(col in df.columns for col in admin_cols):
            analysis['geographic_coverage'] = {
                'total_countries': df['admin0_name'].nunique(),
                'total_regions': df[admin_cols].drop_duplicates().shape[0],
                'countries_list': sorted(df['admin0_name'].unique()),
                'top_countries_by_records': df['admin0_name'].value_counts().head(10).to_dict()
            }
        
        # Data quality checks
        analysis['data_quality'] = {
            'total_missing_values': df.isnull().sum().sum(),
            'missing_percentage': (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100,
            'duplicate_rows': df.duplicated().sum(),
            'completely_empty_rows': df.isnull().all(axis=1).sum()
        }
        
        # Value column analysis (most datasets have a 'value' column)
        if 'value' in df.columns:
            value_col = df['value']
            analysis['value_analysis'] = {
                'count': value_col.notna().sum(),
                'missing': value_col.isna().sum(),
                'min': value_col.min(),
                'max': value_col.max(),
                'mean': value_col.mean(),
                'median': value_col.median(),
                'std': value_col.std(),
                'zero_values': (value_col == 0).sum(),
                'negative_values': (value_col < 0).sum(),
                'outliers': self.detect_outliers(value_col)
            }
        
        # Special analysis based on dataset type
        if dataset_name == 'hazard_ndws':
            analysis['special_analysis'] = self.analyze_ndws_data(df)
        elif dataset_name == 'hazard_erosion':
            analysis['special_analysis'] = self.analyze_tai_data(df)
        elif dataset_name == 'exposure_vop':
            analysis['special_analysis'] = self.analyze_vop_data(df)
        elif dataset_name == 'adaptive_capacity':
            analysis['special_analysis'] = self.analyze_poverty_data(df)
        
        return analysis
    
    def detect_outliers(self, series: pd.Series) -> int:
        """Detect outliers using IQR method"""
        if series.notna().sum() < 4:
            return 0
        
        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1
        
        if IQR == 0:
            return 0
        
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        return ((series < lower_bound) | (series > upper_bound)).sum()
    
    def analyze_ndws_data(self, df: pd.DataFrame) -> Dict:
        """Special analysis for NDWS hazard data"""
        
        analysis = {}
        
        if 'scenario' in df.columns:
            analysis['scenarios'] = df['scenario'].value_counts().to_dict()
        
        if 'timeframe' in df.columns:
            analysis['timeframes'] = df['timeframe'].value_counts().to_dict()
            
        if 'hazard' in df.columns:
            analysis['hazard_types'] = df['hazard'].value_counts().to_dict()
        
        # Recommended filtering for fusion
        analysis['fusion_recommendations'] = {
            'preferred_scenario': 'ssp245',  # Moderate climate scenario
            'preferred_timeframe': '2041_2060',
            'expected_records_after_filter': len(df[
                (df.get('scenario', '') == 'ssp245') & 
                (df.get('timeframe', '') == '2041_2060')
            ]) if all(col in df.columns for col in ['scenario', 'timeframe']) else len(df)
        }
        
        return analysis
    
    def analyze_tai_data(self, df: pd.DataFrame) -> Dict:
        """Special analysis for TAI (erosion proxy) data"""
        
        analysis = {}
        
        if 'scenario' in df.columns:
            analysis['scenarios'] = df['scenario'].value_counts().to_dict()
        
        if 'timeframe' in df.columns:
            analysis['timeframes'] = df['timeframe'].value_counts().to_dict()
        
        if 'hazard' in df.columns:
            analysis['hazard_types'] = df['hazard'].value_counts().to_dict()
        
        # TAI interpretation
        if 'value' in df.columns:
            tai_values = df['value'].dropna()
            analysis['tai_interpretation'] = {
                'mean_aridity': tai_values.mean(),
                'high_aridity_regions': (tai_values > tai_values.quantile(0.75)).sum(),
                'low_aridity_regions': (tai_values < tai_values.quantile(0.25)).sum(),
                'erosion_risk_explanation': 'Higher TAI = More arid = Higher erosion risk (less vegetation protection)'
            }
        
        return analysis
    
    def analyze_vop_data(self, df: pd.DataFrame) -> Dict:
        """Special analysis for VOP crops data"""
        
        analysis = {}
        
        if 'crop' in df.columns:
            analysis['crop_types'] = df['crop'].value_counts().to_dict()
            analysis['total_crop_types'] = df['crop'].nunique()
        
        if 'exposure' in df.columns:
            analysis['exposure_types'] = df['exposure'].value_counts().to_dict()
        
        if 'value' in df.columns and 'crop' in df.columns:
            crop_values = df.groupby('crop')['value'].agg(['sum', 'mean', 'count']).round(2)
            analysis['top_crops_by_value'] = crop_values.sort_values('sum', ascending=False).head(10).to_dict()
        
        # Aggregation needed for fusion
        if all(col in df.columns for col in ['admin0_name', 'admin1_name', 'admin2_name', 'value']):
            admin_totals = df.groupby(['admin0_name', 'admin1_name', 'admin2_name'])['value'].sum()
            analysis['fusion_preparation'] = {
                'unique_regions': len(admin_totals),
                'total_vop_value': admin_totals.sum(),
                'aggregation_needed': True,
                'explanation': 'VOP data needs to be aggregated by region (sum across all crops)'
            }
        
        return analysis
    
    def analyze_poverty_data(self, df: pd.DataFrame) -> Dict:
        """Special analysis for poverty/adaptive capacity data"""
        
        analysis = {}
        
        if 'value' in df.columns:
            poverty_values = df['value'].dropna()
            analysis['poverty_statistics'] = {
                'mean_poverty_rate': poverty_values.mean(),
                'median_poverty_rate': poverty_values.median(),
                'high_poverty_regions': (poverty_values > 0.5).sum(),
                'low_poverty_regions': (poverty_values < 0.2).sum(),
                'extreme_poverty_regions': (poverty_values > 0.8).sum()
            }
        
        return analysis
    
    def print_dataset_summary(self, dataset_name: str, analysis: Dict):
        """Print a summary of dataset analysis"""
        
        if analysis['status'] != 'success':
            logger.error(f"❌ {dataset_name}: {analysis.get('error', 'Unknown error')}")
            return
        
        basic = analysis['basic_info']
        geo = analysis.get('geographic_coverage', {})
        quality = analysis['data_quality']
        
        logger.info(f"📈 Records: {basic['total_records']:,}")
        logger.info(f"📊 Columns: {basic['total_columns']}")
        
        if geo:
            logger.info(f"🌍 Countries: {geo['total_countries']}")
            logger.info(f"🗺️ Regions: {geo['total_regions']:,}")
        
        logger.info(f"✅ Completeness: {100-quality['missing_percentage']:.1f}%")
        
        if 'value_analysis' in analysis and analysis['value_analysis']:
            val = analysis['value_analysis']
            logger.info(f"💰 Value range: [{val['min']:.2f}, {val['max']:.2f}]")
        
        if 'special_analysis' in analysis and analysis['special_analysis']:
            special = analysis['special_analysis']
            if 'fusion_recommendations' in special:
                logger.info(f"🔧 Fusion ready: {special['fusion_recommendations']['expected_records_after_filter']:,} records")
    
    def analyze_cross_dataset_compatibility(self, individual_analyses: Dict) -> Dict:
        """Analyze compatibility across datasets for fusion"""
        
        logger.info("\n🔗 CROSS-DATASET COMPATIBILITY ANALYSIS")
        logger.info("=" * 45)
        
        compatibility = {
            'geographic_alignment': {},
            'coverage_comparison': {},
            'fusion_readiness': {},
            'potential_issues': []
        }
        
        # Extract geographic coverage from each dataset
        geo_data = {}
        for dataset_name, analysis in individual_analyses.items():
            if analysis['status'] == 'success' and 'geographic_coverage' in analysis:
                geo = analysis['geographic_coverage']
                geo_data[dataset_name] = {
                    'countries': set(geo.get('countries_list', [])),
                    'country_count': geo.get('total_countries', 0),
                    'region_count': geo.get('total_regions', 0)
                }
        
        # Find common countries
        if geo_data:
            all_countries = [data['countries'] for data in geo_data.values()]
            common_countries = set.intersection(*all_countries) if all_countries else set()
            all_unique_countries = set.union(*all_countries) if all_countries else set()
            
            compatibility['geographic_alignment'] = {
                'common_countries': sorted(list(common_countries)),
                'common_country_count': len(common_countries),
                'total_unique_countries': len(all_unique_countries),
                'coverage_overlap_percentage': (len(common_countries) / len(all_unique_countries)) * 100 if all_unique_countries else 0
            }
            
            logger.info(f"🌍 Common countries across datasets: {len(common_countries)}")
            logger.info(f"📊 Geographic overlap: {compatibility['geographic_alignment']['coverage_overlap_percentage']:.1f}%")
        
        # Compare record counts and coverage
        for dataset_name, analysis in individual_analyses.items():
            if analysis['status'] == 'success':
                basic = analysis['basic_info']
                compatibility['coverage_comparison'][dataset_name] = {
                    'total_records': basic['total_records'],
                    'completeness_percentage': 100 - analysis['data_quality']['missing_percentage'],
                    'ready_for_fusion': analysis['data_quality']['missing_percentage'] < 10
                }
        
        # Fusion readiness assessment
        ready_datasets = sum(1 for data in compatibility['coverage_comparison'].values() if data['ready_for_fusion'])
        total_datasets = len(compatibility['coverage_comparison'])
        
        compatibility['fusion_readiness'] = {
            'ready_datasets': ready_datasets,
            'total_datasets': total_datasets,
            'readiness_percentage': (ready_datasets / total_datasets) * 100 if total_datasets else 0,
            'recommendation': 'PROCEED' if ready_datasets >= 4 else 'REVIEW_ISSUES'
        }
        
        logger.info(f"✅ Datasets ready for fusion: {ready_datasets}/{total_datasets}")
        logger.info(f"🎯 Fusion readiness: {compatibility['fusion_readiness']['readiness_percentage']:.1f}%")
        
        # Identify potential issues
        for dataset_name, analysis in individual_analyses.items():
            if analysis['status'] != 'success':
                compatibility['potential_issues'].append(f"{dataset_name}: {analysis.get('error', 'Unknown error')}")
            elif analysis['data_quality']['missing_percentage'] > 10:
                compatibility['potential_issues'].append(f"{dataset_name}: High missing data ({analysis['data_quality']['missing_percentage']:.1f}%)")
        
        if compatibility['potential_issues']:
            logger.warning("⚠️ Potential issues identified:")
            for issue in compatibility['potential_issues']:
                logger.warning(f"   • {issue}")
        else:
            logger.info("✅ No major compatibility issues detected")
        
        return compatibility
    
    def generate_fusion_strategy(self, individual_analyses: Dict, compatibility: Dict) -> Dict:
        """Generate recommended fusion strategy"""
        
        logger.info("\n🎯 FUSION STRATEGY RECOMMENDATIONS")
        logger.info("=" * 40)
        
        strategy = {
            'approach': '100% Atlas-based fusion',
            'base_dataset': None,
            'join_strategy': {},
            'aggregation_requirements': {},
            'filtering_requirements': {},
            'quality_expectations': {}
        }
        
        # Determine base dataset (highest coverage, lowest missing data)
        best_coverage = 0
        best_dataset = None
        
        for dataset_name, analysis in individual_analyses.items():
            if analysis['status'] == 'success':
                geo = analysis.get('geographic_coverage', {})
                quality = analysis['data_quality']
                
                coverage_score = geo.get('total_regions', 0) * (100 - quality['missing_percentage']) / 100
                
                if coverage_score > best_coverage:
                    best_coverage = coverage_score
                    best_dataset = dataset_name
        
        strategy['base_dataset'] = best_dataset
        logger.info(f"📍 Recommended base dataset: {best_dataset}")
        
        # Define join strategy for each dataset
        for dataset_name, analysis in individual_analyses.items():
            if analysis['status'] == 'success':
                if dataset_name == 'exposure_vop':
                    strategy['join_strategy'][dataset_name] = {
                        'method': 'left_join_with_aggregation',
                        'key': ['admin0_name', 'admin1_name', 'admin2_name'],
                        'aggregation': 'sum_by_region',
                        'note': 'Aggregate VOP values across all crops per region'
                    }
                    strategy['aggregation_requirements'][dataset_name] = 'sum(value) group by admin regions'
                else:
                    strategy['join_strategy'][dataset_name] = {
                        'method': 'left_join',
                        'key': ['admin0_name', 'admin1_name', 'admin2_name'],
                        'aggregation': 'none'
                    }
        
        # Define filtering requirements
        for dataset_name, analysis in individual_analyses.items():
            special = analysis.get('special_analysis', {})
            if 'fusion_recommendations' in special:
                strategy['filtering_requirements'][dataset_name] = special['fusion_recommendations']
        
        # Quality expectations
        if compatibility['fusion_readiness']['readiness_percentage'] >= 80:
            strategy['quality_expectations'] = {
                'expected_final_coverage': '90-95% of Sub-Saharan Africa',
                'expected_completeness': '95%+',
                'confidence_level': 'HIGH'
            }
        else:
            strategy['quality_expectations'] = {
                'expected_final_coverage': '80-90% of Sub-Saharan Africa',
                'expected_completeness': '85-95%',
                'confidence_level': 'MEDIUM'
            }
        
        logger.info(f"🎯 Strategy: {strategy['approach']}")
        logger.info(f"📊 Expected coverage: {strategy['quality_expectations']['expected_final_coverage']}")
        logger.info(f"✅ Confidence: {strategy['quality_expectations']['confidence_level']}")
        
        return strategy
    
    def save_analysis_results(self, individual_analyses: Dict, compatibility: Dict, strategy: Dict):
        """Save all analysis results"""
        
        logger.info("\n💾 SAVING ANALYSIS RESULTS")
        
        # Combine all results
        full_analysis = {
            'analysis_metadata': {
                'analysis_date': pd.Timestamp.now().isoformat(),
                'data_strategy': '100% Atlas-based (no SoilGrids)',
                'environmental_proxy': 'TAI (Thornthwaite Aridity Index)',
                'total_datasets_analyzed': len(individual_analyses)
            },
            'individual_datasets': individual_analyses,
            'cross_dataset_compatibility': compatibility,
            'fusion_strategy': strategy
        }
        
        # Save comprehensive analysis
        analysis_file = self.processed_dir / "pre_fusion_atlas_analysis.json"
        with open(analysis_file, 'w') as f:
            json.dump(full_analysis, f, indent=2, default=str)
        logger.info(f"✅ Full analysis saved: {analysis_file}")
        
        # Save summary for easy reference
        summary = {
            'datasets_ready': sum(1 for a in individual_analyses.values() if a['status'] == 'success'),
            'total_datasets': len(individual_analyses),
            'fusion_readiness': compatibility['fusion_readiness']['readiness_percentage'],
            'recommended_base': strategy['base_dataset'],
            'confidence_level': strategy['quality_expectations']['confidence_level']
        }
        
        summary_file = self.processed_dir / "atlas_analysis_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"✅ Summary saved: {summary_file}")
    
    def run_complete_analysis(self) -> Tuple[Dict, Dict, Dict]:
        """Run the complete pre-fusion analysis"""
        
        logger.info("🚀 STARTING PRE-FUSION ATLAS ANALYSIS")
        logger.info("=" * 55)
        logger.info("📋 STRATEGY: 100% Atlas-based workflow")
        logger.info("🚫 NO SoilGrids (eliminated due to geometric complexity)")
        logger.info("🌿 Environmental data: TAI as erosion/degradation proxy")
        
        try:
            # Step 1: Analyze individual datasets
            individual_analyses = self.load_and_analyze_individual_datasets()
            
            # Step 2: Cross-dataset compatibility
            compatibility = self.analyze_cross_dataset_compatibility(individual_analyses)
            
            # Step 3: Generate fusion strategy
            strategy = self.generate_fusion_strategy(individual_analyses, compatibility)
            
            # Step 4: Save results
            self.save_analysis_results(individual_analyses, compatibility, strategy)
            
            logger.info("\n🎉 PRE-FUSION ANALYSIS COMPLETE!")
            logger.info("=" * 40)
            
            return individual_analyses, compatibility, strategy
            
        except Exception as e:
            logger.error(f"❌ Analysis failed: {str(e)}")
            raise


def main():
    """Main execution function"""
    
    # Run the complete pre-fusion analysis
    analyzer = AtlasDataAnalyzer()
    individual, compatibility, strategy = analyzer.run_complete_analysis()
    
    # Print final summary
    print("\n" + "="*60)
    print("PRE-FUSION ANALYSIS COMPLETE")
    print("="*60)
    
    ready_count = sum(1 for a in individual.values() if a['status'] == 'success')
    total_count = len(individual)
    
    print(f"📊 Datasets analyzed: {ready_count}/{total_count}")
    print(f"🎯 Fusion readiness: {compatibility['fusion_readiness']['readiness_percentage']:.1f}%")
    print(f"📍 Recommended base: {strategy['base_dataset']}")
    print(f"✅ Confidence level: {strategy['quality_expectations']['confidence_level']}")
    
    print(f"\n🌿 ENVIRONMENTAL DATA STRATEGY:")
    print(f"   • NO SoilGrids (geometric issues eliminated)")
    print(f"   • Using TAI (Thornthwaite's Aridity Index) as erosion proxy")
    print(f"   • 100% Atlas-harmonized data workflow")
    
    print(f"\n📁 Results saved to: data/processed/")
    print(f"   • pre_fusion_atlas_analysis.json (detailed)")
    print(f"   • atlas_analysis_summary.json (summary)")
    
    if compatibility['fusion_readiness']['recommendation'] == 'PROCEED':
        print(f"\n✅ RECOMMENDATION: Proceed with Atlas fusion")
    else:
        print(f"\n⚠️ RECOMMENDATION: Review issues before fusion")


if __name__ == "__main__":
    main()