# pages/3_My_Profile_&_Analytics.py

import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import yaml
from yaml.loader import SafeLoader

# --- Security: Add the "Guard Clause" ---
# This ensures only logged-in users can see this page
if "authentication_status" not in st.session_state or st.session_state["authentication_status"] != True:
    st.error("You must log in to view this page. Please go to the Home page to log in.")
    st.stop() # Stop executing the rest of the script
    
# --- Page Title ---
st.set_page_config(layout="wide", page_title="Analytics")
st.title(f"📊 Analytics for {st.session_state['name']}")
st.markdown("Here's a deep dive into your unique movie taste!")

# --- Helper Function to Load Data ---
# We cache this to keep it fast
# @st.cache_data
# In pages/3_My_Profile_&_Analytics.py
def load_data():
    con = sqlite3.connect('movies.db')
    movies_df = pd.read_sql_query("SELECT * FROM movies", con)
    ratings_df = pd.read_sql_query("SELECT * FROM ratings", con)
    con.close()
    return movies_df, ratings_df

movies_df, ratings_df = load_data()

# REPLACE IT WITH THIS CORRECT LOGIC:
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Get the logged-in user's numeric ID directly from the config file.
# This works for "user_91" AND new users like "sam".
current_user_name = st.session_state['username']
current_user_id = config['credentials']['usernames'][current_user_name]['user_id']

# Filter all ratings for just this user
user_ratings_df = ratings_df[ratings_df['userId'] == current_user_id]
if user_ratings_df.empty:
    st.info("You haven't rated any movies yet. Your analytics will appear here once you do!")
    st.stop()

# Merge with movie details
user_full_data = pd.merge(user_ratings_df, movies_df, on='movieId', how='left')


# --- 1. KPI Cards ---
st.header("Your Stats")
total_ratings = len(user_ratings_df)
avg_rating = user_ratings_df['rating'].mean()

# Calculate favorite genre
all_genres = user_full_data['genres'].str.split('|').explode()
fav_genre = all_genres.mode()[0] # The most frequent genre

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Total Movies Rated", total_ratings)
kpi2.metric("Your Average Rating", f"{avg_rating:.1f} ⭐")
kpi3.metric("Your Favorite Genre", fav_genre)

st.divider()

# --- 2. Interactive Charts (Plotly) ---
c1, c2 = st.columns(2)

with c1:
    # Pie Chart of Genre Distribution
    st.subheader("Your Genre Profile")
    genre_pie_data = all_genres.value_counts().reset_index()
    genre_pie_data.columns = ['genre', 'count']
    fig_pie = px.pie(genre_pie_data.head(10), values='count', names='genre', 
                     title="Top 10 Genres You've Rated", hole=.3)
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_pie, use_container_width=True)

with c2:
    # Histogram of Rating Distribution
    st.subheader("Your Rating Distribution")
    fig_hist = px.histogram(user_ratings_df, x='rating', nbins=10, 
                            title="How You Rate Movies")
    fig_hist.update_xaxes(title="Rating")
    fig_hist.update_yaxes(title="Count")
    st.plotly_chart(fig_hist, use_container_width=True)

st.divider()

# --- 3. Full Rating History ---
st.header("Your Full Rating History")
st.markdown("Click any column header to sort.")
# Show a clean table with the poster, title, and the user's rating
st.dataframe(
    user_full_data[['title', 'genres', 'rating', 'poster_url']],
    column_config={
        "title": "Movie Title",
        "genres": "Genres",
        "rating": "Your Rating",
        "poster_url": st.column_config.ImageColumn("Poster", width=100)
    },
    use_container_width=True,
    hide_index=True,
)