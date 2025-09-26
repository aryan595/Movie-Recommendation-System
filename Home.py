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
st.set_page_config(layout="wide", page_title="Movie Recommendation System")

# --- Helper Function for a Static Poster Grid Display ---
# --- UPDATED: This function now takes the full movie list as an argument ---
def display_poster_grid(title, movies_to_display_df, full_movies_df, is_ai_recs=False, model=None, all_ratings_df=None, user_id=None, movie_to_idx=None):
    st.subheader(title)
    
    cols = st.columns(5)
    
    for i, (index, row) in enumerate(movies_to_display_df.head(10).iterrows()):
        with cols[i % 5]:
            st.image(row['poster_url'], use_container_width=True)
            safe_title = html.escape(row['title'])
            rating_val = row.get('predicted_rating', row.get('rating', 0))
            st.markdown(f"<p style='text-align:center; font-size:0.9em; height: 40px;'>{safe_title}</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align:center; font-size:0.8em; color:gray;'>⭐ {rating_val:.2f}</p>", unsafe_allow_html=True)

            if is_ai_recs:
                with st.expander("Why was this recommended?"):
                    try:
                        user_high_rated_raw = all_ratings_df[(all_ratings_df['userId'] == user_id) & (all_ratings_df['rating'] >= 4.0)]
                        
                        # THE FIX: We merge with the FULL movie list, not the small recommended list
                        user_high_rated = pd.merge(user_high_rated_raw, full_movies_df[['movieId', 'title']], on='movieId', how='inner')

                        if not user_high_rated.empty:
                            movie_embedding_weights = model.get_layer('MovieEmbedding').get_weights()[0]
                            rec_movie_index = movie_to_idx[row['movieId']]
                            rec_movie_embedding = movie_embedding_weights[rec_movie_index]
                            user_movies_indices = user_high_rated['movie_index'].unique()
                            user_movies_embeddings = movie_embedding_weights[user_movies_indices]
                            similarities = cosine_similarity([rec_movie_embedding], user_movies_embeddings)[0]
                            most_similar_index_in_list = similarities.argsort()[-1]
                            most_similar_movie_index = user_movies_indices[most_similar_index_in_list]
                            similar_movie_title = user_high_rated[user_high_rated['movie_index'] == most_similar_movie_index]['title'].iloc[0]
                            st.write(f"Because you loved **{html.escape(similar_movie_title)}**!")
                        else:
                            st.write("This is a top general recommendation. Rate some movies 4 stars or higher to get personalized reasons!")
                    except Exception as e:
                        st.write("Could not determine a specific reason.")

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
        
        # --- THIS IS THE FIX ---
        # We drop any rows where the poster_url is missing.
        movies_df.dropna(subset=['poster_url'], inplace=True)
        # --- END OF FIX ---
        
        average_ratings = ratings_df.groupby('movieId')['rating'].mean().reset_index()
        movies_df = pd.merge(movies_df, average_ratings, on='movieId', how='left')
        movies_df['rating'] = movies_df['rating'].fillna(0)
        
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

    st.title(f"🎬 Top Recommendations for You")

    try:
        selected_user_id = config['credentials']['usernames'][username]['user_id']
    except KeyError:
        try:
            selected_user_id = int(username.split('_')[1])
        except:
            st.info("Welcome! As a new user, your recommendations are based on general trends.")
            selected_user_id = 1 
    
    # --- Data Preparation for ALL Grids ---
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
        title="", 
        movies_to_display_df=top_10_recs, 
        full_movies_df=movies_df, # <-- THE FIX: Pass the full movie list
        is_ai_recs=is_ai_recs,
        model=model, 
        all_ratings_df=ratings_df, 
        user_id=selected_user_id,
        movie_to_idx=movie_to_index
    )
    
    st.title(f"Top Rated Comedies")
    display_poster_grid("", top_10_comedies, movies_df)
    st.title(f"Critically Acclaimed Dramas")
    display_poster_grid("", top_10_dramas, movies_df)

elif authentication_status == False:
    st.error('Username/password is incorrect')
elif authentication_status == None:
    st.warning("Please log in. If you don't have an account, go to the 'Register' page.")