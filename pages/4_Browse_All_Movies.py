# pages/4_Browse_All_Movies.py

import streamlit as st
import pandas as pd
import sqlite3
import html
import string # New import for the alphabet

# --- Security: Add the "Guard Clause" ---
if "authentication_status" not in st.session_state or st.session_state["authentication_status"] != True:
    st.error("You must log in to view this page. Please go to the Home page to log in.")
    st.stop() 

# --- Page Config ---
st.set_page_config(layout="wide", page_title="Browse All Movies")

# --- Helper function to load data ---
@st.cache_data
def load_movie_data():
    con = sqlite3.connect('movies.db')
    movies_df = pd.read_sql_query("SELECT * FROM movies", con)
    con.close()
    movies_df = movies_df.sort_values(by="title")
    return movies_df

movies_df = load_movie_data()

# --- Main Page ---
st.title("🎬 Browse the Full Movie Catalog")

# --- NEW: Alphabet Navigation Bar ---
st.markdown("##### Select a letter to browse movies by title:")

# Define a function to update the session state when a button is clicked
def set_letter(letter):
    st.session_state.selected_letter = letter
    st.session_state.browse_page = 0 # Reset to the first page

# Initialize session state if it doesn't exist
if 'selected_letter' not in st.session_state:
    st.session_state.selected_letter = "ALL"

# Create the alphabet list and the "ALL" button
alphabets = list(string.ascii_uppercase)
cols = st.columns(len(alphabets))

for i, letter in enumerate(alphabets):
    with cols[i]:
        # The on_click parameter calls our function to update the state
        st.button(letter, on_click=set_letter, args=(letter,), use_container_width=True)

st.divider()

# --- Apply Filtering based on the selected letter ---
if st.session_state.selected_letter == "ALL":
    filtered_movies = movies_df
else:
    filtered_movies = movies_df[movies_df['title'].str.startswith(st.session_state.selected_letter)]

# --- Pagination ---
if 'browse_page' not in st.session_state:
    st.session_state.browse_page = 0

PAGE_SIZE = 20
total_pages = -(-len(filtered_movies) // PAGE_SIZE) if len(filtered_movies) > 0 else 1

start_idx = st.session_state.browse_page * PAGE_SIZE
end_idx = start_idx + PAGE_SIZE
page_df = filtered_movies.iloc[start_idx:end_idx]

# --- Display Results Grid ---
st.write(f"Showing page **{st.session_state.browse_page + 1}** of **{total_pages}** for letter: **{st.session_state.selected_letter}**")

if page_df.empty:
    st.warning("No movies found for the selected letter.")
else:
    cols = st.columns(5)
    for i, (index, row) in enumerate(page_df.iterrows()):
        with cols[i % 5]:
            st.image(row['poster_url'], use_container_width=True)
            safe_title = html.escape(row['title'])
            st.markdown(f"<p style='text-align:center; font-size:0.9em;'>{safe_title}</p>", unsafe_allow_html=True)

# --- Pagination Buttons ---
st.divider()
prev_col, page_col, next_col = st.columns([1, 1, 1])

if st.session_state.browse_page > 0:
    if prev_col.button("⬅️ Previous Page"):
        st.session_state.browse_page -= 1
        st.rerun()

with page_col:
    st.write(f"Page {st.session_state.browse_page + 1} of {total_pages}")

if st.session_state.browse_page < total_pages - 1:
    if next_col.button("Next Page ➡️"):
        st.session_state.browse_page += 1
        st.rerun()