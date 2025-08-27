"""
Enhanced Bulk ETL Report Upload Handler with S3 support
Supports intelligent file detection, automatic organization by property/date, and bulk uploads
"""

import streamlit as st
import os
import shutil
import sys
from datetime import datetime, date
from typing import List, Dict, Any, Optional
import pandas as pd

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.s3_service import get_storage_service
from config.upload_config import get_upload_properties, validate_filename

class EnhancedUploadHandler:
    """Enhanced upload handler with intelligent file detection and bulk processing"""
    
    def __init__(self):
        self.storage_service = get_storage_service()
    
    def render_upload_interface(self):
        """Render the complete bulk upload interface in sidebar"""
        
        st.sidebar.header("📤 Bulk Upload")
        
        # Property selection (required)
        selected_property = st.sidebar.selectbox(
            "Select Property",
            options=get_upload_properties(),
            index=None,
            placeholder="Choose a property...",
            help="Select the property for these reports"
        )
        
        # Date selection
        selected_date = st.sidebar.date_input(
            "Report Date",
            value=datetime.now().date(),
            help="Select the date/week this data represents"
        )
        
        # File upload (only show if property is selected)
        uploaded_files = None
        if selected_property:
            uploaded_files = st.sidebar.file_uploader(
                "Upload Reports",
                type=['xlsx'],
                accept_multiple_files=True,
                help="Select multiple Excel files to upload"
            )
        else:
            st.sidebar.info("👆 Please select a property first")
        
        if uploaded_files and selected_property:
            # Validate all files first (before any upload)
            validation_results = self.validate_uploaded_files(uploaded_files)
            
            valid_count = len(validation_results['valid_files'])
            invalid_count = len(validation_results['invalid_files'])
            
            # Show validation results
            if valid_count > 0:
                st.sidebar.success(f"✅ {valid_count} valid files")
                
                with st.sidebar.expander(f"📁 Valid Files ({valid_count})", expanded=True):
                    for file_info in validation_results['valid_files']:
                        st.write(f"📄 **{file_info['filename']}**")
                        st.write(f"Type: {file_info['report_type']}")
            
            if invalid_count > 0:
                st.sidebar.error(f"❌ {invalid_count} invalid files")
                
                with st.sidebar.expander("❌ Invalid Files", expanded=True):
                    for file_info in validation_results['invalid_files']:
                        st.write(f"**{file_info['filename']}**")
                        st.write(file_info['error_message'])
                        st.markdown("---")
            
            # Upload controls (only show if ALL files are valid)
            if valid_count > 0 and invalid_count == 0:
                st.sidebar.markdown("---")
                
                backup_existing = st.sidebar.checkbox(
                    "🔄 Backup existing files",
                    value=True,
                    help="Create backups before replacing existing files"
                )
                
                # Upload button
                if st.sidebar.button("🚀 Upload Files", type="primary", use_container_width=True):
                    self.process_simplified_upload(
                        uploaded_files=uploaded_files,
                        selected_property=selected_property,
                        selected_date=selected_date,
                        backup_existing=backup_existing
                    )
            elif invalid_count > 0:
                st.sidebar.warning("⚠️ Fix invalid files before uploading")
    
    def validate_uploaded_files(self, uploaded_files: List) -> Dict[str, Any]:
        """Validate uploaded files using simple pattern matching"""
        results = {
            'valid_files': [],
            'invalid_files': []
        }
        
        for uploaded_file in uploaded_files:
            filename = uploaded_file.name
            is_valid, report_type, error_message = validate_filename(filename)
            
            if is_valid:
                results['valid_files'].append({
                    'filename': filename,
                    'report_type': report_type
                })
            else:
                results['invalid_files'].append({
                    'filename': filename,
                    'error_message': error_message
                })
        
        return results
    
    def process_simplified_upload(self, uploaded_files: List, selected_property: str,
                                 selected_date: date, backup_existing: bool = True) -> Dict[str, Any]:
        """
        Process simplified upload with user-selected property
        
        Args:
            uploaded_files: List of uploaded file objects from Streamlit
            selected_property: User-selected property name
            selected_date: Selected date for the reports
            backup_existing: Whether to backup existing files
        
        Returns:
            Dictionary with upload results
        """
        week_string = selected_date.strftime("%m_%d_%Y")
        
        upload_results = {
            'success': [],
            'errors': [],
            'backups': [],
            'total_files': len(uploaded_files)
        }
        
        # Process each file with the selected property
        with st.sidebar:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, uploaded_file in enumerate(uploaded_files):
                try:
                    # Update progress
                    progress = (i + 1) / len(uploaded_files)
                    progress_bar.progress(progress)
                    status_text.text(f"Processing {uploaded_file.name}...")
                    
                    # Create S3 key: data/week/property/filename
                    s3_key = f"{week_string}/{selected_property}/{uploaded_file.name}"
                    
                    # Handle existing files - create backup if needed
                    if backup_existing and self.storage_service.file_exists(s3_key):
                        backup_success = self.storage_service.backup_file(s3_key)
                        if backup_success:
                            upload_results['backups'].append(f"Backed up: {uploaded_file.name}")
                    
                    # Get file data and convert memoryview to bytes for S3
                    file_buffer = uploaded_file.getbuffer()
                    file_data = bytes(file_buffer)  # Convert memoryview to bytes
                    file_size = len(file_data)
                    
                    # Write the file using storage service
                    success = self.storage_service.write_file(s3_key, file_data)
                    
                    if success:
                        upload_results['success'].append({
                            'filename': uploaded_file.name,
                            'property': selected_property,
                            'size': file_size
                        })
                    else:
                        upload_results['errors'].append(f"Failed to write {uploaded_file.name}")
                
                except Exception as e:
                    upload_results['errors'].append(f"{uploaded_file.name}: {str(e)}")
            
            # Complete progress
            progress_bar.progress(1.0)
            status_text.text("Upload complete!")
        
        # Display results
        self._display_upload_results(upload_results)
        
        # Auto-refresh if successful
        if upload_results['success'] and not upload_results['errors']:
            st.sidebar.success("🔄 Dashboard will refresh automatically...")
            # Clear all caches to force data reload
            st.cache_data.clear()
            # Store upload notification in session state for main app
            if 'upload_complete' not in st.session_state:
                st.session_state.upload_complete = True
            st.session_state.last_upload_properties = [selected_property]
            st.rerun()
        
        return upload_results
    
    def _display_upload_results(self, results: Dict[str, Any]):
        """Display upload results in sidebar"""
        
        if results['success']:
            st.sidebar.success(f"✅ Successfully uploaded {len(results['success'])} files")
            
            # Group by property for display
            by_property = {}
            for file_info in results['success']:
                prop = file_info['property']
                if prop not in by_property:
                    by_property[prop] = []
                by_property[prop].append(file_info)
            
            with st.sidebar.expander(f"📋 Uploaded Files ({len(results['success'])})"):
                for prop, files in by_property.items():
                    st.write(f"**🏢 {prop}** ({len(files)} files)")
                    for file_info in files:
                        # Just show filename and size - report type not needed
                        size_kb = file_info['size'] / 1024
                        st.write(f"  • `{file_info['filename']}` ({size_kb:.1f} KB)")
        
        if results['backups']:
            st.sidebar.info(f"🔄 Created {len(results['backups'])} backups")
        
        if results['errors']:
            st.sidebar.error(f"❌ {len(results['errors'])} files failed")
            with st.sidebar.expander("❌ Error Details"):
                for error in results['errors']:
                    st.write(f"• {error}")


