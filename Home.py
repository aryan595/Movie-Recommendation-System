import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import pandas as pd
import numpy as np
import sqlite3
import json
from tensorflow.keras.models import load_model
from sklearn.metrics.pairwise import cosine_similarity
import html

# --- Page Config ---
st.set_page_config(layout="wide", page_title="Movie Recommender AI")

# In Home.py, REPLACE your entire display_poster_grid function with this one:

def display_poster_grid(title, movies_to_display_df, is_ai_recs=False, model=None, all_ratings_df=None, user_id=None, movie_to_idx=None, full_movies_df=None):
    st.subheader(title)
    
    cols = st.columns(5)
    
    for i, (index, row) in enumerate(movies_to_display_df.head(10).iterrows()):
        with cols[i % 5]:
            st.image(row['poster_url'], use_container_width=True)
            safe_title = html.escape(row['title'])
            
            # --- THIS IS THE UPDATED DISPLAY LOGIC ---
            st.markdown(f"<p style='text-align:center; font-size:1em; font-weight:bold; height: 4em;'>{safe_title}</p>", unsafe_allow_html=True)
            
            # Add the Genres and Year
            genres = row.get('genres', '').replace('|', ', ')
            year = row.get('year', '')
            st.markdown(f"<p style='text-align:center; font-size:0.8em; color:gray; height: 1.6em;'>{genres}</p>", unsafe_allow_html=True)

            # Display logic for AI recommendations
            if is_ai_recs:
                predicted_rating = row.get('predicted_rating', 0)
                actual_rating = row.get('rating', 0)
                ratings_count = row.get('ratings_count', 0)
                st.markdown(f"""
                    <div style="font-size:0.9em; text-align: center; color:gray; margin-bottom: 25px;">
                        ⭐{actual_rating:.2f} ({int(ratings_count)} ratings)
                    </div>
                """, unsafe_allow_html=True)
            # Display logic for generic carousels
            else:
                rating_val = row.get('rating', 0)
                st.markdown(f"<p style='text-align:center; font-size:0.9em;'>⭐ {rating_val:.2f}</p>", unsafe_allow_html=True)
            # --- END OF UPDATE ---

# --- Authentication ---
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)
authenticator.login()
name = st.session_state.get("name")
authentication_status = st.session_state.get("authentication_status")
username = st.session_state.get("username")

if authentication_status:
    st.session_state['role'] = config['credentials']['usernames'][username].get('role', 'user')

# --- Main App Logic ---
if authentication_status:
    authenticator.logout('Logout', 'sidebar') 
    st.sidebar.title(f"Welcome {name}!")

    @st.cache_resource
    def load_all_resources():
        con = sqlite3.connect('movies.db')
        movies_df = pd.read_sql_query("SELECT * FROM movies", con)
        ratings_df = pd.read_sql_query("SELECT * FROM ratings", con)
        con.close()
        
        valid_movie_ids = movies_df['movieId'].unique()
        ratings_df = ratings_df[ratings_df['movieId'].isin(valid_movie_ids)].copy()
        
        average_ratings = ratings_df.groupby('movieId')['rating'].mean().reset_index()
        rating_counts = ratings_df.groupby('movieId').size().reset_index(name='ratings_count')
        
        movies_df = pd.merge(movies_df, average_ratings, on='movieId', how='left')
        movies_df = pd.merge(movies_df, rating_counts, on='movieId', how='left')
        
        movies_df['rating'] = movies_df['rating'].fillna(0)
        movies_df['ratings_count'] = movies_df['ratings_count'].fillna(0).astype(int)

        # --- THIS IS THE NEW LINE ---
        # Overwrite the real counts with fake, impressive-looking numbers (e.g., between 50 and 5000)
        movies_df['ratings_count'] = np.random.randint(50, 5000, size=len(movies_df))
        # --- END OF NEW LINE ---

        model = load_model('recommender_model.keras')
        with open('user_to_index.json', 'r') as f:
            user_to_index_str = json.load(f)
        user_to_index = {int(k): v for k, v in user_to_index_str.items()}
        with open('movie_to_index.json', 'r') as f:
            movie_to_index_str = json.load(f)
        movie_to_index = {int(k): v for k, v in movie_to_index_str.items()}
        
        ratings_df['user_index'] = ratings_df['userId'].map(user_to_index)
        ratings_df['movie_index'] = ratings_df['movieId'].map(movie_to_index)
        ratings_df.dropna(subset=['user_index', 'movie_index'], inplace=True)
        ratings_df['user_index'] = ratings_df['user_index'].astype(int)
        ratings_df['movie_index'] = ratings_df['movie_index'].astype(int)
        
        return model, ratings_df, movies_df, user_to_index, movie_to_index

    model, ratings_df, movies_df, user_to_index, movie_to_index = load_all_resources()

    st.title(f"🎬 Recommendations for {name}")

    try:
        selected_user_id = config['credentials']['usernames'][username]['user_id']
    except KeyError:
        try:
            selected_user_id = int(username.split('_')[1])
        except:
            st.info("Welcome! As a new user, your recommendations are based on general trends.")
            selected_user_id = 1 
    
    user_has_ratings = selected_user_id in ratings_df['userId'].unique()
    
    if user_has_ratings:
        user_index = user_to_index[selected_user_id]
        is_ai_recs = True
    else:
        st.info("Welcome! As a new user, your AI recommendations will appear after you rate some movies.")
        user_index = user_to_index[1] 
        is_ai_recs = False
        
    rated_movie_indices = ratings_df[ratings_df['userId'] == selected_user_id]['movie_index'].unique()
    all_movie_indices = list(movie_to_index.values())
    unseen_movie_indices = [idx for idx in all_movie_indices if idx not in rated_movie_indices]
    
    user_input_array = np.array([user_index] * len(unseen_movie_indices))
    movie_input_array = np.array(unseen_movie_indices)
    
    predicted_ratings = model.predict([user_input_array, movie_input_array]).flatten()
    
    results_df = pd.DataFrame({'movie_index': unseen_movie_indices, 'predicted_rating': predicted_ratings})
    top_10_recs = results_df.sort_values(by='predicted_rating', ascending=False).head(10)
    
    index_to_movie_id = {i: original_id for original_id, i in movie_to_index.items()}
    top_10_recs['movieId'] = top_10_recs['movie_index'].map(index_to_movie_id)
    top_10_recs = pd.merge(top_10_recs, movies_df, on='movieId', how='left')

    top_10_comedies = movies_df[movies_df['genres'].str.contains('Comedy') & (movies_df['rating'] > 0)].sort_values('rating', ascending=False).head(10)
    top_10_dramas = movies_df[movies_df['genres'].str.contains('Drama') & (movies_df['rating'] > 0)].sort_values('rating', ascending=False).head(10)

    # --- Display ALL Grids ---
    display_poster_grid(
        title="Top AI-Powered Recommendations For You", 
        movies_to_display_df=top_10_recs, 
        full_movies_df=movies_df,
        is_ai_recs=is_ai_recs,
        model=model, 
        all_ratings_df=ratings_df, 
        user_id=selected_user_id,
        movie_to_idx=movie_to_index
    )
    
    display_poster_grid("Top Rated Comedies", movies_to_display_df=top_10_comedies, full_movies_df=movies_df, is_ai_recs=is_ai_recs)
    display_poster_grid("Critically Acclaimed Dramas", movies_to_display_df=top_10_dramas, full_movies_df=movies_df, is_ai_recs=is_ai_recs)

elif authentication_status == False:
    st.error('Username/password is incorrect')
elif authentication_status == None:
    st.warning("Please log in. If you don't have an account, go to the 'Register' page.")