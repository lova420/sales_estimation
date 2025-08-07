#!/usr/bin/env python3
"""
Main entry point for Databricks Apps deployment.
This script launches Streamlit for the Vehicle Price Estimator.

FastAPI code is commented out below for future reference.
"""

import os
import sys
import subprocess

# FastAPI imports (commented out for now)
# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# import pandas as pd
# import numpy as np
# import uvicorn
# import glob
# from model_inference import predict_price

# app = FastAPI(title="VIN Price Estimator")

# FastAPI models (commented out for now)
# class VINRequest(BaseModel):
#     df: list[dict]
# 
# class DataRequest(BaseModel):
#     features: dict

def main():
    """Main entry point for Databricks Apps"""
    
    # Get configuration from environment
    port = int(os.environ.get('PORT', '8080'))
    host = os.environ.get('HOST', '0.0.0.0')
    
    print(f"🚗 Vehicle Price Estimator - Starting Streamlit")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Working Directory: {os.getcwd()}")
    
    # Check if streamlit_main.py exists (should be in parent directory since we're in src/)
    streamlit_file = os.path.join('..', 'streamlit_main.py')
    if not os.path.exists(streamlit_file):
        # Fallback: try current directory
        streamlit_file = 'streamlit_main.py'
        if not os.path.exists(streamlit_file):
            # Try absolute path from working directory
            streamlit_file = os.path.join(os.getcwd(), 'streamlit_main.py')
            if not os.path.exists(streamlit_file):
                print("❌ streamlit_main.py not found!")
                print(f"   Searched in: {os.path.join('..', 'streamlit_main.py')}")
                print(f"   Searched in: streamlit_main.py")
                print(f"   Searched in: {streamlit_file}")
                sys.exit(1)
    
    # Launch Streamlit with proper configuration
    cmd = [
        sys.executable, "-m", "streamlit", "run", streamlit_file,
        f"--server.port={port}",
        f"--server.address={host}",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
        "--server.enableCORS=false",
        "--server.enableXsrfProtection=false"
    ]
    
    print(f"🚀 Launching: {' '.join(cmd)}")
    
    # Replace the current process with Streamlit
    os.execv(sys.executable, cmd)

# FastAPI functions (commented out for now)
"""
def get_vin_data(vin: str):
    vin_search = vin[:8]

    try:
        # Support both local and Databricks file paths
        data_path = os.path.join(os.getcwd(), 'data.csv')
        if not os.path.exists(data_path):
            # Try alternative path for Databricks
            data_path = '/Workspace/Repos/*/data.csv'
            matching_files = glob.glob(data_path)
            if matching_files:
                data_path = matching_files[0]
            else:
                data_path = 'data.csv'
        
        data = pd.read_csv(data_path)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="data.csv not found")

    str_cols = data.select_dtypes(include=['object', 'string']).columns
    data[str_cols] = data[str_cols].apply(lambda x: x.str.strip())

    data_cleaned = data[data['VIN'].str.strip().str[:8] == vin_search].copy()

    if data_cleaned.empty:
        return pd.DataFrame()

    cols = [
        "VIN", "Lot Year", "Lot Make", "Lot Model", "Sale Price",
        "Lot Run Condition", "Sale Title Type", "Damage Type Description",
        "Odometer Reading", "Lot Fuel Type"
    ]
    return data_cleaned[cols].reset_index(drop=True)

def estimate_price_by_vin(df_similar: list[dict]):
    df_similar = pd.DataFrame(df_similar)
    if df_similar.empty:
        return None

    Q1 = df_similar['Sale Price'].quantile(0.25)
    Q3 = df_similar['Sale Price'].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR

    df_cleaned = df_similar[(df_similar['Sale Price'] >= lower) & (df_similar['Sale Price'] <= upper)]

    if df_cleaned.empty:
        return float(df_similar['Sale Price'].median())

    return float(df_cleaned['Sale Price'].median())

@app.get("/get-data/{vin}")
def get_data(vin: str):
    df = get_vin_data(vin)
    if df.empty:
        raise HTTPException(status_code=404, detail="No similar VINs found")
    return df.to_dict(orient="records")

@app.post("/estimate_price/")
def estimate_price(request: VINRequest):
    estimated_price = estimate_price_by_vin(request.df)
    return {
        "matches_found": len(request.df),
        "estimated_price": estimated_price
    }

@app.post("/predict_price/")
def predict_price_from_features(request: DataRequest):
    result = predict_price(request.features)
    return result
"""

if __name__ == "__main__":
    main()