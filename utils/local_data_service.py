"""Local file system data service for development.

Mirrors the S3 bucket structure locally:
  bucket_copy/
  ├── data/              <- Weekly Yardi reports (same as S3 data/)
  ├── historicaldata/    <- Aggregated historical data (Parquet files)
  └── logos/             <- Property logos
"""

import os
import glob
from typing import List, Optional, Dict, Any
from datetime import datetime

# Try to import pandas/pyarrow for Parquet support
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class LocalDataService:
    """Local file system service for file operations.

    Mirrors S3 bucket structure with bucket_copy/ as the root.
    """

    def __init__(self, base_path: str = "bucket_copy"):
        """Initialize with base path for local data.

        Args:
            base_path: Root directory that mirrors S3 bucket structure.
                       Defaults to 'bucket_copy' which should contain:
                       - data/ (weekly reports)
                       - historicaldata/ (aggregated Parquet files)
                       - logos/ (property logos)
        """
        self.base_path = base_path
        self.data_path = os.path.join(base_path, "data")
        self.historical_path = os.path.join(base_path, "historicaldata")
        self.logos_path = os.path.join(base_path, "logos")

        # Create directories if they don't exist
        for path in [self.data_path, self.historical_path, self.logos_path]:
            os.makedirs(path, exist_ok=True)

    def list_weeks(self) -> List[str]:
        """List available weeks (subdirectories in data/)."""
        weeks = []
        if os.path.exists(self.data_path):
            for item in os.listdir(self.data_path):
                item_path = os.path.join(self.data_path, item)
                if os.path.isdir(item_path) and item != 'backups':
                    weeks.append(item)
        return sorted(weeks)

    def list_properties(self, week: str) -> List[str]:
        """List available properties for a given week."""
        week_path = os.path.join(self.data_path, week)
        properties = []

        if os.path.exists(week_path):
            for item in os.listdir(week_path):
                item_path = os.path.join(week_path, item)
                if os.path.isdir(item_path):
                    properties.append(item)

        return sorted(properties)

    def list_files(self, folder_path: str, property_name: Optional[str] = None) -> List[str]:
        """List files in a specific folder."""
        if property_name:
            # Handle the two-parameter version: list_files(week, property_name)
            week = folder_path
            full_path = os.path.join(self.data_path, week, property_name)
        else:
            # Handle the one-parameter version: list_files(folder_path)
            if folder_path.startswith(self.base_path):
                full_path = folder_path
            else:
                full_path = os.path.join(self.data_path, folder_path)

        files = []
        if os.path.exists(full_path):
            for item in os.listdir(full_path):
                item_path = os.path.join(full_path, item)
                if os.path.isfile(item_path) and item.lower().endswith('.xlsx'):
                    files.append(item)

        return sorted(files)

    def read_file(self, file_path: str) -> bytes:
        """Read file content from local filesystem."""
        # Handle paths that might include 'data/' prefix
        if not os.path.isabs(file_path):
            if file_path.startswith('data/'):
                file_path = os.path.join(self.base_path, file_path)
            elif not file_path.startswith(self.base_path):
                file_path = os.path.join(self.data_path, file_path)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, 'rb') as f:
            return f.read()

    # =========================================================================
    # Historical Data Methods (Parquet)
    # =========================================================================

    def list_historical_properties(self) -> List[str]:
        """List properties that have historical data."""
        properties = []
        if os.path.exists(self.historical_path):
            for item in os.listdir(self.historical_path):
                item_path = os.path.join(self.historical_path, item)
                if os.path.isdir(item_path):
                    properties.append(item)
        return sorted(properties)

    def list_historical_years(self, property_name: str) -> List[str]:
        """List years available for a property's historical data."""
        property_path = os.path.join(self.historical_path, property_name)
        years = []
        if os.path.exists(property_path):
            for item in os.listdir(property_path):
                item_path = os.path.join(property_path, item)
                if os.path.isdir(item_path) and item.isdigit():
                    years.append(item)
        return sorted(years)

    def read_historical_data(self, property_name: str, data_type: str,
                            year: Optional[str] = None) -> Optional[Any]:
        """Read historical data from Parquet files.

        Args:
            property_name: Name of the property
            data_type: Type of data ('occupancy', 'maintenance', 'financial')
            year: Optional year filter. If None, reads all years.

        Returns:
            pandas DataFrame with the historical data, or None if not available
        """
        if not PANDAS_AVAILABLE:
            print("Warning: pandas not available, cannot read Parquet files")
            return None

        property_path = os.path.join(self.historical_path, property_name)

        if not os.path.exists(property_path):
            return None

        if year:
            # Read specific year
            file_path = os.path.join(property_path, year, f"{data_type}.parquet")
            if os.path.exists(file_path):
                return pd.read_parquet(file_path)
            return None
        else:
            # Read all years and concatenate
            all_data = []
            for yr in self.list_historical_years(property_name):
                file_path = os.path.join(property_path, yr, f"{data_type}.parquet")
                if os.path.exists(file_path):
                    df = pd.read_parquet(file_path)
                    all_data.append(df)

            if all_data:
                return pd.concat(all_data, ignore_index=True)
            return None

    def write_historical_data(self, property_name: str, year: str,
                             data_type: str, data: Any) -> bool:
        """Write historical data to Parquet file.

        Args:
            property_name: Name of the property
            year: Year for the data
            data_type: Type of data ('occupancy', 'maintenance', 'financial')
            data: pandas DataFrame to write

        Returns:
            True if successful, False otherwise
        """
        if not PANDAS_AVAILABLE:
            print("Warning: pandas not available, cannot write Parquet files")
            return False

        year_path = os.path.join(self.historical_path, property_name, year)
        os.makedirs(year_path, exist_ok=True)

        file_path = os.path.join(year_path, f"{data_type}.parquet")

        try:
            data.to_parquet(file_path, index=False)
            return True
        except Exception as e:
            print(f"Error writing Parquet file: {e}")
            return False

    def get_historical_data_for_graphs(self, property_name: str) -> Dict[str, Any]:
        """Get all historical data for a property formatted for graph rendering.

        Returns a dictionary compatible with the existing graph rendering code.
        """
        result = {
            'weekly_occupancy_data': [],
            'financial_trends': {
                'rent_data': []
            }
        }

        if not PANDAS_AVAILABLE:
            return result

        # Read occupancy data
        occ_df = self.read_historical_data(property_name, 'occupancy')
        if occ_df is not None and not occ_df.empty:
            for _, row in occ_df.iterrows():
                entry = {
                    'date': pd.to_datetime(row.get('date')),
                    'occupancy_percentage': row.get('occupancy_pct', 0),
                    'leased_percentage': row.get('leased_pct', row.get('occupancy_pct', 0)),
                    'projected_percentage': row.get('projected_pct', row.get('occupancy_pct', 0)),
                    'work_orders_count': 0,
                    'make_readies_count': 0
                }
                result['weekly_occupancy_data'].append(entry)

        # Read maintenance data and merge
        maint_df = self.read_historical_data(property_name, 'maintenance')
        if maint_df is not None and not maint_df.empty:
            # Create lookup by date
            maint_lookup = {}
            for _, row in maint_df.iterrows():
                date_str = str(row.get('date'))[:10]
                maint_lookup[date_str] = {
                    'work_orders': row.get('work_orders', 0),
                    'make_readies': row.get('make_readies', 0)
                }

            # Merge with occupancy data
            for entry in result['weekly_occupancy_data']:
                date_str = entry['date'].strftime('%Y-%m-%d') if hasattr(entry['date'], 'strftime') else str(entry['date'])[:10]
                if date_str in maint_lookup:
                    entry['work_orders_count'] = maint_lookup[date_str]['work_orders']
                    entry['make_readies_count'] = maint_lookup[date_str]['make_readies']

        # Read financial data
        fin_df = self.read_historical_data(property_name, 'financial')
        if fin_df is not None and not fin_df.empty:
            for _, row in fin_df.iterrows():
                rent_entry = {
                    'date': pd.to_datetime(row.get('date')),
                    'market_rent': row.get('market_rent'),
                    'occupied_rent': row.get('occupied_rent'),
                    'revenue': row.get('revenue'),
                    'expenses': row.get('expenses'),
                    'collections': row.get('collections_pct')
                }
                result['financial_trends']['rent_data'].append(rent_entry)

        # Sort by date
        result['weekly_occupancy_data'].sort(key=lambda x: x['date'])
        result['financial_trends']['rent_data'].sort(key=lambda x: x['date'])

        return result

    def test_connection(self) -> dict:
        """Test the local data service."""
        return {
            'status': 'success',
            'service': 'local',
            'base_path': self.base_path,
            'data_path': self.data_path,
            'historical_path': self.historical_path,
            'weeks_available': len(self.list_weeks()),
            'historical_properties': len(self.list_historical_properties()),
            'connected': True
        }

    def get_storage_info(self) -> Dict[str, Any]:
        """Get information about current storage configuration."""
        return {
            'type': 'Local',
            'base_path': self.base_path,
            'data_path': self.data_path,
            'historical_path': self.historical_path,
            'location': os.path.abspath(self.base_path),
            'connected': os.path.exists(self.base_path)
        }
