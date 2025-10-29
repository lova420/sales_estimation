
import streamlit as st
import pandas as pd
import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import monotonically_increasing_id

# --- Databricks Connection ---
@st.cache_resource
def get_spark_session():
    """Establish and return a Spark session."""
    spark = SparkSession.builder.appName("deduction_rules_app").getOrCreate()
    return spark

TABLE_NAME = "radiusautos.datafiles.deduction_rules"

# --- Database Functions ---
def create_table():
    """Create the deduction_rules table if it doesn't exist."""
    spark = get_spark_session()
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id BIGINT,
            rule_type STRING,
            rule_condition STRING,
            deduction_rate DOUBLE,
            is_active BOOLEAN
        )
        USING DELTA
    """)

def add_rule(rule_type, deduction_rate, condition=None):
    """Add a new deduction rule to the database."""
    spark = get_spark_session()
    # Create a DataFrame for the new rule
    # Generate a unique ID
    max_id_df = spark.sql(f"SELECT MAX(id) as max_id FROM {TABLE_NAME}")
    max_id = max_id_df.collect()[0]["max_id"]
    new_id = (max_id + 1) if max_id is not None else 1

    new_rule_pd = pd.DataFrame([{
        "id": new_id,
        "rule_type": rule_type,
        "rule_condition": condition,
        "deduction_rate": deduction_rate,
        "is_active": True
    }])
    new_rule_df = spark.createDataFrame(new_rule_pd)
    new_rule_df.write.format("delta").mode("append").saveAsTable(TABLE_NAME)

def get_all_rules():
    """Fetch all deduction rules from the database."""
    try:
        spark = get_spark_session()
        df = spark.read.table(TABLE_NAME).orderBy("id").toPandas()
        return df
    except Exception as e:
        st.error(f"Databricks connection error: {e}")
        # In case of DB error, return an empty DataFrame with the correct columns
        return pd.DataFrame(columns=['id', 'rule_type', 'rule_condition', 'deduction_rate', 'is_active'])

def update_rule_status(rule_id, is_active):
    """Update the is_active status of a rule."""
    spark = get_spark_session()
    spark.sql(f"UPDATE {TABLE_NAME} SET is_active = {is_active} WHERE id = {rule_id}")

def delete_rule(rule_id):
    """Delete a rule from the database."""
    spark = get_spark_session()
    spark.sql(f"DELETE FROM {TABLE_NAME} WHERE id = {rule_id}")


# --- UI Components ---
def settings_page():
    """Renders the Deduction Rules settings page."""
    st.header("Deduction Rules")

    # --- Add New Rule Form ---
    st.subheader("Add New Deduction Rule")

    rule_type = st.selectbox("Rule Type", ["General", "Year", "Making Model"])

    deduction_value = None
    condition = None

    if rule_type == "General":
        deduction_value = st.number_input("Deduction (%)", min_value=0.0, max_value=100.0, step=0.1, format="%.1f")
        condition = "General"

    elif rule_type == "Year":
        try:
            data_path = os.path.join(os.getcwd(), 'data.csv')
            df = pd.read_csv(data_path)
            years = sorted(df['Lot Year'].dropna().unique())
            selected_year = st.selectbox("Select Year", years)
            deduction_value = st.number_input("Deduction (%)", min_value=0.0, max_value=100.0, step=0.1, format="%.1f")
            condition = str(selected_year)
        except FileNotFoundError:
            st.error("data.csv not found. Please make sure the file is in the correct directory.")
            return


    elif rule_type == "Making Model":
        try:
            data_path = os.path.join(os.getcwd(), 'data.csv')
            df = pd.read_csv(data_path)
            makes = sorted(df['Lot Make'].dropna().unique())
            selected_make = st.selectbox("Select Make", makes)

            models = sorted(df[df['Lot Make'] == selected_make]['Lot Model'].dropna().unique())
            selected_model = st.selectbox("Select Model", models)

            deduction_value = st.number_input("Deduction (%)", min_value=0.0, max_value=100.0, step=0.1, format="%.1f")
            condition = f"{selected_make}|{selected_model}"
        except FileNotFoundError:
            st.error("data.csv not found. Please make sure the file is in the correct directory.")
            return

    if st.button("Add Deduction Rule"):
        if deduction_value is not None:
            try:
                add_rule(rule_type, deduction_value, condition)
                st.success("Deduction rule added successfully!")
                # Rerun to show the new rule in the list
                st.rerun()
            except Exception as e:
                st.error(f"Error adding rule: {e}")
        else:
            st.warning("Please fill in all the details.")

    # --- Existing Rules ---
    st.subheader("Existing Deduction Rules")

    try:
        rules_df = get_all_rules()
        if not rules_df.empty:
            for index, row in rules_df.iterrows():
                col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                with col1:
                    st.write(f"**Rule Type:** {row['rule_type']}")
                    if row['rule_condition']:
                        st.write(f"**Condition:** {row['rule_condition']}")
                with col2:
                    st.write(f"**Deduction Rate:** {row['deduction_rate']}%")
                with col3:
                    is_active = st.toggle("Active", value=row['is_active'], key=f"active_{row['id']}")
                    if is_active != row['is_active']:
                        update_rule_status(row['id'], is_active)
                        st.rerun()
                with col4:
                    if st.button("Delete", key=f"delete_{row['id']}"):
                        delete_rule(row['id'])
                        st.rerun()
                st.markdown("---")
        else:
            st.info("There are no existing rules.")
    except Exception as e:
        st.error(f"Could not load rules. Have you configured your Databricks connection? Error: {e}")
        if st.button("Attempt to Create Table"):
            try:
                create_table()
                st.success("Table 'deduction_rules' created. Please refresh the page.")
                st.rerun()
            except Exception as create_error:
                st.error(f"Failed to create table: {create_error}")
