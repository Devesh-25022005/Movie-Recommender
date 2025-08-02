import streamlit as st
import pickle
import pandas as pd
import requests
import urllib.parse
import random
from quiz import questions
import sqlite3
import hashlib
from chatbot_groq import run_chatbot
from watchlist import create_watchlist_table, add_to_watchlist, get_user_watchlist, remove_from_watchlist

if "email" not in st.session_state:
    st.session_state.email = None

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


    # ----- Database functions -----

def create_usertable():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            name TEXT,
            email TEXT PRIMARY KEY,
            password TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_user(name, email, password):
    try:
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)', (name, email, password))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def verify_user(email, password):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password))
    user = cursor.fetchone()
    conn.close()
    return user

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_reviews_table():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
   # cursor.execute("DROP TABLE IF EXISTS reviews")
    cursor.execute('''CREATE TABLE IF NOT EXISTS reviews (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name text,
                        movie_title TEXT,
                        review TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )''')
    conn.commit()
    conn.close()

def add_review(name, movie_title, review):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO reviews (name, movie_title, review) VALUES (?, ?, ?)', (name, movie_title, review))
    conn.commit()
    conn.close()

def get_reviews(movie_title):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name, review, timestamp FROM reviews WHERE movie_title = ? ORDER BY timestamp DESC', (movie_title,))
    reviews = cursor.fetchall()
    conn.close()
    return reviews



# ----- Main UI -----
create_reviews_table()
create_usertable()
create_watchlist_table()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center;'>🎬 Welcome to <span style='color:red;'>MovieFlix</span></h2>", unsafe_allow_html=True)
    st.write("---")

    # Create 3 columns to center the form
    left, center, right = st.columns([1, 2, 1])

    with center:
        auth_choice = st.radio("Choose an option:", ["Login", "Sign Up"])

        if auth_choice == "Login":
            email = st.text_input("📧 Email", key="login_email")
            password = st.text_input("🔑 Password", type="password", key="login_pass")

            if st.button("Login"):
                if email and password:
                    user = verify_user(email, hash_password(password))
                    if user:
                        st.success(f"Welcome back, {user[0]} 👋")
                        st.session_state.logged_in = True
                        st.session_state.name = user[0]
                        st.session_state.email = user[1]
                        st.rerun()
                    else:
                        st.error("❌ Incorrect email or password.")
                        st.info("💡 Tip: If you're new here, please sign up.")
                else:
                    st.warning("⚠️ Please fill in both fields.")

        elif auth_choice == "Sign Up":
            name = st.text_input("👤 Full Name", key="signup_name")
            email = st.text_input("📧 Email", key="signup_email")
            password = st.text_input("🔐 Password", type="password", key="signup_pass")

            if st.button("Create Account"):
                if name and email and password:
                    if add_user(name, email, hash_password(password)):
                        st.success("✅ Account created successfully! You can now log in.")
                    else:
                        st.error("🚫 An account already exists with this email.")
                else:
                    st.warning("⚠️ Please fill in all the fields.")

    st.stop()



# Load Data
movies_dict = pickle.load(open('movie_dict.pkl', 'rb'))
movies = pd.DataFrame(movies_dict)
similarity = pickle.load(open('similarity.pkl', 'rb'))

# OMDb API
OMDB_API_KEY = '5b334106'  # Replace with your actual OMDb key

# Emotion to Genre Mapping
emotion_genre_map = {
    "Happy": ["Comedy", "Adventure"],
    "Sad": ["Drama", "Romance"],
    "Excited": ["Action", "Thriller"],
    "Romantic": ["Romance"],
    "Bored": ["Mystery", "Sci-Fi", "Fantasy"],
    "Thrilled": ["Horror", "Thriller"]
}

# Get Poster, Plot, Genre, Rating, Year
def fetch_movie_details(title):
    title_encoded = urllib.parse.quote(title)
    url = f'https://www.omdbapi.com/?t={title_encoded}&apikey={OMDB_API_KEY}'
    response = requests.get(url)
    data = response.json()

    poster = data.get('Poster', "https://via.placeholder.com/300x450?text=No+Poster+Found")
    plot = data.get('Plot', 'No description available.')
    genre = data.get('Genre', 'N/A')
    rating = data.get('imdbRating', 'N/A')
    year = data.get('Year', 'N/A')

    return poster, plot, genre, rating, year

def get_trailer_link(title):
    query = urllib.parse.quote(title + " trailer")
    return f"https://www.youtube.com/results?search_query={query}"

# Recommend similar movies
def recommend(movie):
    index = movies[movies['title'] == movie].index[0]
    distances = similarity[index]
    top_indices = sorted(enumerate(distances), key=lambda x: x[1], reverse=True)[1:6]
    return [movies.iloc[i[0]].title for i in top_indices]