# Main interface function
def render_upload_interface():
    """
    Main function to render the enhanced upload interface
    This is the primary entry point for the upload system
    """
    handler = EnhancedUploadHandler()
    handler.render_upload_interface()

def get_upload_history(property_name: str = None, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get recent upload history using storage service
    """
    history = []
    storage_service = get_storage_service()
    
    try:
        # Get all available weeks
        weeks = storage_service.list_weeks()
        
        for week_folder in weeks:
            try:
                # Parse week date
                week_date = datetime.strptime(week_folder, "%m_%d_%Y")
                
                # Get properties for this week
                properties = storage_service.list_properties(week_folder)
                
                for prop_folder in properties:
                    # Get files for this property/week
                    files = storage_service.list_files(week_folder, prop_folder)
                    
                    if files:
                        # For S3, we can't easily get modification times, so use current time
                        # In a real implementation, you might store metadata or use S3 object timestamps
                        latest_time = datetime.now()  # Simplified - could be enhanced with S3 object metadata
                        
                        history.append({
                            'property_name': prop_folder,
                            'week': week_folder,
                            'week_date': week_date,
                            'file_count': len(files),
                            'last_upload': latest_time,
                            'files': files
                        })
            except ValueError:
                continue  # Skip invalid week folders
        
        # Sort by week date (newest first) since we can't get accurate upload times
        history.sort(key=lambda x: x['week_date'], reverse=True)
        
        # Filter by property if specified
        if property_name:
            history = [h for h in history if property_name.lower() in h['property_name'].lower()]
        
        # Limit results
        return history[:limit]
        
    except Exception as e:
        print(f"Error getting upload history: {e}")
        return []

def cleanup_old_backups(days_old: int = 30) -> int:
    """
    Clean up old backup files - S3 versioning handles this automatically
    """
    # S3 versioning and lifecycle policies handle backup cleanup
    # This function is kept for compatibility but does nothing in S3 mode
    return 0

# Usage example and backward compatibility
if __name__ == "__main__":
    render_upload_interface()