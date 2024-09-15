import sqlite3
import json

# Connect to SQLite database (creates the file if it doesn't exist)
conn = sqlite3.connect(r'data\database.db')
cursor = conn.cursor()

cursor.execute("DELETE FROM users")

# Commit the changes and close the connection
conn.commit()
conn.close()
