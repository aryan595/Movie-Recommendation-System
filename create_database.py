# create_database.py

import pandas as pd
import sqlite3

print("Starting database creation...")

# Create a connection to a new database file
# This will create 'movies.db' in your folder
con = sqlite3.connect('movies.db')

# --- Load your clean CSVs ---
try:
    movies = pd.read_csv('movies_clean_final.csv')
    ratings = pd.read_csv('ratings_clean_final.csv')
except FileNotFoundError:
    print("ERROR: Make sure 'movies_clean_final.csv' and 'ratings_clean_final.csv' are in this folder!")
    exit()

# --- Save these dataframes as tables in the database ---
movies.to_sql('movies', con, if_exists='replace', index=False)
ratings.to_sql('ratings', con, if_exists='replace', index=False)

# --- Close the connection ---
con.close()

print("SUCCESS: Your 'movies.db' file has been created.")
print("It contains a 'movies' table and a 'ratings' table.")
print("You can now delete this script. You only need to run it once.")