"""
Entry point for Elastic Beanstalk Python platform
EB will run this file to start the Streamlit application
"""

import os
import sys
import subprocess

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

def main():
    """Start the Streamlit application"""
    # Run Streamlit on the port EB expects
    cmd = [
        "streamlit", "run", 
        "streamlit_dashboard/app.py",
        "--server.port=8080",  # EB expects port 8080 for Python apps
        "--server.address=0.0.0.0",
        "--server.headless=true",
        "--server.enableCORS=false",
        "--server.enableXsrfProtection=false"
    ]
    
    subprocess.run(cmd)

if __name__ == "__main__":
    main()