# Recommend based on emotion
def get_movies_by_emotion(mood, count=5):
    matched_movies = []
    target_genres = emotion_genre_map.get(mood, [])

    for title in movies['title'].sample(frac=1):  # shuffle
        _, _, genre, _, _ = fetch_movie_details(title)
        if any(g.strip() in target_genres for g in genre.split(',')):
            matched_movies.append(title)
        if len(matched_movies) == count:
            break

    return matched_movies

# Streamlit App
st.set_page_config(page_title="Movie Recommender", layout="wide")
st.markdown("<h2 style='text-align: center;'>🎬 Welcome to <span style='color:red;'>MovieFlix</span></h2>", unsafe_allow_html=True)


# Tabs 
tab1, tab2 ,tab3, tab4= st.tabs(["🎞️ Movie-based Recommendation", "🎭 Emotion-based Recommendation","🎯 Movie Quiz","📝 Review"])

# --- Movie-Based Recommendation ---
with tab1:
     st.markdown("<h2>Choose a  <span style='color:red;'>Movie</span> you Like?</h2>", unsafe_allow_html=True)

     selected_movie = st.selectbox('Select Movie:', movies['title'].values)

     if st.button('Recommend Similar Movies'):
         recommended = recommend(selected_movie)
         st.subheader("🎯 Top Recommendations")

         cols = st.columns(5)

         for i, title in enumerate(recommended):
           poster, plot, genre, rating , year = fetch_movie_details(title)
           with cols[i]:
            st.image(poster, use_container_width=True)
            st.markdown(f"**{title}({year})**")

            try:
             rating_float = float(rating)
             st.markdown(f"**IMDb:** {rating} ⭐")
            except:
             st.markdown(f"**IMDb:** {rating}")

            genre_tags = ', '.join([f'`{g.strip()}`' for g in genre.split(',')])
            st.markdown(f"**Genres:** {genre_tags}")
            st.caption(plot)

            trailer_link = get_trailer_link(title)
            st.markdown(f"[▶ Watch Trailer]({trailer_link})", unsafe_allow_html=True)
  
# --- Emotion-Based Recommendation ---
with tab2:
    st.markdown("<h2>How you are <span style='color:red;'>Feeling</span> today ?</h2>", unsafe_allow_html=True)

    mood = st.radio("Select your mood:", list(emotion_genre_map.keys()))
   


    if st.button("🎯 Recommend Based on Mood"):
        emotion_recs = get_movies_by_emotion(mood)
        st.subheader(f"🎥 Movies for when you're feeling *{mood}*")

        cols = st.columns(5)
        for i, title in enumerate(emotion_recs):
            poster, plot,genre,rating,year = fetch_movie_details(title)
            with cols[i]:
                st.image(poster, use_container_width=True)
                st.markdown(f"**{title}({year})**")
                try:
                   rating_float = float(rating)
                   stars = "⭐"
                   st.markdown(f"**IMDb:** {rating} {stars}")
                except:
                   st.markdown(f"**IMDb:** {rating}")

# Show genres as tags
                   genre_tags = ', '.join([f'`{g.strip()}`' for g in genre.split(',')])
                   st.markdown(f"**Genres:** {genre_tags}")
                st.caption(plot)
                trailer_url = get_trailer_link(title)
                st.markdown(f"[▶ Watch Trailer]({trailer_url})", unsafe_allow_html=True)
               
    
    if st.button("🎲 Surprise Me!"):
     surprise_title = random.choice(movies['title'].tolist())
     st.subheader(f"🎉 Surprise Movie: {surprise_title}")
    
     poster, plot, genre, rating, year = fetch_movie_details(surprise_title)

     st.image(poster, width=250)
     st.markdown(f"**🎬 Title:** {surprise_title} ({year})")
     st.markdown(f"**⭐ IMDb Rating:** {rating}")
     st.markdown(f"**🎭 Genre:** {genre}")
     st.markdown(f"**📝 Plot:** {plot}")
     trailer_link = get_trailer_link(surprise_title)
     st.markdown(f"[▶ Watch Trailer]({trailer_link})", unsafe_allow_html=True)

