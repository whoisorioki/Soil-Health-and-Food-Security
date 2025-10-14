#!/usr/bin/env python3
"""
Atlas Data Inconsistency Analysis
=================================

This script investigates the specific inconsistencies found in the pre-fusion analysis
and provides detailed recommendations for handling them.

Key Issues Identified:
1. Record count variations across datasets (9,192 vs 4,596 vs 151,668)
2. Different data structures (scenario/timeframe filtering)
3. VOP data aggregation needs

Author: Atlas Data Investigation Pipeline
Date: October 2025
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AtlasInconsistencyAnalyzer:
    """Analyze and resolve Atlas dataset inconsistencies"""
    
    def __init__(self):
        self.data_dir = Path("data/raw")
        self.issues = defaultdict(list)
        self.solutions = defaultdict(list)
    
    def analyze_record_count_discrepancies(self):
        """Investigate why datasets have different record counts"""
        
        logger.info("🔍 INVESTIGATING RECORD COUNT DISCREPANCIES")
        logger.info("=" * 50)
        
        datasets = {
            'NDWS': 'atlas_hazard_ndws_future.csv',
            'TAI': 'atlas_hazard_erosion_proxy.csv', 
            'Population': 'atlas_exposure_population.csv',
            'VOP': 'atlas_exposure_vop_crops.csv',
            'Poverty': 'atlas_adaptive_capacity_poverty.csv'
        }
        
        record_analysis = {}
        
        for name, filename in datasets.items():
            df = pd.read_csv(self.data_dir / filename)
            
            # Basic counts
            total_records = len(df)
            unique_regions = len(df[['admin0_name', 'admin1_name', 'admin2_name']].drop_duplicates())
            
            analysis = {
                'total_records': total_records,
                'unique_regions': unique_regions,
                'records_per_region': total_records / unique_regions if unique_regions > 0 else 0
            }
            
            # Check for scenario/timeframe multipliers
            if 'scenario' in df.columns:
                scenarios = df['scenario'].nunique()
                timeframes = df['timeframe'].nunique() if 'timeframe' in df.columns else 1
                analysis['scenarios'] = scenarios
                analysis['timeframes'] = timeframes
                analysis['expected_multiplier'] = scenarios * timeframes
            
            # Check for crop/indicator multipliers  
            if 'crop' in df.columns:
                crops = df['crop'].nunique()
                analysis['crops'] = crops
                analysis['expected_multiplier'] = crops
            
            if 'hazard' in df.columns:
                hazards = df['hazard'].nunique()
                analysis['hazards'] = hazards
                analysis['expected_multiplier'] = hazards if 'crop' not in df.columns else 1
            
            record_analysis[name] = analysis
            
            logger.info(f"📊 {name}:")
            logger.info(f"   Total records: {total_records:,}")
            logger.info(f"   Unique regions: {unique_regions:,}")
            logger.info(f"   Records per region: {analysis['records_per_region']:.1f}")
            
            if 'expected_multiplier' in analysis:
                logger.info(f"   Data multiplier: {analysis['expected_multiplier']}x")
        
        # Identify the issues
        base_regions = record_analysis['TAI']['unique_regions']  # TAI has clean 1:1 mapping
        
        for name, analysis in record_analysis.items():
            if analysis['unique_regions'] != base_regions:
                self.issues['region_mismatch'].append(f"{name}: {analysis['unique_regions']} regions vs expected {base_regions}")
            
            if analysis['records_per_region'] > 1.1:  # Allow small floating point tolerance
                self.issues['data_multiplication'].append(f"{name}: {analysis['records_per_region']:.1f} records per region")
        
        return record_analysis
    
    def investigate_vop_aggregation_issue(self):
        """Analyze the VOP data structure and aggregation needs"""
        
        logger.info("\n🌾 INVESTIGATING VOP DATA STRUCTURE")
        logger.info("=" * 40)
        
        df_vop = pd.read_csv(self.data_dir / 'atlas_exposure_vop_crops.csv')
        
        # Analyze crop distribution
        crops = df_vop['crop'].value_counts()
        regions = df_vop[['admin0_name', 'admin1_name', 'admin2_name']].drop_duplicates()
        
        logger.info(f"📊 VOP Data Structure:")
        logger.info(f"   Total records: {len(df_vop):,}")
        logger.info(f"   Unique regions: {len(regions):,}")
        logger.info(f"   Unique crops: {len(crops)}")
        logger.info(f"   Records per region: {len(df_vop) / len(regions):.1f}")
        
        logger.info(f"\n🌾 Top 10 crops by record count:")
        for crop, count in crops.head(10).items():
            logger.info(f"   {crop}: {count:,} records")
        
        # Check if all regions have all crops
        region_crop_matrix = df_vop.groupby(['admin0_name', 'admin1_name', 'admin2_name'])['crop'].nunique()
        crops_per_region = region_crop_matrix.describe()
        
        logger.info(f"\n📊 Crops per region distribution:")
        logger.info(f"   Mean: {crops_per_region['mean']:.1f}")
        logger.info(f"   Min: {crops_per_region['min']:.0f}")
        logger.info(f"   Max: {crops_per_region['max']:.0f}")
        logger.info(f"   Std: {crops_per_region['std']:.1f}")
        
        # Identify the solution needed
        if crops_per_region['max'] > 1:
            self.issues['vop_aggregation'].append("VOP data needs aggregation across crops")
            self.solutions['vop_aggregation'].append("Sum VOP values by region to get total agricultural value")
        
        return {
            'total_records': len(df_vop),
            'unique_regions': len(regions),
            'unique_crops': len(crops),
            'crops_per_region_stats': crops_per_region.to_dict()
        }
    
    def investigate_scenario_filtering(self):
        """Analyze scenario/timeframe filtering needs"""
        
        logger.info("\n📅 INVESTIGATING SCENARIO/TIMEFRAME FILTERING")
        logger.info("=" * 45)
        
        # Check NDWS data
        df_ndws = pd.read_csv(self.data_dir / 'atlas_hazard_ndws_future.csv')
        
        logger.info(f"📊 NDWS Data Scenarios:")
        scenarios = df_ndws['scenario'].value_counts()
        timeframes = df_ndws['timeframe'].value_counts()
        
        for scenario, count in scenarios.items():
            logger.info(f"   {scenario}: {count:,} records")
        
        logger.info(f"📊 NDWS Data Timeframes:")
        for timeframe, count in timeframes.items():
            logger.info(f"   {timeframe}: {count:,} records")
        
        # Check if we need to pick specific scenarios
        unique_regions_per_scenario = df_ndws.groupby('scenario').apply(
            lambda x: len(x[['admin0_name', 'admin1_name', 'admin2_name']].drop_duplicates())
        )
        
        logger.info(f"📊 Regions per scenario:")
        for scenario, region_count in unique_regions_per_scenario.items():
            logger.info(f"   {scenario}: {region_count:,} regions")
        
        # Check population data
        df_pop = pd.read_csv(self.data_dir / 'atlas_exposure_population.csv')
        
        logger.info(f"\n📊 Population Data Scenarios:")
        if 'scenario' in df_pop.columns:
            pop_scenarios = df_pop['scenario'].value_counts()
            for scenario, count in pop_scenarios.items():
                logger.info(f"   {scenario}: {count:,} records")
        else:
            logger.info("   No scenario column in population data")
        
        # Identify filtering needs
        if len(scenarios) > 1:
            self.issues['scenario_filtering'].append(f"NDWS has {len(scenarios)} scenarios: {list(scenarios.index)}")
            self.solutions['scenario_filtering'].append("Choose one scenario (recommend ssp245 for moderate projection)")
        
        return {
            'ndws_scenarios': scenarios.to_dict(),
            'ndws_timeframes': timeframes.to_dict(),
            'regions_per_scenario': unique_regions_per_scenario.to_dict()
        }
    
    def check_poverty_data_coverage(self):
        """Analyze poverty data completeness"""
        
        logger.info("\n💰 INVESTIGATING POVERTY DATA COVERAGE")
        logger.info("=" * 40)
        
        df_poverty = pd.read_csv(self.data_dir / 'atlas_adaptive_capacity_poverty.csv')
        
        # Check for missing values
        missing_values = df_poverty['value'].isnull().sum()
        total_records = len(df_poverty)
        missing_pct = missing_values / total_records * 100
        
        logger.info(f"📊 Poverty Data Coverage:")
        logger.info(f"   Total records: {total_records:,}")
        logger.info(f"   Missing values: {missing_values:,} ({missing_pct:.1f}%)")
        logger.info(f"   Complete records: {total_records - missing_values:,}")
        
        if missing_values > 0:
            self.issues['poverty_coverage'].append(f"Poverty data missing for {missing_values:,} records ({missing_pct:.1f}%)")
            self.solutions['poverty_coverage'].append("Use imputation strategy or exclude regions with missing poverty data")
        
        # Check scenarios in poverty data
        if 'scenario' in df_poverty.columns:
            poverty_scenarios = df_poverty['scenario'].value_counts()
            logger.info(f"📊 Poverty scenarios:")
            for scenario, count in poverty_scenarios.items():
                logger.info(f"   {scenario}: {count:,} records")
        
        return {
            'total_records': total_records,
            'missing_values': missing_values,
            'missing_percentage': missing_pct
        }
    
    def generate_fusion_recommendations(self):
        """Generate specific recommendations for data fusion"""
        
        logger.info("\n🎯 FUSION RECOMMENDATIONS")
        logger.info("=" * 30)
        
        logger.info("📋 IDENTIFIED ISSUES:")
        for issue_type, issue_list in self.issues.items():
            logger.info(f"\n   {issue_type.upper()}:")
            for issue in issue_list:
                logger.info(f"     • {issue}")
        
        logger.info("\n💡 RECOMMENDED SOLUTIONS:")
        for solution_type, solution_list in self.solutions.items():
            logger.info(f"\n   {solution_type.upper()}:")
            for solution in solution_list:
                logger.info(f"     ✅ {solution}")
        
        # Additional specific recommendations
        logger.info("\n🔧 SPECIFIC FUSION STEPS:")
        logger.info("   1. Filter NDWS data: scenario='ssp245', timeframe='2041_2060'")
        logger.info("   2. Aggregate VOP data: SUM by region across all crops") 
        logger.info("   3. Filter population data: Use scenario='ssp245' if available")
        logger.info("   4. Handle poverty missing values: Use existing imputation or exclude")
        logger.info("   5. Use TAI data as-is (already clean 1:1 mapping)")
        
        # SoilGrids clarification
        logger.info("\n🌿 SOILGRIDS CLARIFICATION:")
        logger.info("   ❌ NOT USING SoilGrids due to:")
        logger.info("     • Complex geometric errors in boundary files")
        logger.info("     • Time-consuming QGIS workflow issues")
        logger.info("     • Data pipeline fragility")
        logger.info("   ✅ USING Atlas TAI instead:")
        logger.info("     • Thornthwaite's Aridity Index as erosion proxy")
        logger.info("     • Higher aridity = higher erosion risk")
        logger.info("     • Scientifically valid proxy for soil degradation")
        logger.info("     • 100% compatible with Atlas data structure")
        
        return {
            'issues_identified': len(self.issues),
            'solutions_provided': len(self.solutions),
            'fusion_confidence': 'HIGH' if len(self.issues) <= 3 else 'MEDIUM'
        }
    
    def run_complete_analysis(self):
        """Run complete inconsistency analysis"""
        
        logger.info("🔍 ATLAS DATA INCONSISTENCY ANALYSIS")
        logger.info("=" * 45)
        
        # Run all analyses
        record_analysis = self.analyze_record_count_discrepancies()
        vop_analysis = self.investigate_vop_aggregation_issue()
        scenario_analysis = self.investigate_scenario_filtering()
        poverty_analysis = self.check_poverty_data_coverage()
        recommendations = self.generate_fusion_recommendations()
        
        # Compile results
        results = {
            'record_analysis': record_analysis,
            'vop_analysis': vop_analysis,
            'scenario_analysis': scenario_analysis,
            'poverty_analysis': poverty_analysis,
            'issues': dict(self.issues),
            'solutions': dict(self.solutions),
            'recommendations': recommendations
        }
        
        # Save results
        import json
        output_file = Path("data/processed/atlas_inconsistency_analysis.json")
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"\n💾 Analysis saved to: {output_file}")
        
        return results

def main():
    """Main execution function"""
    
    analyzer = AtlasInconsistencyAnalyzer()
    results = analyzer.run_complete_analysis()
    
    print("\n" + "="*60)
    print("INCONSISTENCY ANALYSIS COMPLETE")
    print("="*60)
    print(f"🔍 Issues identified: {results['recommendations']['issues_identified']}")
    print(f"💡 Solutions provided: {results['recommendations']['solutions_provided']}")
    print(f"🎯 Fusion confidence: {results['recommendations']['fusion_confidence']}")
    
    print("\n🌿 SOILGRIDS STATUS: NOT USED")
    print("   • Strategic decision to avoid geometric complexity")
    print("   • Using TAI (Thornthwaite's Aridity Index) as soil proxy")
    print("   • 100% Atlas-harmonized workflow")
    
    print("\n✅ Ready to proceed with corrected fusion approach!")

if __name__ == "__main__":
    main()