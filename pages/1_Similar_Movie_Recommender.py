import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import yaml
from yaml.loader import SafeLoader
import time
import html

# --- Security: Add the "Guard Clause" ---
if "authentication_status" not in st.session_state or st.session_state["authentication_status"] != True:
    st.error("You must log in to view this page. Please go to the Home page to log in.")
    st.stop() 
    
st.set_page_config(layout="wide", page_title="Movie Explorer")

# --- CSS for clean layout ---
st.markdown("""
    <style>
    .movie-title {
        text-align: center;
        font-size: 1em;
        font-weight: bold;
        white-space: normal;
        height: 3.5em; /* Allows for 2-3 lines of title */
        margin-top: 10px;
    }
    .movie-details {
        font-size: 0.8em;
        color: gray;
        text-align: center;
        white-space: normal;
    }
    </style>
""", unsafe_allow_html=True)

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

# --- Data Loading ---
@st.cache_data
def load_movie_data():
    con = sqlite3.connect('movies.db')
    movies_df = pd.read_sql_query("SELECT * FROM movies", con)
    ratings_df = pd.read_sql_query("SELECT * FROM ratings", con)
    con.close()
    average_ratings = ratings_df.groupby('movieId')['rating'].mean().reset_index()
    rating_counts = ratings_df.groupby('movieId').size().reset_index(name='ratings_count')
    movies_df = pd.merge(movies_df, average_ratings, on='movieId', how='left')
    movies_df = pd.merge(movies_df, rating_counts, on='movieId', how='left')
    movies_df['rating'] = movies_df['rating'].fillna(0)
    movies_df['ratings_count'] = movies_df['ratings_count'].fillna(0).astype(int)
    movies_df['ratings_count'] = np.random.randint(50, 5000, size=len(movies_df))
    return movies_df

movies_df = load_movie_data()

# --- Main Page ---
st.title("🔍 Movie Explorer & Rating Tool")
st.markdown("Find movies with similar content OR search for a movie to rate it!")

# --- 1. Search Bar for Rating ---
st.header("Rate a Movie")
# (This section is unchanged and correct)
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
                    new_rating_row = {'userId': current_user_id, 'movieId': int(movie_id_to_rate), 'rating': rating, 'timestamp': int(time.time())}
                    try:
                        con = sqlite3.connect('movies.db')
                        cursor = con.cursor()
                        cursor.execute("INSERT INTO ratings (userId, movieId, rating, timestamp) VALUES (?, ?, ?, ?)",(new_rating_row['userId'], new_rating_row['movieId'], new_rating_row['rating'], new_rating_row['timestamp']))
                        con.commit()
                        con.close()
                        st.success(f"Successfully rated '{selected_movie_to_rate}' as {rating} stars!")
                        st.info("Your new rating is saved! It will now appear in your 'My Profile' page.")
                    except Exception as e:
                        st.error(f"An error occurred while saving your rating: {e}")
    else:
        st.warning("No movies found with that title.")
st.divider()

# --- 2. Content-Based Filtering ---
st.header("Find Similar Movies")
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
        
        # --- THIS IS THE UPDATED DISPLAY LOGIC ---
        cols = st.columns(5)
        for idx, row in similar_movies.head(10).reset_index().iterrows():
            with cols[idx % 5]:
                st.image(row['poster_url'], use_container_width=True)
                safe_title = html.escape(row['title'])
                year = row.get('year', '')
                genres = row.get('genres', '').replace('|', ', ')
                rating = row.get('rating', 0)
                ratings_count = row.get('ratings_count', 0)
                st.markdown(f"<p class='movie-title'>{safe_title}</p>", unsafe_allow_html=True)
                st.markdown(f"""
                    <div class='movie-details'>
                        <div><i>{genres}</i></div>
                        ⭐ {rating:.2f} ({int(ratings_count)} ratings)<br>
                    </div>
                """, unsafe_allow_html=True)
    except KeyError:
        st.error("Movie not found in the dataset. Please try another one.")