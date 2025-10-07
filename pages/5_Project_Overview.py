import streamlit as st

st.set_page_config(layout="wide", page_title="Project Overview")

st.title("Project Overview: AI-Powered Movie Recommendation Dashboard")

# --- OBJECTIVE ---
st.header("Objective")
st.markdown("""
This project demonstrates a full-fledged, multi-functional movie recommendation system built from the ground up. The primary objective was to move beyond a single, basic model and engineer a complete, interactive dashboard that showcases a deep understanding of Data Warehousing and Mining (DWM) principles. The application is designed to tackle real-world challenges such as data inconsistency, the "cold start" problem for new users, model performance tuning, and creating an intuitive, professional user experience similar to modern streaming platforms.
""")

st.divider()

# --- APPLICATION ARCHITECTURE ---
st.header("Application Architecture")
st.markdown("""
The final application uses a professional, two-stage architecture that separates the slow, intensive model training from the fast, lightweight web application. This is a standard industry best practice for deploying machine learning systems.

**1. Offline Training Phase:**
A separate Python script (run in a Jupyter Notebook) acts as the "Model Trainer." This script performs the heavy lifting:
- Connects to the curated SQLite database.
- Prepares the entire dataset, creating user and movie indexes.
- Builds and trains the complex TensorFlow/Keras Deep Learning model for the optimal number of epochs.
- Saves the final, trained "AI brain" as a `.keras` file and the necessary data mappings as `.json` files.

**2. Online Inference Phase (The Streamlit App):**
The Streamlit application itself is the "inference" engine. It's designed to be fast and responsive:
- On startup, it simply **loads the pre-trained `.keras` model** and the `.json` mapping files from disk.
- It **does not** re-train the model, making the app load in seconds, not minutes.
- When a user requests recommendations, it uses the loaded model to perform rapid predictions (inference).
- New user ratings are written live to the SQLite database, ready to be included in the *next* offline training cycle.
""")

st.divider()

# --- DATA WAREHOUSING & MINING (DWM) CONCEPTS ---
st.header("Data Warehousing & Mining (DWM) Concepts Implemented")

st.subheader("Data Warehousing & ETL (Extract, Transform, Load)")
st.markdown("""
- **Data Integration:** Data was sourced from multiple disparate files (MovieLens `ratings.csv` & `movies.csv`, Kaggle's `movies_metadata.csv`). The critical challenge of inconsistent data was solved by using a `links.csv` file to perform a robust **ID-based merge**, joining the datasets on `tmdbId` instead of fragile movie titles.
- **Data Cleaning & Curation:** The project involved several advanced cleaning steps:
  - **Live URL Validation:** A custom script was built to programmatically check thousands of poster URLs from the static dataset, filtering out dead links to ensure UI quality.
  - **Database Curation:** An admin-facing tool was built to run `DELETE` commands on the database, allowing for manual removal of inappropriate or unwanted content.
  - **Data Consistency:** Final loading logic includes an **inner join** to guarantee that every rating in the system corresponds to a movie for which we have complete details, preventing data integrity errors.
- **Database Management:** The system was migrated from a collection of flat `.csv` files to a centralized **SQLite database** (`movies.db`). This acts as a mini-Data Warehouse, providing a single source of truth, ensuring data integrity, and allowing for transactional updates (like adding new ratings) without file corruption.
""")

st.subheader("Data Mining Models & Techniques")
st.markdown("""
- **Collaborative Filtering (Deep Learning):** The main AI model is a **Neural Collaborative Filtering (NCF)** network. It utilizes **Embedding Layers** to learn dense, latent feature vectors for each user and movie. These "embeddings" represent a sophisticated understanding of taste and allow the model to make nuanced, non-linear predictions beyond simple popularity.

- **Content-Based Filtering:** The "Movie Explorer" page uses a classic Scikit-learn pipeline. It applies a **TF-IDF Vectorizer** on movie genres to create a numerical representation of each movie's content, then uses **Cosine Similarity** to find and recommend other movies that are mathematically similar.

- **Explainable AI (XAI):** The "Why was this recommended?" feature provides transparency. It uses **Cosine Similarity** on the learned **embeddings** from the main AI model to find the movie from a user's own high-rating history that is most conceptually similar to the recommended movie.

- **Cold Start Problem Solution:** The system addresses new users in two ways:
  1. The "New User Recommender" page uses a simple but effective **genre-matching** algorithm.
  2. The "Home" page detects users with no rating history and serves them a list of globally popular movies instead of personalized AI recommendations.

- **Model Evaluation & Tuning:** The optimal number of training cycles (**10 epochs**) was not guessed. It was determined experimentally by training the model for 50 epochs and plotting the **training vs. validation loss**. The "sweet spot" was identified at the point where the validation loss was at its minimum, just before the model began to **overfit**. This demonstrates a rigorous, data-driven approach to model tuning.
""")

st.divider()

# --- KEY FEATURES ---
st.header("Key Application Features")
st.markdown("""
- **Full User Authentication:** A complete, secure login, registration, and logout system using `streamlit-authenticator`, with passwords hashed using `bcrypt`.
- **Role-Based Access Control (RBAC):** The system distinguishes between `'admin'` and `'user'` roles, with a dedicated "Admin Dashboard" page visible only to admins.
- **Dynamic, Personalized Homepage:** A Netflix-style UI with multiple carousels for AI-powered recommendations and globally popular movies.
- **Live Rating System:** Users can search for movies and submit new ratings, which are saved permanently to the SQLite database.
- **Interactive Personal Analytics:** A dedicated "Analytics" page that provides logged-in users with real-time visualizations (KPIs, Pie Charts, Histograms) of their own rating history.
- **Comprehensive Browse Tools:** Two separate discovery pages—"Browse All Movies" with A-Z pagination and "Browse by Genre" with multi-select filtering—allow for deep exploration of the catalog.
""")