import sqlite3
import json

# Connect to the SQLite database
conn = sqlite3.connect('data/database.db')
cursor = conn.cursor()

def add_user(username, password, data=[]):
    data_json = json.dumps(data)  # Convert Python object to JSON string
    
    # Check if user already exists
    cursor.execute('''
    SELECT COUNT(*) FROM users WHERE username = ?
    ''', (username,))
    
    count = cursor.fetchone()[0]
    
    if count > 0:
        raise Exception("User already exists!")
    else:
        # Insert new user
        cursor.execute('''
        INSERT INTO users (username, password, data) VALUES (?, ?, ?)
        ''', (username, password, data_json))
        conn.commit()  # Commit the transaction

def remove_user(username):
    cursor.execute('''
    DELETE FROM users WHERE username = ?
    ''', (username,))
    conn.commit()  # Commit the transaction

def authentication(username, password):
    cursor.execute('''
    SELECT password FROM users WHERE username = ?
    ''', (username,))
    
    row = cursor.fetchone()
    
    if row and password == row[0]:
        return True
    else:
        return False

def update_data(username, new_data):
    new_data_json = json.dumps(new_data)  # Convert Python object to JSON string
    
    cursor.execute('''
    UPDATE users SET data = ? WHERE username = ?
    ''', (new_data_json, username))
    conn.commit()  # Commit the transaction

