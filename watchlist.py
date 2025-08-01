import sqlite3

def create_watchlist_table():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS watchlist(user_email TEXT, movie_title TEXT)')
    conn.commit()
    conn.close()

def add_to_watchlist(user_email, movie_title):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT * FROM watchlist WHERE user_email = ? AND movie_title = ?", (user_email, movie_title))
    if not c.fetchone():
        c.execute("INSERT INTO watchlist (user_email, movie_title) VALUES (?, ?)", (user_email, movie_title))
    conn.commit()
    conn.close()

def get_user_watchlist(user_email):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT movie_title FROM watchlist WHERE user_email = ?", (user_email,))
    data = c.fetchall()
    conn.close()
    return [i[0] for i in data]

def remove_from_watchlist(user_email, movie_title):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("DELETE FROM watchlist WHERE user_email = ? AND movie_title = ?", (user_email, movie_title))
    conn.commit()
    conn.close()
