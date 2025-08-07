#!/usr/bin/env python3
"""
Minimal entry point for Databricks Apps.
This script launches Streamlit without any imports that could cause ScriptRunContext issues.
"""

import os
import sys
import subprocess

def main():
    """Launch Streamlit with proper configuration"""
    
    # Get environment configuration
    port = int(os.environ.get('PORT', '8080'))
    host = os.environ.get('HOST', '0.0.0.0')
    
    print("🚗 Vehicle Price Estimator - Launching Streamlit")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Working Directory: {os.getcwd()}")
    
    # Verify streamlit_main.py exists
    if not os.path.exists('streamlit_main.py'):
        print("❌ streamlit_main.py not found!")
        print(f"   Current directory contents: {os.listdir('.')}")
        sys.exit(1)
    
    print("✅ streamlit_main.py found")
    
    # Build Streamlit command
    cmd = [
        sys.executable, "-m", "streamlit", "run", "streamlit_main.py",
        f"--server.port={port}",
        f"--server.address={host}",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
        "--server.enableCORS=false",
        "--server.enableXsrfProtection=false",
        "--server.enableWebsocketCompression=false"
    ]
    
    print(f"🚀 Executing: {' '.join(cmd)}")
    
    # Start Streamlit subprocess and wait for it
    try:
        result = subprocess.run(cmd, check=True)
        print(f"✅ Streamlit exited with code: {result.returncode}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Streamlit failed with code: {e.returncode}")
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("🛑 Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()