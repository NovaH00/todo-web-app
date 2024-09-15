import sqlite3
import json

# Connect to SQLite database (creates the file if it doesn't exist)
conn = sqlite3.connect(r'data\backup_database.db')
cursor = conn.cursor()

# Create the table with specified columns
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    tasks TEXT -- Storing JSON as TEXT
);
''')

# Commit the changes and close the connection
conn.commit()
conn.close()
