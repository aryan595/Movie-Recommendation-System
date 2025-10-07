# pages/0_Register.py

import streamlit as st
import yaml
from yaml.loader import SafeLoader
from streamlit_authenticator.utilities import Hasher
import pandas as pd

st.set_page_config(layout="wide", page_title="Register")
st.title("🔐 Register a New Account")

# --- THIS IS THE FIX: Load the config file correctly ---
try:
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)
except FileNotFoundError:
    # If the file doesn't exist, create a default structure
    config = {'credentials': {'usernames': {}}, 'cookie': {}}

# Create a registration form
with st.form("Register User"):
    email = st.text_input("Email")
    name = st.text_input("Full Name")
    username = st.text_input("Username (must be unique)")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    submitted = st.form_submit_button("Register")

if submitted:
    if not (email and name and username and password and confirm_password):
        st.warning("Please fill out all fields.")
    elif password != confirm_password:
        st.error("Passwords do not match.")
    elif username in config['credentials']['usernames']:
        st.error("This username already exists. Please choose another.")
    else:
        try:
            ratings_df = pd.read_csv('ratings_clean_final.csv')
            max_user_id = ratings_df['userId'].max()
            new_user_id = max_user_id + 1
        except (FileNotFoundError, pd.errors.EmptyDataError):
            new_user_id = 611

        hashed_password = Hasher.hash(password)
        
        # Add the new user to the config dictionary
        config['credentials']['usernames'][username] = {
            'email': email,
            'name': name,
            'password': hashed_password,
            'user_id': int(new_user_id),
            'role': 'user'
        }
        
        # --- THIS IS ALSO THE FIX: Save the updated config back to the file ---
        # This ensures the 'cookie' section is preserved
        with open('config.yaml', 'w') as file:
            yaml.dump(config, file, default_flow_style=False)
            
        st.success(f"User '{username}' registered successfully! Your new User ID is {new_user_id}.")
        st.balloons()
        st.info("You can now go to the 'Home' page to log in.")