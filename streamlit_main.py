#!/usr/bin/env python3
"""
Main Streamlit app for Databricks Apps deployment.
This version runs only Streamlit with embedded API functionality.
"""

import streamlit as st
import pandas as pd
import os
import sys
import joblib
import glob
import time

# Add src to path for imports
sys.path.append('src')
from model_inference import predict_price
from settings import settings_page, get_all_rules, initialize_rules

# Page configuration
st.set_page_config(
    page_title="Vehicle Price Estimator",
    page_icon="🚗",
    layout="wide"
)

def load_preprocessor():
    """Load the preprocessor to get feature names and categories"""
    try:
        # Support both local and Databricks file paths
        preprocessor_path = os.path.join(os.getcwd(), 'pkl_files', 'preprocessor_v1.pkl')
        if not os.path.exists(preprocessor_path):
            # Try alternative path for Databricks
            preprocessor_path = '/Workspace/Repos/*/pkl_files/preprocessor_v1.pkl'
            matching_files = glob.glob(preprocessor_path)
            if matching_files:
                preprocessor_path = matching_files[0]
            else:
                preprocessor_path = 'pkl_files/preprocessor_v1.pkl'
        
        preprocessor = joblib.load(preprocessor_path)
        return preprocessor
    except Exception as e:
        st.error(f"Error loading preprocessor: {e}")
        return None

def get_unique_values_from_data():
    """Get unique values for categorical features from the data.csv file"""
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
        unique_values = {}
        
        # Get unique values for categorical columns
        categorical_cols = ['Lot Make', 'Lot Model', 'Lot Run Condition', 
                          'Sale Title Type', 'Damage Type Description', 'Lot Fuel Type']
        
        for col in categorical_cols:
            if col in data.columns:
                unique_values[col] = sorted(data[col].dropna().unique().tolist())
        
        return unique_values
    except Exception as e:
        st.error(f"Error loading data for dropdowns: {e}")
        return {}

def get_vin_data(vin: str):
    """Get VIN data directly without API call"""
    try:
        # Support both local and Databricks file paths
        data_path = os.path.join(os.getcwd(), 'data.csv')
        if not os.path.exists(data_path):
            data_path = '/Workspace/Repos/*/data.csv'
            matching_files = glob.glob(data_path)
            if matching_files:
                data_path = matching_files[0]
            else:
                data_path = 'data.csv'
        
        data = pd.read_csv(data_path)
        
        vin_search = vin[:8]
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
    except Exception as e:
        st.error(f"Error loading VIN data: {e}")
        return pd.DataFrame()

def estimate_price_by_vin(df_similar: pd.DataFrame):
    """Estimate price from similar vehicles"""
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

def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Choose a page:",
        ["VIN-Based Prediction", "Manual Input Prediction", "Settings"]
    )

    if page == "VIN-Based Prediction":
        st.title("🚗 Vehicle Price Estimator")
        st.markdown("---")
        vin_based_prediction()
    elif page == "Manual Input Prediction":
        st.title("🚗 Vehicle Price Estimator")
        st.markdown("---")
        manual_input_prediction()
    elif page == "Settings":
        settings_page()

def vin_based_prediction():
    st.header("VIN-Based Price Prediction")
    st.markdown("Enter a VIN number to find similar vehicles and estimate the price.")
    
    # Initialize session state safely
    try:
        if 'similar_vehicles' not in st.session_state:
            st.session_state.similar_vehicles = None
        if 'vin_searched' not in st.session_state:
            st.session_state.vin_searched = None
    except Exception:
        # Fallback for when session state is not available
        pass
    
    # VIN input
    vin = st.text_input("Enter VIN Number:", placeholder="e.g., 1HGBH41JXMN109186")
    
    # Search button
    if st.button("Search Similar Vehicles", type="primary"):
        time.sleep(3)
        if vin:
            with st.spinner("Searching for similar vehicles..."):
                # Get VIN data directly
                similar_df = get_vin_data(vin)
                
                if not similar_df.empty:
                    similar_vehicles = similar_df.to_dict(orient="records")
                    try:
                        st.session_state.similar_vehicles = similar_vehicles
                        st.session_state.vin_searched = vin
                    except Exception:
                        pass  # Fallback for session state issues
                    st.success(f"Found {len(similar_vehicles)} similar vehicles!")
                else:
                    try:
                        st.session_state.similar_vehicles = None
                        st.session_state.vin_searched = None
                    except Exception:
                        pass  # Fallback for session state issues
                    st.warning("No similar vehicles found for this VIN.")
        else:
            st.warning("Please enter a VIN number.")
    
    # Display results if we have similar vehicles
    try:
        similar_vehicles = getattr(st.session_state, 'similar_vehicles', None)
    except Exception:
        similar_vehicles = None
    
    if similar_vehicles:
        st.subheader("Similar Vehicles Found:")
        df_similar = pd.DataFrame(similar_vehicles)
        st.dataframe(df_similar, use_container_width=True)
        
        # Prediction button
        if st.button("Predict Price", type="secondary"):
            with st.spinner("Calculating price prediction..."):
                # Add 3-second delay for demonstration
                time.sleep(3)
                # Calculate prediction directly
                estimated_price = estimate_price_by_vin(df_similar)
                
                if estimated_price:
                    st.subheader("Price Prediction Results:")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        # --- Deduction Rules Application ---
                        initialize_rules()
                        all_rules = get_all_rules()
                        active_rules = all_rules[all_rules['is_active']]

                        total_deduction_rate = 0.0
                        if not active_rules.empty:
                            # Correctly reference the DataFrame of similar vehicles
                            vehicle_year = df_similar['Lot Year'].iloc[0]
                            vehicle_make = df_similar['Lot Make'].iloc[0]
                            vehicle_model = df_similar['Lot Model'].iloc[0]

                            for _, rule in active_rules.iterrows():
                                applied = False
                                if rule['rule_type'] == 'General' and rule['rule_condition'] == 'General':
                                    applied = True
                                elif rule['rule_type'] == 'Year':
                                    if str(int(vehicle_year)) == rule['rule_condition']:
                                        applied = True
                                elif rule['rule_type'] == 'Making Model':
                                    if f"{vehicle_make}|{vehicle_model}" == rule['rule_condition']:
                                        applied = True
                                
                                if applied:
                                    total_deduction_rate += rule['deduction_rate']

                        final_price = estimated_price * (1 - total_deduction_rate / 100)

                        st.write("##### After Deduction Rate:")
                        st.metric(
                            "Final Price",
                            f"${final_price:,.2f}",
                            delta=f"-{total_deduction_rate:.2f}%" if total_deduction_rate > 0 else "No deductions applied",
                            delta_color="inverse" if total_deduction_rate > 0 else "off"
                        )
                        st.write(f"**Actual Estimated Price:** ${estimated_price:,.2f}")
                        st.caption(f"Based on {len(df_similar)} similar vehicles")
                    with col2:
                        st.metric("Matches Used", len(df_similar))
                    
                    # Show price distribution
                    if 'Sale Price' in df_similar.columns:
                        st.subheader("Price Distribution of Similar Vehicles")
                        st.bar_chart(df_similar['Sale Price'])

