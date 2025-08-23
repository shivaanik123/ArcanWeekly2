"""
Comprehensive Historical Data Parser

This module processes comprehensive reports from the "Comprehensive Reports" directory
to extract historical trends across multiple properties and time periods.

Features:
- Aggregates historical data from all property weekly reports
- Tracks occupancy trends, work orders, make ready counts over time
- Provides cross-property comparisons and benchmarking
- Generates time-series data for dashboard visualization
"""

import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import glob
from pathlib import Path

try:
    from .comprehensive_internal_parser import parse_comprehensive_internal_report
    from .file_parser import parse_file
except ImportError:
    from comprehensive_internal_parser import parse_comprehensive_internal_report
    from file_parser import parse_file


class ComprehensiveHistoricalParser:
    """Parser for aggregating historical data from comprehensive reports."""
    
    def __init__(self, comprehensive_reports_path: str):
        """
        Initialize the historical parser.
        
        Args:
            comprehensive_reports_path: Path to the Comprehensive Reports directory
        """
        self.reports_path = comprehensive_reports_path
        self.property_data = {}
        self.aggregated_data = {}
        
    def discover_property_reports(self) -> Dict[str, str]:
        """
        Discover all property weekly reports in the comprehensive reports directory.
        
        Returns:
            Dictionary mapping property names to their report file paths
        """
        reports_dir = os.path.join(self.reports_path, "Comprehensive Reports")
        if not os.path.exists(reports_dir):
            return {}
        
        property_reports = {}
        
        # Look for Weekly Report files
        pattern = os.path.join(reports_dir, "*Weekly Report*.xlsx")
        report_files = glob.glob(pattern)
        
        for file_path in report_files:
            filename = os.path.basename(file_path)
            # Extract property name from filename
            property_name = filename.replace(" Weekly Report.xlsx", "").replace(" Weekly Report (1).xlsx", "")
            property_reports[property_name] = file_path
            
        return property_reports
    
    def parse_all_properties(self) -> Dict[str, Any]:
        """
        Parse historical data from all discovered property reports.
        
        Returns:
            Dictionary containing parsed data for all properties
        """
        property_reports = self.discover_property_reports()
        
        results = {
            'properties_found': len(property_reports),
            'properties_data': {},
            'parsing_errors': [],
            'summary': {}
        }
        
        for property_name, file_path in property_reports.items():
            try:
                print(f"Parsing {property_name}...")
                parsed_data = parse_file(file_path)
                
                if 'error' not in parsed_data:
                    results['properties_data'][property_name] = parsed_data
                    self.property_data[property_name] = parsed_data
                else:
                    results['parsing_errors'].append({
                        'property': property_name,
                        'error': parsed_data['error']
                    })
                    
            except Exception as e:
                results['parsing_errors'].append({
                    'property': property_name,
                    'error': str(e)
                })
        
        # Generate summary statistics
        results['summary'] = self._generate_summary()
        
        return results
    
    def get_historical_trends(self, property_name: str = None) -> Dict[str, Any]:
        """
        Extract historical trends for a specific property or all properties.
        
        Args:
            property_name: Specific property name, or None for all properties
            
        Returns:
            Dictionary containing historical trend data
        """
        if property_name and property_name in self.property_data:
            return self._extract_property_trends(property_name, self.property_data[property_name])
        
        # Aggregate trends across all properties
        all_trends = {}
        
        for prop_name, prop_data in self.property_data.items():
            trends = self._extract_property_trends(prop_name, prop_data)
            all_trends[prop_name] = trends
            
        return all_trends
    
    def _extract_property_trends(self, property_name: str, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract trends from a single property's data."""
        
        historical_data = property_data.get('historical_data', {})
        weekly_data = historical_data.get('weekly_occupancy_data', [])
        
        if not weekly_data:
            return {'error': 'No historical data found'}
        
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(weekly_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Calculate trends
        trends = {
            'property_name': property_name,
            'data_points': len(df),
            'date_range': {
                'start': df['date'].min().isoformat() if not df.empty else None,
                'end': df['date'].max().isoformat() if not df.empty else None
            },
            'occupancy_trends': self._calculate_occupancy_trends(df),
            'work_order_trends': self._calculate_work_order_trends(df),
            'make_ready_trends': self._calculate_make_ready_trends(df),
            'recent_performance': self._get_recent_performance(df),
            'monthly_averages': self._calculate_monthly_averages(df)
        }
        
        return trends
    
    def _calculate_occupancy_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate occupancy trend metrics."""
        if df.empty:
            return {}
        
        occupancy_data = df['occupancy_percent'].dropna()
        
        return {
            'current': float(occupancy_data.iloc[-1]) if not occupancy_data.empty else 0,
            'average': float(occupancy_data.mean()),
            'min': float(occupancy_data.min()),
            'max': float(occupancy_data.max()),
            'trend_direction': 'increasing' if len(occupancy_data) > 1 and occupancy_data.iloc[-1] > occupancy_data.iloc[0] else 'decreasing',
            'volatility': float(occupancy_data.std()) if len(occupancy_data) > 1 else 0
        }
    
    def _calculate_work_order_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate work order trend metrics."""
        if df.empty:
            return {}
        
        wo_data = df['work_orders_count'].dropna()
        
        return {
            'current': int(wo_data.iloc[-1]) if not wo_data.empty else 0,
            'average': float(wo_data.mean()),
            'total_period': int(wo_data.sum()),
            'max_week': int(wo_data.max()),
            'weeks_with_orders': int((wo_data > 0).sum())
        }
    
    def _calculate_make_ready_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate make ready trend metrics."""
        if df.empty:
            return {}
        
        mr_data = df['make_readies_count'].dropna()
        
        return {
            'current': int(mr_data.iloc[-1]) if not mr_data.empty else 0,
            'average': float(mr_data.mean()),
            'max_week': int(mr_data.max()),
            'total_period': int(mr_data.sum())
        }
    
    def _get_recent_performance(self, df: pd.DataFrame, weeks: int = 4) -> Dict[str, Any]:
        """Get performance metrics for recent weeks."""
        if df.empty:
            return {}
        
        recent_df = df.tail(weeks)
        
        return {
            'weeks_analyzed': len(recent_df),
            'avg_occupancy': float(recent_df['occupancy_percent'].mean()),
            'avg_leased': float(recent_df['leased_percent'].mean()),
            'total_work_orders': int(recent_df['work_orders_count'].sum()),
            'avg_make_ready': float(recent_df['make_readies_count'].mean())
        }
    
    def _calculate_monthly_averages(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Calculate monthly averages for trending."""
        if df.empty:
            return []
        
        df_copy = df.copy()
        df_copy['year_month'] = df_copy['date'].dt.to_period('M')
        
        monthly_stats = []
        
        for period, group in df_copy.groupby('year_month'):
            stats = {
                'period': str(period),
                'avg_occupancy': float(group['occupancy_percent'].mean()),
                'avg_leased': float(group['leased_percent'].mean()),
                'total_work_orders': int(group['work_orders_count'].sum()),
                'avg_make_ready': float(group['make_readies_count'].mean()),
                'weeks_in_month': len(group)
            }
            monthly_stats.append(stats)
        
        return monthly_stats
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary statistics across all properties."""
        if not self.property_data:
            return {}
        
        summary = {
            'total_properties': len(self.property_data),
            'properties_with_historical_data': 0,
            'total_historical_weeks': 0,
            'date_range': {'earliest': None, 'latest': None},
            'aggregate_metrics': {}
        }
        
        all_occupancies = []
        all_work_orders = []
        all_dates = []
        
        for prop_data in self.property_data.values():
            historical = prop_data.get('historical_data', {})
            weekly_data = historical.get('weekly_occupancy_data', [])
            
            if weekly_data:
                summary['properties_with_historical_data'] += 1
                summary['total_historical_weeks'] += len(weekly_data)
                
                for week in weekly_data:
                    all_occupancies.append(week.get('occupancy_percent', 0))
                    all_work_orders.append(week.get('work_orders_count', 0))
                    all_dates.append(week.get('date'))
        
        if all_dates:
            valid_dates = [d for d in all_dates if d is not None]
            if valid_dates:
                summary['date_range']['earliest'] = min(valid_dates).isoformat()
                summary['date_range']['latest'] = max(valid_dates).isoformat()
        
        if all_occupancies:
            summary['aggregate_metrics'] = {
                'avg_occupancy_all_properties': sum(all_occupancies) / len(all_occupancies),
                'total_work_orders_all_properties': sum(all_work_orders),
                'avg_work_orders_per_week': sum(all_work_orders) / len(all_work_orders) if all_work_orders else 0
            }
        
        return summary
    
    def export_historical_data(self, output_path: str, format_type: str = 'json') -> bool:
        """
        Export aggregated historical data to file.
        
        Args:
            output_path: Path for output file
            format_type: 'json' or 'csv'
            
        Returns:
            True if successful, False otherwise
        """
        try:
            trends = self.get_historical_trends()
            
            if format_type.lower() == 'json':
                import json
                with open(output_path, 'w') as f:
                    json.dump(trends, f, indent=2, default=str)
            elif format_type.lower() == 'csv':
                # Flatten data for CSV export
                rows = []
                for prop_name, prop_trends in trends.items():
                    if 'monthly_averages' in prop_trends:
                        for month_data in prop_trends['monthly_averages']:
                            row = {
                                'property': prop_name,
                                'period': month_data['period'],
                                'avg_occupancy': month_data['avg_occupancy'],
                                'avg_leased': month_data['avg_leased'],
                                'total_work_orders': month_data['total_work_orders'],
                                'avg_make_ready': month_data['avg_make_ready']
                            }
                            rows.append(row)
                
                df = pd.DataFrame(rows)
                df.to_csv(output_path, index=False)
            
            return True
            
        except Exception as e:
            print(f"Error exporting data: {e}")
            return False


def parse_comprehensive_reports_directory(reports_path: str) -> Dict[str, Any]:
    """
    Convenience function to parse all comprehensive reports in a directory.
    
    Args:
        reports_path: Path to the Comprehensive Reports directory
        
    Returns:
        Dictionary containing all parsed historical data
    """
    parser = ComprehensiveHistoricalParser(reports_path)
    
    # Parse all properties
    results = parser.parse_all_properties()
    
    # Add aggregated trends
    results['historical_trends'] = parser.get_historical_trends()
    
    return results


if __name__ == "__main__":
    # Test the comprehensive historical parser
    reports_path = "/Users/shivaanikomanduri/ArcanClean/data/Comprehensive Reports"
    
    print("=== COMPREHENSIVE HISTORICAL PARSER TEST ===")
    
    parser = ComprehensiveHistoricalParser(reports_path)
    
    # Discover properties
    properties = parser.discover_property_reports()
    print(f"\nDiscovered {len(properties)} property reports:")
    for prop_name in properties.keys():
        print(f"  - {prop_name}")
    
    # Parse a sample property (limit to avoid long output)
    if "Marbella" in properties:
        print(f"\n=== Parsing Marbella Historical Data ===")
        marbella_data = parse_file(properties["Marbella"])
        
        if 'historical_data' in marbella_data:
            historical = marbella_data['historical_data']['weekly_occupancy_data']
            print(f"Found {len(historical)} historical weeks")
            
            parser.property_data["Marbella"] = marbella_data
            trends = parser.get_historical_trends("Marbella")
            
            print(f"\nMarbella Trends Summary:")
            print(f"  - Data Range: {trends['date_range']['start']} to {trends['date_range']['end']}")
            print(f"  - Average Occupancy: {trends['occupancy_trends']['average']:.1%}")
            print(f"  - Current Occupancy: {trends['occupancy_trends']['current']:.1%}")
            print(f"  - Total Work Orders: {trends['work_order_trends']['total_period']}")
            print(f"  - Monthly Data Points: {len(trends['monthly_averages'])}")
