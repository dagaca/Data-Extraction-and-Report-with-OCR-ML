"""
This module initializes the Flask application and sets up Swagger for API documentation.
"""
from flask import Flask
from flasgger import Swagger
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Create Flask application for API service - POSTMAN
app = Flask(__name__)

# Setting up Upload Folder configuration
app.config["UPLOAD_FOLDER"] = "uploads"

# Setting up Swagger configuration for API documentation.
app.config['SWAGGER'] = {
    'title': 'Data Extraction and Report with OCR & ML API',
    'description': 'This is the Data Extraction and Report with OCR & ML API documentation.'
}
swagger = Swagger(app)

# Import and use the routes module
from app import routes
