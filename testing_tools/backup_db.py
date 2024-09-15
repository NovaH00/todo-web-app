import sqlite3


connection = sqlite3.connect("data/database.db")
            
# Create a new connection to the backup database
with sqlite3.connect("data/backup_database.db") as backup_connection:
    # Perform the backup
    connection.backup(backup_connection)
    print("Database backup completed successfully.")

# Close the connection to the original database
connection.close()