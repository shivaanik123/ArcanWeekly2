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
                # Skip non-directories and special folders like "Comprehensive Reports"
                if os.path.isdir(item_path) and item != "Comprehensive Reports":
                    # Only include directories that look like date patterns (MM_DD_YYYY)
                    if '_' in item and len(item.split('_')) == 3:
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
            # First, check if there are direct Excel files
            for item in os.listdir(full_path):
                item_path = os.path.join(full_path, item)
                if os.path.isfile(item_path) and item.lower().endswith('.xlsx') and not item.startswith('~$'):
                    files.append(item)
            
            # If no direct files found, check subdirectories for Excel files
            if not files:
                for item in os.listdir(full_path):
                    item_path = os.path.join(full_path, item)
                    if os.path.isdir(item_path):
                        # Check subdirectory for Excel files
                        for subitem in os.listdir(item_path):
                            subitem_path = os.path.join(item_path, subitem)
                            if os.path.isfile(subitem_path) and subitem.lower().endswith('.xlsx') and not subitem.startswith('~$'):
                                files.append(subitem)
                        # If files found in subdirectory, update the full_path for read_file method
                        if files:
                            print(f"🔍 LOCAL_DATA: Found {len(files)} files in subdirectory {item}")
                            break
        
        return sorted(files)
    
    def read_file(self, file_path: str) -> bytes:
        """Read file content from local filesystem"""
        if not file_path.startswith(self.base_path):
            file_path = os.path.join(self.base_path, file_path)
        
        # If file doesn't exist directly, try to find it in subdirectories
        if not os.path.exists(file_path):
            # Extract the filename and search for it
            filename = os.path.basename(file_path)
            dir_path = os.path.dirname(file_path)
            
            # Search in subdirectories
            if os.path.exists(dir_path):
                for root, dirs, files in os.walk(dir_path):
                    for file in files:
                        if file == filename:
                            file_path = os.path.join(root, file)
                            break
                    if os.path.exists(file_path):
                        break
        
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


