# pages/1_Movie_Explorer.py

import streamlit as st
import pandas as pd
import sqlite3
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import yaml
from yaml.loader import SafeLoader
import time

# --- Security: Add the "Guard Clause" ---
if "authentication_status" not in st.session_state or st.session_state["authentication_status"] != True:
    st.error("You must log in to view this page. Please go to the Home page to log in.")
    st.stop() 
    
st.set_page_config(layout="wide", page_title="Movie Explorer")

# --- Load Config to get User ID ---
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

try:
    current_user_name = st.session_state['username']
    current_user_id = config['credentials']['usernames'][current_user_name]['user_id']
except KeyError:
    try:
        current_user_id = int(current_user_name.split('_')[1])
    except:
        st.error("Could not verify your User ID. Using default.")
        current_user_id = 1

def load_movie_data():
    con = sqlite3.connect('movies.db')
    movies_df = pd.read_sql_query("SELECT * FROM movies", con)
    ratings_df = pd.read_sql_query("SELECT * FROM ratings", con)
    con.close()
    
    # --- THIS IS THE FIX ---
    movies_df.dropna(subset=['poster_url'], inplace=True)
    # --- END OF FIX ---

    average_ratings = ratings_df.groupby('movieId')['rating'].mean().reset_index()
    movies_df = pd.merge(movies_df, average_ratings, on='movieId', how='left')
    movies_df['rating'] = movies_df['rating'].fillna(0)
    
    return movies_df

# --- END OF FUNCTION CORRECTION ---

movies_df = load_movie_data()

st.title("🔍 Movie Explorer & Rating Tool")
st.markdown("Find movies with similar content OR search for a movie to rate it!")

# --- 1. Search Bar for Rating ---
st.header("Rate a Movie")
search_term = st.text_input("Search for a movie you've seen:")
if search_term:
    search_results = movies_df[movies_df['title'].str.contains(search_term, case=False)]
    if not search_results.empty:
        selected_movie_to_rate = st.selectbox("Select the movie you want to rate:", search_results['title'])
        if selected_movie_to_rate:
            movie_details = movies_df[movies_df['title'] == selected_movie_to_rate].iloc[0]
            movie_id_to_rate = movie_details['movieId']
            
            c1, c2 = st.columns([1, 2])
            with c1:
                st.image(movie_details['poster_url'])
            with c2:
                st.subheader(movie_details['title'])
                st.write(movie_details['genres'])
                
                rating = st.slider("Your Rating (from 0.5 to 5.0):", 0.5, 5.0, 3.0, 0.5)
                
                if st.button("Submit Your Rating"):
                    new_rating_row = {
                        'userId': current_user_id,
                        'movieId': int(movie_id_to_rate), # Ensure it's a standard integer
                        'rating': rating,
                        'timestamp': int(time.time())
                    }

                    # --- This is the new database logic ---
                    try:
                        con = sqlite3.connect('movies.db')
                        cursor = con.cursor()
                        # Use parameterized query to safely insert data
                        cursor.execute("INSERT INTO ratings (userId, movieId, rating, timestamp) VALUES (?, ?, ?, ?)",
                                       (new_rating_row['userId'], new_rating_row['movieId'], 
                                        new_rating_row['rating'], new_rating_row['timestamp']))
                        con.commit() # Save the change
                        con.close()
                        
                        st.success(f"Successfully rated '{selected_movie_to_rate}' as {rating} stars!")
                        st.info("Your new rating is saved! It will now appear in your 'My Profile' page.")
                    except Exception as e:
                        st.error(f"An error occurred while saving your rating: {e}")

    else:
        st.warning("No movies found with that title.")

st.divider()

# --- 2. Content-Based Filtering (This code will now work) ---
st.header("Find Similar Movies")

# This code was failing because 'movies_df' was a tuple. Now it's a DataFrame, so this will work.
tfidf = TfidfVectorizer(stop_words='english')
tfidf_matrix = tfidf.fit_transform(movies_df['genres'])
cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
indices = pd.Series(movies_df.index, index=movies_df['title']).drop_duplicates()

movie_list = movies_df['title'].tolist()
selected_movie = st.selectbox("Select a movie to find similar ones:", movie_list)

if st.button("Find Similar Movies"):
    try:
        idx = indices[selected_movie]
        sim_scores = list(enumerate(cosine_sim[idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        sim_scores = sim_scores[1:11] 
        movie_indices = [i[0] for i in sim_scores]
        similar_movies = movies_df.iloc[movie_indices]

        st.subheader(f"Movies similar to '{selected_movie}':")
        cols = st.columns(5)
        for idx, row in similar_movies.head(10).reset_index().iterrows():
            with cols[idx % 5]:
                st.image(row['poster_url'], caption=row['title'])
    except KeyError:
        st.error("Movie not found in the dataset. Please try another one.")