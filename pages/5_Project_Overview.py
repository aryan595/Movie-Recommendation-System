# pages/3_Project_Overview.py

import streamlit as st

st.set_page_config(layout="wide", page_title="Project Overview")

st.title("Project Overview: AI-Powered Movie Recommendation Dashboard")

st.header("Objective")
st.markdown("""
This project demonstrates a full-fledged, multi-functional movie recommendation system. The goal was to go beyond a simple model and create an interactive dashboard that showcases several key concepts in Data Warehousing and Mining (DWM) and modern AI.
""")

st.header("Key Features")
st.markdown("""
- **Personalized Recommendations (Home):** Utilizes a deep learning model (Neural Collaborative Filtering) to provide recommendations based on a user's historical ratings. It also includes an **Explainable AI (XAI)** component to justify its suggestions.
- **Movie Explorer:** Implements a **Content-Based Filtering** model using TF-IDF and Cosine Similarity to find movies with similar genre profiles.
- **New User Onboarding:** Addresses the **"Cold Start" problem** by providing genre-based recommendations to new users after they select a few movies they like.
""")

st.header("Technology & Concepts")
st.markdown("""
- **Language:** Python
- **Libraries:** Streamlit (UI), Pandas (Data Manipulation), Scikit-learn (Content-Based Model), TensorFlow/Keras (Deep Learning Model).
- **DWM Concepts:**
  - Collaborative Filtering (Deep Learning Approach)
  - Content-Based Filtering
  - Cold Start Problem & Solution
  - Data Integration & Cleaning
  - Interactive Data Visualization
""")

st.header("Dataset")
st.markdown("""
The project integrates data from two primary sources:
1.  **MovieLens (Small):** Provides user rating data (`ratings.csv`).
2.  **The Movies Dataset (Kaggle):** Enriched with poster URLs and detailed movie metadata.
These datasets were cleaned and merged to create a robust foundation for the models.
""")