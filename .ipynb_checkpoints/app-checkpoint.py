import streamlit as st
import pandas as pd
import numpy as np
from sklearn.decomposition import NMF

# --- Caching the model training to make the app faster ---
@st.cache_resource
def train_nmf_model():
    # Load the data
    movies_df = pd.read_csv('ml-latest-small/movies.csv')
    ratings_df = pd.read_csv('ml-latest-small/ratings.csv')
    df = pd.merge(ratings_df, movies_df, on='movieId')
    
    # Create the utility matrix
    utility_matrix = df.pivot_table(index='userId', columns='title', values='rating').fillna(0)
    
    # Create and train the NMF model
    model = NMF(n_components=20, init='random', random_state=42)
    W = model.fit_transform(utility_matrix)
    H = model.components_
    
    # Reconstruct the predicted ratings matrix
    predicted_ratings_matrix = np.dot(W, H)
    predicted_ratings_df = pd.DataFrame(predicted_ratings_matrix, columns=utility_matrix.columns, index=utility_matrix.index)
    
    return utility_matrix, predicted_ratings_df

# --- Load the data and trained model ---
utility_matrix, predicted_ratings_df = train_nmf_model()

# --- Building the Streamlit App ---
st.title('🎬 Movie Recommendation Engine')

st.write("This app recommends movies to users based on a machine learning model.")

# Get a list of all user IDs
all_user_ids = utility_matrix.index.tolist()

# Create a dropdown menu for the user to select their ID
selected_user_id = st.selectbox("Select your User ID:", all_user_ids)

# Create a button to get recommendations
if st.button('Get My Recommendations'):
    st.write(f"Here are the Top 10 recommendations for User {selected_user_id}:")
    
    # Get predictions and filter out seen movies
    user_predictions = predicted_ratings_df.loc[selected_user_id]
    user_actual_ratings = utility_matrix.loc[selected_user_id]
    unseen_movies = user_actual_ratings[user_actual_ratings == 0]
    recommendations = user_predictions[unseen_movies.index]
    
    # Get top 10 and display them
    top_10_recommendations = recommendations.sort_values(ascending=False).head(10)
    
    st.table(top_10_recommendations)