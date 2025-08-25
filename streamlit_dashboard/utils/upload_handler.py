"""
Enhanced Bulk ETL Report Upload Handler
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
from parsers.file_parser import analyze_filename, analyze_bulk_upload, FileAnalysisResult

class EnhancedUploadHandler:
    """Enhanced upload handler with intelligent file detection and bulk processing"""
    
    def __init__(self):
        self.base_data_path = os.environ.get("DATA_PATH", "/Users/shivaanikomanduri/ArcanClean/data")
    
    def render_upload_interface(self):
        """Render the complete bulk upload interface in sidebar"""
        
        st.sidebar.header("Bulk Upload")
        # Date selection
        selected_date = st.sidebar.date_input(
            "Report Date",
            value=datetime.now().date(),
            help="Select the date/week this data represents"
        )
        
        
        # File upload
        uploaded_files = st.sidebar.file_uploader(
            "Upload Reports",
            type=['xlsx'],
            accept_multiple_files=True,
            help="Select multiple Excel files to upload"
        )
        
        if uploaded_files:
            # Analyze files
            analysis_results = self.analyze_uploaded_files(uploaded_files)
            
            # Show quick summary
            valid_count = len(analysis_results['valid_files'])
            invalid_count = len(analysis_results['invalid_files'])
            property_count = len(analysis_results['by_property'])
            
            if valid_count > 0:
                st.sidebar.success(f"✅ {valid_count} valid files detected")
                st.sidebar.info(f"🏢 {property_count} properties found")
                
                # Show properties found
                properties = [f"{data['property_name']} ({len(data['files'])} files)" 
                             for data in analysis_results['by_property'].values()]
                st.sidebar.write("**Properties:**")
                for prop in properties:
                    st.sidebar.write(f"• {prop}")
            
            if invalid_count > 0:
                st.sidebar.error(f"❌ {invalid_count} files have naming issues")
                
                # Show invalid files
                with st.sidebar.expander("❌ Invalid Files"):
                    for invalid_file in analysis_results['invalid_files']:
                        st.write(f"**{invalid_file.filename}**")
                        st.write(f"Error: {invalid_file.error_message}")
            
            # Upload controls
            if valid_count > 0:
                st.sidebar.markdown("---")
                
                backup_existing = st.sidebar.checkbox(
                    "🔄 Backup existing files",
                    value=True,
                    help="Create backups before replacing existing files"
                )
                
                # Upload button
                if st.sidebar.button("🚀 Upload Files", type="primary", use_container_width=True):
                    self.process_bulk_upload(
                        uploaded_files=uploaded_files,
                        analysis_results=analysis_results,
                        selected_date=selected_date,
                        backup_existing=backup_existing
                    )
    
    def analyze_uploaded_files(self, uploaded_files: List) -> Dict[str, Any]:
        """Analyze uploaded files and return categorized results"""
        filenames = [file.name for file in uploaded_files]
        return analyze_bulk_upload(filenames)
    
    def process_bulk_upload(self, uploaded_files: List, analysis_results: Dict[str, Any], 
                           selected_date: date, backup_existing: bool = True) -> Dict[str, Any]:
        """
        Process bulk upload with intelligent file organization
        
        Args:
            uploaded_files: List of uploaded file objects from Streamlit
            analysis_results: Results from filename analysis
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
            'total_files': len(analysis_results['valid_files'])
        }
        
        # Create file mapping for quick lookup
        file_map = {file.name: file for file in uploaded_files}
        
        # Process each valid file
        with st.sidebar:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, file_result in enumerate(analysis_results['valid_files']):
                try:
                    # Update progress
                    progress = (i + 1) / len(analysis_results['valid_files'])
                    progress_bar.progress(progress)
                    status_text.text(f"Processing {file_result.filename}...")
                    
                    # Create directory structure based on detected property
                    property_path = os.path.join(
                        self.base_data_path,
                        week_string,
                        file_result.property_name
                    )
                    os.makedirs(property_path, exist_ok=True)
                    
                    # File path
                    file_path = os.path.join(property_path, file_result.filename)
                    
                    # Handle existing files
                    if os.path.exists(file_path) and backup_existing:
                        backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        shutil.move(file_path, backup_path)
                        upload_results['backups'].append(f"Backed up: {file_result.filename}")
                    
                    # Get the uploaded file object
                    uploaded_file = file_map.get(file_result.filename)
                    if uploaded_file:
                        # Write the file
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        # Get file size for confirmation
                        file_size = os.path.getsize(file_path)
                        upload_results['success'].append({
                            'filename': file_result.filename,
                            'property': file_result.property_name,
                            'report_type': file_result.report_type,
                            'size': file_size
                        })
                    else:
                        upload_results['errors'].append(f"Could not find file object: {file_result.filename}")
                
                except Exception as e:
                    upload_results['errors'].append(f"{file_result.filename}: {str(e)}")
            
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
            st.session_state.last_upload_properties = list(set([
                file_info['property'] for file_info in upload_results['success']
            ]))
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
                        # Simple description mapping
                        report_descriptions = {
                            'resanalytics_box': 'ResAnalytics Box Score Summary',
                            'work_order': 'Work Order Report',
                            'resanalytics_unit': 'ResAnalytics Unit Availability Details',
                            'resanalytics_market': 'ResAnalytics Market Rent Schedule',
                            'resanalytic_lease': 'ResAnalytic Lease Expiration',
                            'resaranalytics_delinquency': 'ResARAnalytics Delinquency Summary',
                            'pending_make': 'Pending Make Ready Unit Details',
                            'residents_on_notice': 'Residents on Notice Report',
                            'budget_comparison': 'Budget Comparison Report',
                            'comprehensive_weekly': 'Comprehensive Weekly Report'
                        }
                        report_desc = report_descriptions.get(
                            file_info['report_type'], file_info['report_type']
                        )
                        size_kb = file_info['size'] / 1024
                        st.write(f"  • {report_desc}: `{file_info['filename']}` ({size_kb:.1f} KB)")
        
        if results['backups']:
            st.sidebar.info(f"🔄 Created {len(results['backups'])} backups")
        
        if results['errors']:
            st.sidebar.error(f"❌ {len(results['errors'])} files failed")
            with st.sidebar.expander("❌ Error Details"):
                for error in results['errors']:
                    st.write(f"• {error}")

