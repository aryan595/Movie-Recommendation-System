# pages/6_Admin_Dashboard.py

import streamlit as st
import yaml
from yaml.loader import SafeLoader
import pandas as pd
import sqlite3

# --- ADMIN-ONLY GUARD CLAUSE ---
if "role" not in st.session_state or st.session_state["role"] != "admin":
    st.error("You must be an admin to view this page.")
    st.stop()

# --- Admin Page Content ---
st.set_page_config(layout="wide", page_title="Admin Dashboard")
st.title("⚙️ Admin Dashboard")
st.markdown("This page is only visible to users with the 'admin' role.")

# Load all users from the config file
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)
users = config['credentials']['usernames']

st.divider()

# --- Platform Statistics (Same as before) ---
st.header("Platform Statistics")
try:
    con = sqlite3.connect('movies.db')
    ratings_df = pd.read_sql_query("SELECT * FROM ratings", con)
    movies_df = pd.read_sql_query("SELECT * FROM movies", con)
    con.close()
    
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Total Registered Users", len(users))
    kpi2.metric("Total Movies in Database", len(movies_df))
    kpi3.metric("Total Ratings Submitted", len(ratings_df))
except Exception as e:
    st.error(f"Could not load platform stats: {e}")

st.divider()

# --- NEW FEATURE: User Management ---
st.header("User Management")
st.write("Here you can view and manage all registered users.")

# Display a list of all registered users
user_list = []
for username, details in users.items():
    user_list.append({
        "Username": username,
        "Name": details.get('name'),
        "Email": details.get('email'),
        "Role": details.get('role'),
        "User ID": details.get('user_id')
    })
st.dataframe(pd.DataFrame(user_list), use_container_width=True)

# Delete a user
with st.expander("⚠️ Delete a User"):
    users_to_delete = list(users.keys())
    user_to_delete = st.selectbox("Select a user to delete:", users_to_delete)
    
    if st.button("Delete User Permanently", type="primary"):
        if user_to_delete == st.session_state['username']:
            st.error("You cannot delete yourself.")
        else:
            with st.spinner(f"Deleting user '{user_to_delete}'..."):
                # Remove the user from the config dictionary
                del config['credentials']['usernames'][user_to_delete]
                # Save the updated config back to the file
                with open('config.yaml', 'w') as file:
                    yaml.dump(config, file, default_flow_style=False)
                st.success(f"User '{user_to_delete}' has been deleted.")
                st.info("The user list will update on the next page refresh.")
                st.rerun()

st.divider()

# --- NEW FEATURE: Content Management ---
st.header("Content Management")
with st.expander("⚠️ Delete a Movie"):
    movie_title_to_delete = st.text_input("Search for a movie title to delete:")
    
    if movie_title_to_delete:
        try:
            con = sqlite3.connect('movies.db')
            # Find matching movies
            query = f"SELECT movieId, title FROM movies WHERE title LIKE ?"
            search_results = pd.read_sql_query(query, con, params=(f'%{movie_title_to_delete}%',))
            con.close()

            if not search_results.empty:
                movie_to_delete_id = st.selectbox("Select the exact movie to delete:", search_results['movieId'], format_func=lambda x: search_results[search_results['movieId'] == x]['title'].iloc[0])
                
                if st.button("Delete Movie Permanently", type="primary"):
                    with st.spinner(f"Deleting movie ID {movie_to_delete_id} and all its ratings..."):
                        con = sqlite3.connect('movies.db')
                        cursor = con.cursor()
                        # Delete ratings for this movie
                        cursor.execute("DELETE FROM ratings WHERE movieId = ?", (movie_to_delete_id,))
                        ratings_deleted = cursor.rowcount
                        # Delete the movie itself
                        cursor.execute("DELETE FROM movies WHERE movieId = ?", (movie_to_delete_id,))
                        movies_deleted = cursor.rowcount
                        con.commit()
                        con.close()
                        st.success(f"Deleted {ratings_deleted} ratings and {movies_deleted} movie record.")
                        st.warning("IMPORTANT: Your AI model is now out of sync. You must re-run your 'Model Trainer' script to update the AI.")
                        st.rerun()
            else:
                st.warning("No movies found with that title.")
        except Exception as e:
            st.error(f"An error occurred: {e}")