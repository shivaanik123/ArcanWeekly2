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


class S3DataService:
    """S3-only service for file operations"""
    
    def __init__(self):
        self.bucket_name = os.environ.get("S3_BUCKET_NAME")
        self.s3_prefix = os.environ.get("S3_DATA_PREFIX", "data/")
        
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