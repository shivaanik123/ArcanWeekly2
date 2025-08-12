"""
Data processor that orchestrates all calculations and prepares data for dashboard components
"""

from typing import Dict, Any
from datetime import datetime
import sys
import os

# Add utils to path
sys.path.append(os.path.dirname(__file__))
from ..utils.calculations import (
    get_box_score_metrics,
    get_move_schedule,
    get_unit_counts,
    calculate_projection,
    calculate_net_to_rent,
    calculate_collections_rate,
    get_traffic_metrics,
    get_residents_on_notice_metrics
)

class DashboardDataProcessor:
    """
    Main class for processing raw parsed data into dashboard-ready metrics
    """
    
    def __init__(self, raw_data: Dict[str, Any], week_start: datetime):
        self.raw_data = raw_data
        self.week_start = week_start
        self.processed_metrics = {}
        
    def process_all_metrics(self) -> Dict[str, Any]:
        """
        Process all available data and calculate dashboard metrics.
        
        Returns:
            Dictionary with all processed metrics organized by category
        """
        # Initialize metrics structure
        self.processed_metrics = {
            'kpi_cards': {},
            'current_occupancy': {},
            'projections_applications': {},
            'maintenance': {},
            'move_schedule': {},
            'errors': [],
            'data_availability': {}
        }
        
        # Check data availability
        self.processed_metrics['data_availability'] = self._check_data_availability()
        
        # Process each data type if available
        try:
            # Box Score metrics (required for most calculations)
            box_score_metrics = {}
            if 'resanalytics_box_score' in self.raw_data['raw_data']:
                box_score_data = self.raw_data['raw_data']['resanalytics_box_score']
                box_score_metrics = get_box_score_metrics(box_score_data)
                self.processed_metrics['box_score_metrics'] = box_score_metrics
                
                # Traffic metrics from box score
                traffic_metrics = get_traffic_metrics(box_score_data)
                self.processed_metrics['traffic_metrics'] = traffic_metrics
                
                # Current occupancy metrics
                self.processed_metrics['current_occupancy'] = self._process_current_occupancy(box_score_metrics)
                
            # Residents on Notice metrics (NEW - for eviction data)
            residents_metrics = {}
            if 'residents_on_notice' in self.raw_data['raw_data']:
                residents_data = self.raw_data['raw_data']['residents_on_notice']
                residents_metrics = get_residents_on_notice_metrics(residents_data)
                self.processed_metrics['residents_metrics'] = residents_metrics
                
                # Update current occupancy with residents data
                if 'current_occupancy' in self.processed_metrics:
                    self.processed_metrics['current_occupancy'].update({
                        'notice_units': residents_metrics.get('notice_units', 0),
                        'under_eviction': residents_metrics.get('under_eviction', 0)  # REAL EVICTION DATA!
                    })
                
            # Unit availability metrics
            unit_metrics = {}
            if 'resanalytics_unit_availability' in self.raw_data['raw_data']:
                unit_data = self.raw_data['raw_data']['resanalytics_unit_availability']
                unit_metrics = get_unit_counts(unit_data)
                self.processed_metrics['unit_metrics'] = unit_metrics
                
                # Move schedule metrics
                move_metrics = get_move_schedule(unit_data, self.week_start)
                self.processed_metrics['move_schedule'] = move_metrics
                
                # Update current occupancy with unit-level details
                if 'current_occupancy' in self.processed_metrics:
                    self.processed_metrics['current_occupancy'].update({
                        'pre_leased': box_score_metrics.get('notice_rented', 0),  # From box score
                        'vacant_rentable': box_score_metrics.get('vacant_unrented', 0),
                        'leased_vacant': box_score_metrics.get('vacant_rented', 0)
                    })
                    
                    # Calculate Net to Rent
                    if box_score_metrics:
                        # Merge all metrics for calculation
                        combined_metrics = {**unit_metrics, **residents_metrics}
                        combined_metrics['vacant_rentable'] = box_score_metrics.get('vacant_unrented', 0)
                        combined_metrics['leased_vacant'] = box_score_metrics.get('vacant_rented', 0)
                        combined_metrics['pre_leased'] = box_score_metrics.get('notice_rented', 0)
                        
                        net_to_rent = calculate_net_to_rent(box_score_metrics, combined_metrics)
                        self.processed_metrics['current_occupancy']['net_to_rent'] = net_to_rent
            
            # Maintenance metrics
            work_order_count = 0
            make_ready_count = 0
            
            if 'work_order_report' in self.raw_data['raw_data']:
                work_order_data = self.raw_data['raw_data']['work_order_report']
                if 'work_order_data' in work_order_data and not work_order_data['work_order_data'].empty:
                    work_order_count = len(work_order_data['work_order_data'])
            
            if 'pending_make_ready' in self.raw_data['raw_data']:
                make_ready_data = self.raw_data['raw_data']['pending_make_ready']
                if 'make_ready_data' in make_ready_data and not make_ready_data['make_ready_data'].empty:
                    make_ready_count = len(make_ready_data['make_ready_data'])
            
            self.processed_metrics['maintenance'] = {
                'work_orders': work_order_count,
                'make_ready': make_ready_count
            }
            
            # Collections rate
            collections_rate = 0.0
            if 'resaranalytics_delinquency' in self.raw_data['raw_data']:
                delinquency_data = self.raw_data['raw_data']['resaranalytics_delinquency']
                collections_rate = calculate_collections_rate(delinquency_data, box_score_metrics)
            
            # KPI Cards (requires box score and move metrics)
            if box_score_metrics and 'move_schedule' in self.processed_metrics:
                projection_metrics = calculate_projection(box_score_metrics, self.processed_metrics['move_schedule'])
                
                self.processed_metrics['kpi_cards'] = {
                    'projection_percent': projection_metrics['projection_percent'],
                    'status': projection_metrics['status'],
                    'percent_leased': box_score_metrics.get('percent_leased', 0.0),
                    'percent_occupied': box_score_metrics.get('percent_occupied', 0.0),
                    'collections_rate': collections_rate
                }
            
            # Projections & Applications
            self.processed_metrics['projections_applications'] = {
                'total_projected_percent': self.processed_metrics.get('kpi_cards', {}).get('projection_percent', 0),
                'total_traffic': self.processed_metrics.get('traffic_metrics', {}).get('total_traffic', 0),
                'total_applications': self.processed_metrics.get('traffic_metrics', {}).get('total_applications', 0),
                'approved': self.processed_metrics.get('traffic_metrics', {}).get('approved', 0),
                'cancelled': self.processed_metrics.get('traffic_metrics', {}).get('cancelled', 0),
                'denied': self.processed_metrics.get('traffic_metrics', {}).get('denied', 0)
            }
            
        except Exception as e:
            self.processed_metrics['errors'].append(f"Error processing metrics: {str(e)}")
        
        return self.processed_metrics
    
    def _check_data_availability(self) -> Dict[str, bool]:
        """Check which data files are available"""
        required_files = [
            'resanalytics_box_score',
            'work_order_report',
            'resanalytics_unit_availability',
            'pending_make_ready',
            'resaranalytics_delinquency',
            'residents_on_notice'
        ]
        
        availability = {}
        raw_data = self.raw_data.get('raw_data', {})
        
        for file_type in required_files:
            availability[file_type] = file_type in raw_data
        
        return availability
    
    def _process_current_occupancy(self, box_score_metrics: Dict[str, float]) -> Dict[str, Any]:
        """Process current occupancy metrics"""
        return {
            'occupied_units': box_score_metrics.get('occupied_units', 0),
            'model_down_units': box_score_metrics.get('model_down', 0),
            'vacant_rentable': box_score_metrics.get('vacant_unrented', 0),
            'leased_vacant': box_score_metrics.get('vacant_rented', 0),
            'total_units': box_score_metrics.get('total_units', 0),
            'percent_occupied': box_score_metrics.get('percent_occupied', 0)
        }

def process_dashboard_data(raw_data: Dict[str, Any], week_start: datetime) -> Dict[str, Any]:
    """
    Convenience function to process dashboard data.
    
    Args:
        raw_data: Raw data from loader
        week_start: Start date of the week
        
    Returns:
        Processed metrics for dashboard
    """
    processor = DashboardDataProcessor(raw_data, week_start)
    return processor.process_all_metrics()