def manual_input_prediction():
    st.header("Manual Input Price Prediction")
    st.markdown("Enter vehicle details manually to get a price prediction using our ML model.")
    
    # Load preprocessor and unique values
    preprocessor = load_preprocessor()
    unique_values = get_unique_values_from_data()
    
    if not unique_values:
        st.error("Unable to load data for dropdowns. Please check if the files are available.")
        return
    
    # Create form for manual input
    with st.form("manual_prediction_form"):
        st.subheader("Vehicle Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            lot_year = st.number_input("Lot Year", min_value=1900, max_value=2024, value=2020)
            odometer_reading = st.number_input("Odometer Reading", min_value=0, value=50000)
            
            # Categorical inputs with dropdowns
            lot_make = st.selectbox("Lot Make", unique_values.get('Lot Make', []))
            lot_model = st.selectbox("Lot Model", unique_values.get('Lot Model', []))
            lot_run_condition = st.selectbox("Lot Run Condition", unique_values.get('Lot Run Condition', []))
        
        with col2:
            sale_title_type = st.selectbox("Sale Title Type", unique_values.get('Sale Title Type', []))
            damage_type_description = st.selectbox("Damage Type Description", unique_values.get('Damage Type Description', []))
            lot_fuel_type = st.selectbox("Lot Fuel Type", unique_values.get('Lot Fuel Type', []))
        
        submitted = st.form_submit_button("Predict Price", type="primary")
        
        if submitted:
            # Prepare input data
            input_data = {
                'Lot Year': lot_year,
                'Odometer Reading': odometer_reading,
                'Lot Make': lot_make,
                'Lot Model': lot_model,
                'Lot Run Condition': lot_run_condition,
                'Sale Title Type': sale_title_type,
                'Damage Type Description': damage_type_description,
                'Lot Fuel Type': lot_fuel_type
            }
            
            with st.spinner("Making prediction..."):
                # Call the ML model directly
                prediction_result = predict_price(input_data)
                
                if 'error' in prediction_result:
                    st.error(f"Prediction Error: {prediction_result['error']}")
                else:
                    st.success("Prediction completed successfully!")
                    
                    # Display results
                    st.subheader("ML Model Prediction Results:")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        # --- Deduction Rules Application ---
                        initialize_rules()
                        all_rules = get_all_rules()
                        active_rules = all_rules[all_rules['is_active']]

                        total_deduction_rate = 0.0
                        estimated_price = prediction_result['predicted_sale_price']

                        if not active_rules.empty:
                            # Data from manual input form
                            vehicle_year = input_data['Lot Year']
                            vehicle_make = input_data['Lot Make']
                            vehicle_model = input_data['Lot Model']

                            for _, rule in active_rules.iterrows():
                                applied = False
                                if rule['rule_type'] == 'General' and rule['rule_condition'] == 'General':
                                    applied = True
                                elif rule['rule_type'] == 'Year':
                                    if str(int(vehicle_year)) == rule['rule_condition']:
                                        applied = True
                                elif rule['rule_type'] == 'Making Model':
                                    if f"{vehicle_make}|{vehicle_model}" == rule['rule_condition']:
                                        applied = True
                                
                                if applied:
                                    total_deduction_rate += rule['deduction_rate']

                        final_price = estimated_price * (1 - total_deduction_rate / 100)

                        st.write("##### After Deduction Rate:")
                        st.metric(
                            "Final Price",
                            f"${final_price:,.2f}",
                            delta=f"-{total_deduction_rate:.2f}%" if total_deduction_rate > 0 else "No deductions applied",
                            delta_color="inverse" if total_deduction_rate > 0 else "off"
                        )
                        st.write(f"**Actual Estimated Price:** ${estimated_price:,.2f}")
                    with col2:
                        st.metric(
                            "Confidence Level", 
                            prediction_result['confidence_level'],
                            delta=prediction_result['estimated_prediction_variability']
                        )
                    with col3:
                        st.metric(
                            "Prediction Variability",
                            prediction_result['estimated_prediction_variability']
                        )
                    
                    # Show input summary
                    st.subheader("Input Summary")
                    input_df = pd.DataFrame([input_data])
                    st.dataframe(input_df, use_container_width=True)

if __name__ == "__main__":
    main()