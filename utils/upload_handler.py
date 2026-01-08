"""Weekly Report Upload Handler with S3 support"""

import streamlit as st
import os
import sys
from datetime import datetime, date
from typing import List, Dict, Any
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from utils.s3_service import get_storage_service
from config.upload_config import get_upload_properties, validate_filename
from utils.historical_data_service import HistoricalDataService

logger = logging.getLogger(__name__)

class EnhancedUploadHandler:
    """Upload handler for single property/week uploads"""

    def __init__(self):
        self.storage_service = get_storage_service()
        self.historical_service = HistoricalDataService(self.storage_service)

    def render_upload_interface(self):
        """Render upload interface in sidebar"""
        st.sidebar.header("Upload Reports")
        selected_property = st.sidebar.selectbox(
            "Property",
            options=get_upload_properties(),
            index=None,
            placeholder="Choose property...",
            help="One property at a time"
        )

        selected_date = st.sidebar.date_input(
            "Week Date",
            value=datetime.now().date(),
            help="Week ending date"
        )

        uploaded_files = None
        if selected_property:
            uploaded_files = st.sidebar.file_uploader(
                "Excel Files",
                type=['xlsx'],
                accept_multiple_files=True,
                help="Upload all reports for this week"
            )
        else:
            st.sidebar.info("Select property first")
        
        if uploaded_files and selected_property:
            validation_results = self.validate_uploaded_files(uploaded_files)

            valid_count = len(validation_results['valid_files'])
            invalid_count = len(validation_results['invalid_files'])

            if valid_count > 0:
                st.sidebar.success(f"✓ {valid_count} valid file(s)")

            if invalid_count > 0:
                st.sidebar.error(f"✗ {invalid_count} invalid file(s)")
                for file_info in validation_results['invalid_files']:
                    st.sidebar.caption(f"• {file_info['filename']}")

            if valid_count > 0 and invalid_count == 0:
                backup_existing = st.sidebar.checkbox(
                    "Backup existing",
                    value=True,
                    help="Backup before replacing"
                )

                if st.sidebar.button("Upload", type="primary", use_container_width=True):
                    self.process_upload(
                        uploaded_files=uploaded_files,
                        selected_property=selected_property,
                        selected_date=selected_date,
                        backup_existing=backup_existing
                    )
            elif invalid_count > 0:
                st.sidebar.warning("Fix invalid files")
    
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
    
    def process_upload(self, uploaded_files: List, selected_property: str,
                       selected_date: date, backup_existing: bool = True) -> Dict[str, Any]:
        """
        Process upload for single property and week

        Args:
            uploaded_files: Uploaded file objects
            selected_property: Property name
            selected_date: Week date
            backup_existing: Backup before replacing

        Returns:
            Upload results dict
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

        # Update historical data if upload was successful
        if upload_results['success'] and not upload_results['errors']:
            try:
                status_text.text("Updating historical data...")
                self._update_historical_data(
                    property_name=selected_property,
                    week_string=week_string,
                    report_date=datetime.combine(selected_date, datetime.min.time())
                )
                logger.info(f"Historical data updated for {selected_property}")
            except Exception as e:
                logger.error(f"Error updating historical data: {e}")
                # Don't fail the upload if historical update fails
                st.sidebar.warning("Upload successful, but historical data update failed")

        # Auto-refresh if successful
        if upload_results['success'] and not upload_results['errors']:
            st.sidebar.success("Dashboard will refresh automatically...")
            # Clear all caches to force data reload
            st.cache_data.clear()
            # Store upload notification in session state for main app
            if 'upload_complete' not in st.session_state:
                st.session_state.upload_complete = True
            st.session_state.last_upload_properties = [selected_property]
            st.rerun()

        return upload_results
    
    def _update_historical_data(self, property_name: str, week_string: str, report_date: datetime):
        """
        Update centralized historical data after successful upload

        Args:
            property_name: Name of the property
            week_string: Week folder (e.g., "01_15_2025")
            report_date: Date of the reports
        """
        from data.loader import load_property_data

        try:
            # Load and parse the uploaded files
            logger.info(f"Loading data for {property_name} from week {week_string}")
            parsed_data = load_property_data(week_string, property_name)

            if parsed_data:
                # Update historical data
                success = self.historical_service.update_with_new_week_data(
                    property_name=property_name,
                    parsed_data=parsed_data,
                    report_date=report_date
                )

                if success:
                    logger.info(f"Successfully updated historical data for {property_name}")
                else:
                    logger.warning(f"Failed to update historical data for {property_name}")

        except Exception as e:
            logger.error(f"Error updating historical data for {property_name}: {e}")
            raise

    def _display_upload_results(self, results: Dict[str, Any]):
        """Display upload results"""
        if results['success']:
            st.sidebar.success(f"Uploaded {len(results['success'])} file(s)")

        if results['backups']:
            st.sidebar.info(f"{len(results['backups'])} backup(s) created")

        if results['errors']:
            st.sidebar.error(f"{len(results['errors'])} failed")
            for error in results['errors']:
                st.sidebar.caption(f"• {error}")


def render_upload_interface():
    """Render upload interface"""
    handler = EnhancedUploadHandler()
    handler.render_upload_interface()