
import streamlit as st
import pandas as pd
import os
import json

RULES_FILE = os.path.join(os.getcwd(), "rules.json")

# --- Rules Storage ---
def _load_rules():
    """Load rules from the JSON file."""
    if os.path.exists(RULES_FILE):
        try:
            with open(RULES_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    return []

def _save_rules(rules):
    """Save rules to the JSON file."""
    with open(RULES_FILE, 'w') as f:
        json.dump(rules, f, indent=4)

def initialize_rules():
    """Initialize session state for rules from file."""
    if 'rules' not in st.session_state:
        st.session_state.rules = _load_rules()

def add_rule(rule_type, deduction_rate, condition=None):
    """Add a new deduction rule."""
    rules = st.session_state.rules
    new_id = max([rule['id'] for rule in rules], default=0) + 1
    new_rule = {
        "id": new_id,
        "rule_type": rule_type,
        "rule_condition": condition,
        "deduction_rate": deduction_rate,
        "is_active": True
    }
    rules.append(new_rule)
    st.session_state.rules = rules
    _save_rules(rules)

def get_all_rules():
    """Fetch all deduction rules."""
    if 'rules' not in st.session_state:
        initialize_rules()
    return pd.DataFrame(st.session_state.rules)

def update_rule_status(rule_id, is_active):
    """Update the is_active status of a rule."""
    rules = st.session_state.rules
    for rule in rules:
        if rule['id'] == rule_id:
            rule['is_active'] = is_active
            break
    st.session_state.rules = rules
    _save_rules(rules)

def delete_rule(rule_id):
    """Delete a rule."""
    rules = [rule for rule in st.session_state.rules if rule['id'] != rule_id]
    st.session_state.rules = rules
    _save_rules(rules)


# --- UI Components ---
def settings_page():
    """Renders the Deduction Rules settings page."""
    st.header("Deduction Rules")

    # Initialize rules if not already done
    initialize_rules()

    # --- Add New Rule Form ---
    st.subheader("Add New Deduction Rule")

    rule_type = st.selectbox("Rule Type", ["General", "Year", "Make Model"])

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


    elif rule_type == "Make Model":
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
            rules_df = get_all_rules()
            duplicate_found = False

            if rule_type == "General":
                if 'General' in rules_df[rules_df['rule_type'] == 'General']['rule_condition'].values:
                    st.toast("General deduction rule already exists. Please delete it to add a new one.", icon="⚠️")
                    duplicate_found = True

            elif rule_type == "Year":
                if condition in rules_df[rules_df['rule_type'] == 'Year']['rule_condition'].values:
                    st.toast(f"Deduction rule for year {condition} already exists.", icon="⚠️")
                    duplicate_found = True

            elif rule_type == "Make Model":
                if condition in rules_df[rules_df['rule_type'] == 'Make Model']['rule_condition'].values:
                    st.toast(f"Deduction rule for {condition.replace('|', ' ')} already exists.", icon="⚠️")
                    duplicate_found = True

            if not duplicate_found:
                add_rule(rule_type, deduction_value, condition)
                st.success("Deduction rule added successfully!")
                st.rerun()
        else:
            st.warning("Please fill in all the details.")

    # --- Existing Rules ---
    st.subheader("Existing Deduction Rules")

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
