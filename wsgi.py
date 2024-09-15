import sys
import os
from app import app  # Import the Flask application from app.py

# Optional: Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Set the WSGI application callable to be used by the server
application = app
