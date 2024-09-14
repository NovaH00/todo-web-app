import sys
import os
from app import app  # Import the Flask application from app.py

# Optional: Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Load tasks at the start of the application
from app import load_tasks
load_tasks()

# Set the WSGI application callable to be used by the server
application = app
