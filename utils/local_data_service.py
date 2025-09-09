"""Local file system data service for development"""

import os
import glob
from typing import List, Optional


class LocalDataService:
    """Local file system service for file operations"""
    
    def __init__(self, base_path: str = "test_data"):
        """Initialize with base path for local data"""
        self.base_path = base_path
        if not os.path.exists(self.base_path):
            raise ValueError(f"Local data path does not exist: {self.base_path}")
    
    def list_weeks(self) -> List[str]:
        """List available weeks (subdirectories in base path)"""
        weeks = []
        if os.path.exists(self.base_path):
            for item in os.listdir(self.base_path):
                item_path = os.path.join(self.base_path, item)
                if os.path.isdir(item_path):
                    weeks.append(item)
        return sorted(weeks)
    
    def list_properties(self, week: str) -> List[str]:
        """List available properties for a given week"""
        week_path = os.path.join(self.base_path, week)
        properties = []
        
        if os.path.exists(week_path):
            for item in os.listdir(week_path):
                item_path = os.path.join(week_path, item)
                if os.path.isdir(item_path):
                    properties.append(item)
        
        return sorted(properties)
    
    def list_files(self, folder_path: str, property_name: Optional[str] = None) -> List[str]:
        """List files in a specific folder"""
        if property_name:
            # Handle the two-parameter version: list_files(week, property_name)
            week = folder_path
            full_path = os.path.join(self.base_path, week, property_name)
        else:
            # Handle the one-parameter version: list_files(folder_path)
            if folder_path.startswith(self.base_path):
                full_path = folder_path
            else:
                full_path = os.path.join(self.base_path, folder_path)
        
        files = []
        if os.path.exists(full_path):
            for item in os.listdir(full_path):
                item_path = os.path.join(full_path, item)
                if os.path.isfile(item_path) and item.lower().endswith('.xlsx'):
                    files.append(item)
        
        return sorted(files)
    
    def read_file(self, file_path: str) -> bytes:
        """Read file content from local filesystem"""
        if not file_path.startswith(self.base_path):
            file_path = os.path.join(self.base_path, file_path)
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'rb') as f:
            return f.read()
    
    def test_connection(self) -> dict:
        """Test the local data service"""
        return {
            'status': 'success',
            'service': 'local',
            'base_path': self.base_path,
            'weeks_available': len(self.list_weeks()),
            'connected': True
        }


