# Azure Databricks Apps Deployment Guide

This guide will help you deploy the Vehicle Price Estimator application to Azure Databricks Apps.

## Prerequisites

1. **Azure Databricks Workspace** with Apps feature enabled
2. **Databricks CLI** installed and configured
3. **Git repository** connected to your Databricks workspace

## Deployment Steps

### 1. Prepare Your Repository

Make sure your repository contains all the required files:
- `streamlit_app.py` - Main Streamlit application
- `src/app.py` - FastAPI backend
- `src/model_inference.py` - ML model inference
- `requirements.txt` - Python dependencies
- `data.csv` - Training data
- `pkl_files/` - Model artifacts
  - `lgbm_model_v1.pkl`
  - `preprocessor_v1.pkl`

### 2. Connect Repository to Databricks

1. Go to your Databricks workspace
2. Navigate to **Repos** → **Add Repo**
3. Clone your repository containing the sales estimation app

### 3. Deploy as Databricks App

#### Option A: Deploy Streamlit App (Recommended)

1. In your Databricks workspace, navigate to **Apps**
2. Click **Create App**
3. Fill in the app details:
   - **Name**: `vehicle-price-estimator`
   - **Description**: `Vehicle Price Estimation Application`
   - **Source Code**: Select your repository
   - **Python file**: `streamlit_app.py`
   - **Cluster**: Choose or create a cluster with Python 3.9+

4. Set environment variables (if needed):
   - `API_BASE_URL`: URL of your FastAPI backend (if deployed separately)

5. Click **Create** and wait for deployment

#### Option B: Deploy FastAPI Backend Separately

If you want to deploy the FastAPI backend as a separate service:

1. Create another app for the FastAPI backend:
   - **Name**: `vehicle-price-api`
   - **Python file**: `src/app.py`
   - **Environment variables**:
     - `PORT`: `8000`
     - `HOST`: `0.0.0.0`

2. Update the Streamlit app's `API_BASE_URL` to point to the FastAPI service

### 4. Configure File Paths

The modified code supports multiple file path configurations:

1. **Local development**: Files in current directory
2. **Databricks Repos**: Files in `/Workspace/Repos/*/` path
3. **Fallback**: Original relative paths

### 5. Access Your Application

Once deployed:
1. Navigate to **Apps** in your Databricks workspace
2. Find your `vehicle-price-estimator` app
3. Click on the app name to access the URL
4. Your Streamlit app should load with both VIN-based and manual prediction features

## Application Features

### VIN-Based Prediction
- Enter a VIN number to find similar vehicles
- Get price estimates based on historical data
- View similar vehicles and price distribution

### Manual Input Prediction
- Input vehicle details manually
- Get ML-powered price predictions
- View confidence levels and prediction variability

## Troubleshooting

### Common Issues

1. **File Not Found Errors**
   - Ensure all required files are in your repository
   - Check that `data.csv` and `pkl_files/` are included

2. **Model Loading Issues**
   - Verify model files are not corrupted
   - Check file permissions in Databricks
   - Application will fallback to simple statistical prediction if ML models fail

3. **Import Errors**
   - Verify all packages in `requirements.txt` are available
   - Some packages may need specific versions for Databricks

4. **Memory Issues**
   - Ensure your cluster has sufficient memory for the data and models
   - Consider using a larger cluster configuration

### Debugging

To debug issues:
1. Check the app logs in Databricks Apps console
2. Use `print()` statements in your code for debugging
3. Test individual components in Databricks notebooks first

## Best Practices

1. **Version Control**: Keep your repository organized with proper version control
2. **Environment Variables**: Use environment variables for configuration
3. **Error Handling**: The app includes robust error handling and fallbacks
4. **Resource Management**: Monitor cluster usage and scale as needed
5. **Security**: Follow Databricks security best practices for data access

## Support

For additional support:
- Check Databricks documentation for Apps
- Review Streamlit and FastAPI documentation
- Monitor application logs for specific error messages

## File Structure

```
sales_estimation/
├── streamlit_app.py          # Main Streamlit app (modified for Databricks)
├── src/
│   ├── app.py               # FastAPI backend (modified for Databricks)
│   └── model_inference.py   # ML inference (modified for Databricks)
├── requirements.txt         # Updated dependencies
├── data.csv                # Training data
├── pkl_files/
│   ├── lgbm_model_v1.pkl   # Trained model
│   └── preprocessor_v1.pkl # Data preprocessor
└── DATABRICKS_DEPLOYMENT.md # This file
```