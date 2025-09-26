import streamlit as st

# Add this "guard clause" at the top of all protected pages
if "authentication_status" not in st.session_state or st.session_state["authentication_status"] != True:
    st.error("You must log in to view this page. Please go to the Home page to log in.")
    st.stop() # Stop executing the rest of the script
    
# --- The rest of your page code (import pandas, load_data, etc.) goes below ---

# pages/2_New_User_Recommender.py

import streamlit as st
import pandas as pd
import sqlite3

st.set_page_config(layout="wide", page_title="New User Recommendations")

# In pages/2_New_User_Recommender.py, REPLACE the load_movie_data function:

@st.cache_data  # We can keep this cache, it's fine
def load_movie_data():
    con = sqlite3.connect('movies.db')
    all_movies_df = pd.read_sql_query("SELECT * FROM movies", con)
    ratings_df = pd.read_sql_query("SELECT * FROM ratings", con)
    con.close()
    
    # --- ADD THE FIX HERE AS WELL ---
    average_ratings = ratings_df.groupby('movieId')['rating'].mean().reset_index()
    all_movies_df = pd.merge(all_movies_df, average_ratings, on='movieId', how='left')
    all_movies_df['rating'] = all_movies_df['rating'].fillna(0)

    # (The rest of the logic is the same)
    movie_popularity = ratings_df.groupby('movieId').size().reset_index(name='ratings_count')
    popular_movies_df = pd.merge(all_movies_df, movie_popularity, on='movieId')
    popular_movies_df = popular_movies_df.sort_values(by=['ratings_count', 'rating'], ascending=False)
    popular_movies_list = popular_movies_df.head(500)
    
    return popular_movies_list, all_movies_df

popular_movies_df, all_movies_df = load_movie_data()

st.title("👋 New User? Let's Find Your Taste!")
st.markdown("Please select at least 5 movies you love from the list of popular movies below.")

movie_list = popular_movies_df['title'].tolist()
selected_movies = st.multiselect("Select movies you like:", movie_list)

if st.button("Get Recommendations"):
    if len(selected_movies) < 5:
        st.warning("Please select at least 5 movies for better recommendations.")
    else:
        liked_genres = set()
        for movie in selected_movies:
            genres = popular_movies_df[popular_movies_df['title'] == movie]['genres'].iloc[0].split('|')
            liked_genres.update(genres)
        
        def genre_match_score(genres_str):
            movie_genres = set(genres_str.split('|'))
            return len(liked_genres.intersection(movie_genres))

        recommendations_df = all_movies_df[~all_movies_df['title'].isin(selected_movies)].copy()
        recommendations_df['match_score'] = recommendations_df['genres'].apply(genre_match_score)
        
        final_recommendations = recommendations_df.sort_values(by='match_score', ascending=False).head(10)

        st.subheader("Based on your selections, you might also like:")
        cols = st.columns(5)
        for idx, row in final_recommendations.reset_index().iterrows():
            with cols[idx % 5]:
                st.image(row['poster_url'], caption=row['title'])