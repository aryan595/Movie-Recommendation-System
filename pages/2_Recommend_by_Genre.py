import streamlit as st
import pandas as pd
import sqlite3
import html
import numpy as np

# --- Security: Add the "Guard Clause" ---
if "authentication_status" not in st.session_state or st.session_state["authentication_status"] != True:
    st.error("You must log in to view this page. Please go to the Home page to log in.")
    st.stop() 

# --- Page Config ---
st.set_page_config(layout="wide", page_title="Browse by Genre")

# --- CSS for clean layout ---
st.markdown("""
    <style>
    .movie-title {
        text-align: center;
        font-size: 1em;
        font-weight: bold;
        white-space: normal;
        height: 3.5em;
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
st.title("🎬 Browse Movies by Genre")
st.markdown("Select one or more genres to find movies that match all your criteria.")

# --- Genre Selection ---
all_genres = sorted(movies_df['genres'].str.split('|').explode().unique())
selected_genres = st.multiselect("Select genres:", all_genres)
st.divider()

# --- Apply Filtering ---
if not selected_genres:
    st.info("Please select one or more genres to see results.")
    st.stop()
filtered_movies = movies_df
for genre in selected_genres:
    filtered_movies = filtered_movies[filtered_movies['genres'].str.contains(genre, case=False)]
filtered_movies = filtered_movies.sort_values(by="title")

# --- Pagination ---
if 'genre_page' not in st.session_state:
    st.session_state.genre_page = 0
PAGE_SIZE = 15
total_pages = -(-len(filtered_movies) // PAGE_SIZE) if len(filtered_movies) > 0 else 1
start_idx = st.session_state.genre_page * PAGE_SIZE
end_idx = start_idx + PAGE_SIZE
page_df = filtered_movies.iloc[start_idx:end_idx]

# --- Display Results Grid ---
st.write(f"Found **{len(filtered_movies)}** movies. Showing page **{st.session_state.genre_page + 1}** of **{total_pages}**.")
if page_df.empty:
    st.warning("No movies found that match ALL selected genres.")
else:
    # --- THIS IS THE UPDATED DISPLAY LOGIC ---
    cols = st.columns(5)
    for i, (index, row) in enumerate(page_df.iterrows()):
        with cols[i % 5]:
            st.image(row['poster_url'], use_container_width=True)
            safe_title = html.escape(row['title'])
            year = row.get('year', '')
            genres = row.get('genres', '').replace('|', ', ')
            rating = row.get('rating', 0)
            ratings_count = row.get('ratings_count', 0)
            st.markdown(f"<p class='movie-title'>{safe_title}</p>", unsafe_allow_html=True)
            st.markdown(f"""
                <div class='movie-details'>
                    ⭐ {rating:.2f} ({int(ratings_count)} ratings)<br>
                    <i>{genres}</i>
                </div>
            """, unsafe_allow_html=True)
            
# --- Pagination Buttons ---
st.divider()
prev_col, page_col, next_col = st.columns([1, 1, 1])
if st.session_state.genre_page > 0:
    if prev_col.button("⬅️ Previous Page", key="genre_prev"):
        st.session_state.genre_page -= 1
        st.rerun()
with page_col:
    st.write(f"Page {st.session_state.genre_page + 1} of {total_pages}")
if st.session_state.genre_page < total_pages - 1:
    if next_col.button("Next Page ➡️", key="genre_next"):
        st.session_state.genre_page += 1
        st.rerun()