# Legacy function support (for backward compatibility)
def process_etl_uploads(uploaded_files: List, property_name: str, week: str) -> Dict[str, Any]:
    """
    Legacy function for backward compatibility
    Now redirects to enhanced bulk upload system
    """
    st.warning("⚠️ This upload method is deprecated. Please use the new bulk upload interface in the sidebar.")
    
    # Convert to new format
    try:
        selected_date = datetime.strptime(week, "%m_%d_%Y").date()
    except ValueError:
        selected_date = datetime.now().date()
    
    handler = EnhancedUploadHandler()
    
    # Analyze files
    analysis_results = handler.analyze_uploaded_files(uploaded_files)
    
    # Process upload
    return handler.process_bulk_upload(
        uploaded_files=uploaded_files,
        analysis_results=analysis_results,
        selected_date=selected_date,
        backup_existing=True
    )

def validate_etl_file(uploaded_file) -> Dict[str, Any]:
    """
    Enhanced validation using filename analyzer
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
    
    # Use filename analysis for pattern validation
    analysis = analyze_filename(uploaded_file.name)
    
    if not analysis.is_valid:
        result['valid'] = False
        result['error'] = analysis.error_message
        if analysis.suggested_fixes:
            result['suggestions'] = analysis.suggested_fixes
    
    return result

def get_upload_history(property_name: str = None, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Get recent upload history from data directory
    """
    history = []
    base_path = os.environ.get("DATA_PATH", "/Users/shivaanikomanduri/ArcanClean/data")
    
    try:
        # Scan data directory for recent uploads
        for week_folder in os.listdir(base_path):
            week_path = os.path.join(base_path, week_folder)
            if os.path.isdir(week_path) and '_' in week_folder:
                try:
                    # Parse week date
                    week_date = datetime.strptime(week_folder, "%m_%d_%Y")
                    
                    # Scan properties in this week
                    for prop_folder in os.listdir(week_path):
                        prop_path = os.path.join(week_path, prop_folder)
                        if os.path.isdir(prop_path):
                            
                            # Count files
                            files = [f for f in os.listdir(prop_path) 
                                   if f.endswith('.xlsx') and not f.startswith('~$')]
                            
                            if files:
                                # Get most recent file modification time
                                file_times = []
                                for file in files:
                                    file_path = os.path.join(prop_path, file)
                                    file_times.append(os.path.getmtime(file_path))
                                
                                if file_times:
                                    latest_time = datetime.fromtimestamp(max(file_times))
                                    
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
        
        # Sort by last upload time (newest first)
        history.sort(key=lambda x: x['last_upload'], reverse=True)
        
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
    Clean up old backup files
    """
    base_path = os.environ.get("DATA_PATH", "/Users/shivaanikomanduri/ArcanClean/data")
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

def render_upload_interface():
    """
    Main function to render the enhanced upload interface
    This is the primary entry point for the upload system
    """
    handler = EnhancedUploadHandler()
    handler.render_upload_interface()

# Usage example and backward compatibility
if __name__ == "__main__":
    render_upload_interface()