# --- Tab 3: Movie Quiz ---
with tab3:
    st.markdown("<h2>🎯Lets Play <span style='color:red;'>Kaun Banega Movie Champion</span></h2>", unsafe_allow_html=True)

    if st.button("🚪 Exit Quiz"):
        st.info("Thank you for playing the quiz! Come back soon 🎬")
        for key in list(st.session_state.keys()):
            if key.startswith("quiz") or key in ["current_question", "selected"]:
                del st.session_state[key]
        


    # Initialize session state
    if 'quiz_started' not in st.session_state:
        st.session_state.quiz_started = False
        st.session_state.quiz_score = 0
        st.session_state.quiz_index = 0
        st.session_state.asked_questions = []
        st.session_state.current_question = None
        st.session_state.selected = None

    # Start button (only show before quiz starts)
    if not st.session_state.quiz_started:
        if st.button("▶️ Start Quiz"):
            st.session_state.quiz_started = True
            st.rerun()
             # prevent the rest from running if quiz not started

    # Show score
    st.markdown(f"**🧠 Your Score: {st.session_state.quiz_score} / {len(questions)}**")

    # Quiz completion check
    if len(st.session_state.asked_questions) >= len(questions):
        st.success(f"🎉 Quiz Complete! Final Score: {st.session_state.quiz_score}/{len(questions)}")
        if st.button("🔄 Restart Quiz"):
            for key in list(st.session_state.keys()):
                if key.startswith("quiz") or key in ["current_question", "selected"]:
                    del st.session_state[key]
            st.rerun()
        

    # Pick new question if needed
    if not st.session_state.current_question:
        while True:
            question = random.choice(questions)
            if question['question'] not in st.session_state.asked_questions:
                st.session_state.asked_questions.append(question['question'])
                st.session_state.current_question = question
                break

    question = st.session_state.current_question
    st.markdown(f"**Q{st.session_state.quiz_index + 1}. {question['question']}**")

    # Display 4 options
    col1, col2 = st.columns(2)
    with col1:
        if st.button(f"A. {question['options'][0]}", key=f"A_{st.session_state.quiz_index}"):
            st.session_state.selected = question['options'][0]
    with col2:
        if st.button(f"B. {question['options'][1]}", key=f"B_{st.session_state.quiz_index}"):
            st.session_state.selected = question['options'][1]
    col3, col4 = st.columns(2)
    with col3:
        if st.button(f"C. {question['options'][2]}", key=f"C_{st.session_state.quiz_index}"):
            st.session_state.selected = question['options'][2]
    with col4:
        if st.button(f"D. {question['options'][3]}", key=f"D_{st.session_state.quiz_index}"):
            st.session_state.selected = question['options'][3]

    # Process answer if selected
    if st.session_state.selected:
        if st.session_state.selected == question['answer']:
            st.success("✅ Correct!")
            st.session_state.quiz_score += 1
        else:
            st.error(f"❌ Wrong! Correct answer: {question['answer']}")
        
        st.session_state.quiz_index += 1
        st.session_state.current_question = None
        st.session_state.selected = None
        st.rerun()
       
with tab4:
   
    st.markdown("## 📝 Share Your Thoughts")

    if st.session_state.logged_in:
        selected_movie = st.selectbox('🎥 Select a movie to review or read reviews:', movies['title'].values)

        # Submit a review
        st.subheader("✍️ Write Your Review")
        user_review = st.text_area("Share your experience, feelings, or opinion about this movie...")

        if st.button("📤 Submit Review"):
            if user_review.strip():
                add_review(st.session_state["name"], selected_movie, user_review.strip())
                st.success("✅ Your review has been posted!")
                st.rerun()
            else:
                st.warning("⚠️ Review cannot be empty.")

        # Display all reviews
        st.subheader("💬 What others are saying:")
        all_reviews = get_reviews(selected_movie)
        if all_reviews:
            for name, review, time in all_reviews:
                with st.container():
                    st.markdown(f"**📧 {name}** — *{time}*")
                    st.info(f"💬 {review}")
        else:
            st.info("🫥 No reviews yet for this movie. Be the first one to write!")
    else:
        st.warning("🔐 Please log in to access the review section.")

if st.session_state.logged_in:

    # Toggle state if not set
    if "show_chatbot_full" not in st.session_state:
        st.session_state.show_chatbot_full = False

    # Full page chatbot mode
    if st.session_state.show_chatbot_full:
        st.markdown("<h2 style='text-align: center;'>🤖 MovieBot Assistant</h2>", unsafe_allow_html=True)
        
        # Center the chatbot on full page
        col1, col2, col3 = st.columns([1, 4, 1])
        with col2:
            run_chatbot()
            st.markdown(" ")
            if st.button("🔙 Back to MovieFlix"):
                st.session_state.show_chatbot_full = False
                st.rerun()

    else:
        # Default UI — chatbot button on main app
        if st.button("💬 Open MovieBot"):
            st.session_state.show_chatbot_full = True
            st.rerun()



st.markdown("""
---
<div style='text-align: center; font-size: 14px;'>
    © 2025 <b>Devesh Rajput</b>. All rights reserved. <br>
    
</div>
""", unsafe_allow_html=True)
