"""
S3 Data Service for Excel file operations
S3-only implementation for cloud deployment
"""

import os
import io
from typing import List, Dict, Optional, Any
from datetime import datetime
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

# Try to import pandas for Parquet support
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class S3DataService:
    """S3-only service for file operations"""
    
    def __init__(self):
        self.bucket_name = os.environ.get("S3_BUCKET_NAME")
        self.s3_prefix = os.environ.get("S3_DATA_PREFIX", "data/")
        self.historical_prefix = "historicaldata/"
        
        if not self.bucket_name:
            raise ValueError("S3_BUCKET_NAME environment variable is required")
        
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
                region_name=os.environ.get("AWS_REGION", "us-east-1")
            )
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except (ClientError, NoCredentialsError) as e:
            raise ConnectionError(f"Failed to connect to S3: {str(e)}")
    
    def list_weeks(self) -> List[str]:
        """List available week directories (MM_DD_YYYY format)"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=self.s3_prefix,
                Delimiter='/'
            )
            weeks = []
            for prefix_info in response.get('CommonPrefixes', []):
                prefix = prefix_info['Prefix']
                week_name = prefix.replace(self.s3_prefix, '').rstrip('/')
                if '_' in week_name and not week_name.startswith('.'):
                    weeks.append(week_name)
            weeks.sort()
            return weeks
        except ClientError:
            return []
    
    def list_properties(self, week: str) -> List[str]:
        """List available properties for a given week"""
        
        try:
            week_prefix = f"{self.s3_prefix}{week}/"
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=week_prefix,
                Delimiter='/'
            )
            
            properties = []
            for prefix_info in response.get('CommonPrefixes', []):
                prefix = prefix_info['Prefix']
                # Extract property name from prefix
                property_name = prefix.replace(week_prefix, '').rstrip('/')
                
                if property_name and not property_name.startswith('.'):
                    properties.append(property_name)
            
            properties.sort()
            return properties
            
        except ClientError:
            return []
    
    def list_files(self, folder_path: str) -> List[str]:
        """List files in a specific S3 folder"""
        
        try:
            # Handle both absolute paths and relative paths
            if folder_path.startswith(self.s3_prefix):
                s3_prefix = folder_path + '/' if not folder_path.endswith('/') else folder_path
            else:
                s3_prefix = f"{self.s3_prefix}{folder_path}/"
            
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=s3_prefix
            )
            
            
            files = []
            for obj in response.get('Contents', []):
                file_path = obj['Key']
                # Extract just the filename
                filename = file_path.replace(s3_prefix, '')
                
                if filename and '/' not in filename:  # Only direct files, not subdirectories
                    files.append(filename)
            
            return files
            
        except ClientError:
            return []
    
    def read_file(self, s3_key: str) -> bytes:
        """Read file content from S3"""
        
        try:
            # Handle both absolute and relative paths
            if not s3_key.startswith(self.s3_prefix):
                s3_key = f"{self.s3_prefix}{s3_key}"
            
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            return response['Body'].read()
            
        except ClientError:
            raise FileNotFoundError(f"File not found in S3: {s3_key}")
    
    def write_file(self, s3_key: str, content: bytes) -> bool:
        """Write file content to S3"""
        
        try:
            # Handle both absolute and relative paths
            if not s3_key.startswith(self.s3_prefix):
                s3_key = f"{self.s3_prefix}{s3_key}"
            
            self.s3_client.put_object(
                Bucket=self.bucket_name, 
                Key=s3_key, 
                Body=content
            )
            return True
            
        except ClientError:
            return False
    
    def file_exists(self, s3_key: str) -> bool:
        """Check if file exists in S3"""
        
        try:
            # Handle both absolute and relative paths
            if not s3_key.startswith(self.s3_prefix):
                s3_key = f"{self.s3_prefix}{s3_key}"
            
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError:
            return False
    
    def backup_file(self, s3_key: str) -> bool:
        """Create backup of file in S3 (copy with .backup_ prefix)"""
        
        try:
            # Handle both absolute and relative paths
            if not s3_key.startswith(self.s3_prefix):
                s3_key = f"{self.s3_prefix}{s3_key}"
            
            # Create backup key with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_key = s3_key.replace(self.s3_prefix, f"{self.s3_prefix}backups/")
            backup_key = f"{backup_key}.backup_{timestamp}"
            
            # Copy original to backup location
            copy_source = {'Bucket': self.bucket_name, 'Key': s3_key}
            self.s3_client.copy_object(
                CopySource=copy_source,
                Bucket=self.bucket_name,
                Key=backup_key
            )
            return True
            
        except ClientError:
            return False
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get information about current storage configuration"""

        return {
            'type': 'S3',
            'bucket': self.bucket_name,
            'prefix': self.s3_prefix,
            'region': os.environ.get("AWS_REGION", "us-east-1"),
            'location': self.bucket_name,
            'connected': True
        }

    # =========================================================================
    # Historical Data Methods (Parquet)
    # =========================================================================

    def list_historical_properties(self) -> List[str]:
        """List properties that have historical data in S3."""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=self.historical_prefix,
                Delimiter='/'
            )
            properties = []
            for prefix_info in response.get('CommonPrefixes', []):
                prefix = prefix_info['Prefix']
                property_name = prefix.replace(self.historical_prefix, '').rstrip('/')
                if property_name and not property_name.startswith('.'):
                    properties.append(property_name)
            return sorted(properties)
        except ClientError:
            return []

    def list_historical_years(self, property_name: str) -> List[str]:
        """List years available for a property's historical data in S3."""
        try:
            prefix = f"{self.historical_prefix}{property_name}/"
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                Delimiter='/'
            )
            years = []
            for prefix_info in response.get('CommonPrefixes', []):
                year_prefix = prefix_info['Prefix']
                year = year_prefix.replace(prefix, '').rstrip('/')
                if year.isdigit():
                    years.append(year)
            return sorted(years)
        except ClientError:
            return []

    def read_historical_data(self, property_name: str, data_type: str,
                            year: Optional[str] = None) -> Optional[Any]:
        """Read historical data from Parquet files in S3.

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

        if year:
            # Read specific year
            s3_key = f"{self.historical_prefix}{property_name}/{year}/{data_type}.parquet"
            try:
                response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
                return pd.read_parquet(io.BytesIO(response['Body'].read()))
            except ClientError:
                return None
        else:
            # Read all years and concatenate
            all_data = []
            for yr in self.list_historical_years(property_name):
                s3_key = f"{self.historical_prefix}{property_name}/{yr}/{data_type}.parquet"
                try:
                    response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
                    df = pd.read_parquet(io.BytesIO(response['Body'].read()))
                    all_data.append(df)
                except ClientError:
                    continue

            if all_data:
                return pd.concat(all_data, ignore_index=True)
            return None

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


def get_storage_service():
    """Get configured storage service instance - S3 or Local based on environment"""
    import os
    
    # Check if S3 environment variables are set
    s3_bucket = os.getenv('S3_BUCKET_NAME')
    
    if s3_bucket:
        # Use S3 service if bucket is configured
        return S3DataService()
    else:
        # Fall back to local data service for development
        from .local_data_service import LocalDataService
        print("🔧 S3_BUCKET_NAME not set, using local data service")
        return LocalDataService()