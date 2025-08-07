#!/usr/bin/env python3
"""
Startup script for the Vehicle Price Estimator application.
This script starts both the FastAPI server and Streamlit app for Databricks Apps.
"""

import subprocess
import sys
import time
import os
import signal
import threading
import uvicorn
from multiprocessing import Process
import asyncio

def start_fastapi_server():
    """Start the FastAPI server in a separate process"""
    print("Starting FastAPI server...")
    try:
        # Import and run FastAPI directly to avoid subprocess issues
        sys.path.append('src')
        from app import app
        
        # Run FastAPI server on port 8000
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
    except Exception as e:
        print(f"❌ Error starting FastAPI server: {e}")

def start_streamlit_app():
    """Start the Streamlit app in the main process"""
    print("Starting Streamlit app...")
    try:
        # Use subprocess but with proper configuration for Databricks
        env = os.environ.copy()
        env['STREAMLIT_SERVER_PORT'] = '8080'
        env['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'
        env['STREAMLIT_SERVER_HEADLESS'] = 'true'
        env['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
        
        # Start Streamlit with proper configuration
        cmd = [
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.port=8080",
            "--server.address=0.0.0.0",
            "--server.headless=true",
            "--browser.gatherUsageStats=false"
        ]
        
        subprocess.run(cmd, env=env)
    except Exception as e:
        print(f"❌ Error starting Streamlit app: {e}")

def main():
    print("🚗 Vehicle Price Estimator - Startup Script")
    print("=" * 50)
    
    # Check if required files exist
    required_files = ["src/app.py", "streamlit_app.py", "data.csv"]
    required_dirs = ["pkl_files"]
    
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ Required file not found: {file}")
            return
    
    for dir in required_dirs:
        if not os.path.exists(dir):
            print(f"❌ Required directory not found: {dir}")
            return
    
    print("✅ All required files found")
    
    try:
        # Start FastAPI server in a separate process
        print("🔄 Starting FastAPI server in background...")
        fastapi_process = Process(target=start_fastapi_server)
        fastapi_process.daemon = True
        fastapi_process.start()
        
        # Give FastAPI time to start
        time.sleep(3)
        print("✅ FastAPI server started on port 8000")
        
        # Start Streamlit in the main process (this will be the main service for Databricks Apps)
        print("🔄 Starting Streamlit app on main process...")
        start_streamlit_app()
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
        if 'fastapi_process' in locals():
            fastapi_process.terminate()
            fastapi_process.join()
        print("✅ Services stopped")
    except Exception as e:
        print(f"❌ Error in main: {e}")
        if 'fastapi_process' in locals():
            fastapi_process.terminate()

if __name__ == "__main__":
    main() 