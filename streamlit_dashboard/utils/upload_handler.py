"""
ETL Report Upload Handler
Handles file uploads, validation, and storage for ETL reports
"""

import streamlit as st
import os
import shutil
from typing import List, Dict, Any
from datetime import datetime
import sys

# Add parent directory to path for parsers
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

def process_etl_uploads(uploaded_files: List, property_name: str, week: str) -> Dict[str, Any]:
    """
    Process uploaded ETL files for a specific property and week.
    
    Args:
        uploaded_files: List of uploaded file objects from Streamlit
        property_name: Name of the property
        week: Week identifier (MM_DD_YYYY format)
    
    Returns:
        Dictionary with upload results
    """
    results = {
        'success': [],
        'errors': [],
        'total_files': len(uploaded_files)
    }
    
    # Create upload directory structure
    base_path = "/Users/jsai23/Workspace/Arcan/data"
    week_path = os.path.join(base_path, week)
    property_path = os.path.join(week_path, property_name)
    
    try:
        # Create directories if they don't exist
        os.makedirs(property_path, exist_ok=True)
        
        for uploaded_file in uploaded_files:
            try:
                # Validate file
                validation_result = validate_etl_file(uploaded_file)
                if not validation_result['valid']:
                    results['errors'].append(f"{uploaded_file.name}: {validation_result['error']}")
                    continue
                
                # Save file
                file_path = os.path.join(property_path, uploaded_file.name)
                
                # Check if file already exists
                if os.path.exists(file_path):
                    # Create backup of existing file
                    backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    shutil.move(file_path, backup_path)
                    results['success'].append(f"Backed up existing {uploaded_file.name}")
                
                # Write new file
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                results['success'].append(f"Uploaded {uploaded_file.name}")
                
            except Exception as e:
                results['errors'].append(f"{uploaded_file.name}: {str(e)}")
        
        # Show results
        if results['success']:
            st.sidebar.success(f"✅ Successfully uploaded {len(results['success'])} files")
            for success_msg in results['success']:
                st.sidebar.write(f"  • {success_msg}")
        
        if results['errors']:
            st.sidebar.error(f"❌ {len(results['errors'])} files failed")
            for error_msg in results['errors']:
                st.sidebar.write(f"  • {error_msg}")
        
        # Refresh the page to show new data
        if results['success'] and not results['errors']:
            st.sidebar.info("🔄 Refresh the page to see updated data")
            
    except Exception as e:
        st.sidebar.error(f"Upload failed: {str(e)}")
        results['errors'].append(f"System error: {str(e)}")
    
    return results

def validate_etl_file(uploaded_file) -> Dict[str, Any]:
    """
    Validate an uploaded ETL file.
    
    Args:
        uploaded_file: Streamlit uploaded file object
    
    Returns:
        Dictionary with validation result
    """
    result = {'valid': True, 'error': None}
    
    # Check file extension
    if not uploaded_file.name.lower().endswith('.xlsx'):
        result['valid'] = False
        result['error'] = "File must be an Excel (.xlsx) file"
        return result
    
    # Check file size (max 50MB)
    if uploaded_file.size > 50 * 1024 * 1024:
        result['valid'] = False
        result['error'] = "File size must be less than 50MB"
        return result
    
    # Check filename patterns (basic validation)
    filename = uploaded_file.name.lower()
    expected_patterns = [
        'box_score', 'unit_availability', 'work_order', 'make_ready',
        'delinquency', 'residents_on_notice', 'lease_expiration', 'market_rent'
    ]
    
    # Check if filename contains any expected pattern
    if not any(pattern in filename for pattern in expected_patterns):
        result['valid'] = False
        result['error'] = f"Filename should contain one of: {', '.join(expected_patterns)}"
        return result
    
    return result

def get_upload_history(property_name: str = None, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get recent upload history.
    
    Args:
        property_name: Filter by property name (optional)
        limit: Maximum number of records to return
    
    Returns:
        List of upload records
    """
    # This would typically query a database or log file
    # For now, return empty list - can be implemented later
    return []

def cleanup_old_backups(days_old: int = 30) -> int:
    """
    Clean up old backup files.
    
    Args:
        days_old: Remove backups older than this many days
    
    Returns:
        Number of files cleaned up
    """
    base_path = "/Users/jsai23/Workspace/Arcan/data/"
    cleaned_count = 0
    
    try:
        for root, dirs, files in os.walk(base_path):
            for file in files:
                if '.backup_' in file:
                    file_path = os.path.join(root, file)
                    # Check file age
                    file_age = datetime.now() - datetime.fromtimestamp(os.path.getctime(file_path))
                    if file_age.days > days_old:
                        os.remove(file_path)
                        cleaned_count += 1
    except Exception as e:
        print(f"Error cleaning up backups: {e}")
    
    return cleaned_count
