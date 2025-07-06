import streamlit as st
import pickle
import pandas as pd
import requests
import urllib.parse

# ✅ Fetch poster and plot from OMDb
def fetch_poster_and_plot(title):
    api_key = '5b334106'  # Replace with your OMDb API key
    title_encoded = urllib.parse.quote(title)
    url = f'https://www.omdbapi.com/?t={title_encoded}&apikey={api_key}'
    response = requests.get(url)
    data = response.json()
    
    # Defaults
    poster = "https://via.placeholder.com/300x450?text=No+Poster+Found"
    plot = "No description available."

    if data.get('Response') == 'True':
        if data.get('Poster') != 'N/A':
            poster = data['Poster']
        if data.get('Plot') and data['Plot'] != 'N/A':
            plot = data['Plot']
    
    return poster, plot

# ✅ Recommend similar movies
def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    recommended_movies = []
    recommended_posters = []
    recommended_plots = []

    for i in movies_list:
        title = movies.iloc[i[0]].title
        poster, plot = fetch_poster_and_plot(title)
        recommended_movies.append(title)
        recommended_posters.append(poster)
        recommended_plots.append(plot)
    
    return recommended_movies, recommended_posters, recommended_plots

# Load data
movies_dict = pickle.load(open('movie_dict.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)
similarity = pickle.load(open('similarity.pkl', 'rb'))

# ✅ Streamlit UI
st.title('🎬 Movie Recommender System')
selected_movie_name = st.selectbox('Choose a movie you like:', movies['title'].values)

if st.button('Recommend'):
    names, posters, plots = recommend(selected_movie_name)

    cols = st.columns(5)
    for i in range(5):
        with cols[i]:
            st.image(posters[i])
            st.markdown(f"**{names[i]}**")
            st.caption(plots[i])  # ⬅️ Movie description
