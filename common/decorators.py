"""
This module provides an API key authentication decorator for Flask endpoints.
The API key is retrieved from the environment variable "COMMON_API_KEY" and is 
used to secure routes by comparing it against the key provided in the 
"x-api-key" request header.
"""
import os
from functools import wraps
from flask import request, jsonify

# Retrieve API key from the environment variable
COMMON_API_KEY = os.getenv("COMMON_API_KEY")

def require_api_key(f):
    """
    Decorator to enforce API key authentication on Flask routes.

    This decorator checks if the incoming request contains the expected API key
    in the 'x-api-key' header. The API key is compared with the one obtained from
    the environment variable "COMMON_API_KEY". If the API key is missing or invalid,
    the function returns a JSON response with an "Unauthorized access" error and
    a 401 status code.

    Args:
        f (callable): The Flask view function to decorate.

    Returns:
        callable: The decorated function which enforces API key authentication.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # API key is usually passed in the request header
        api_key = request.headers.get('x-api-key')
        if not api_key or api_key != COMMON_API_KEY:
            return jsonify({"error": "Unauthorized access"}), 401
        return f(*args, **kwargs)
    return decorated
