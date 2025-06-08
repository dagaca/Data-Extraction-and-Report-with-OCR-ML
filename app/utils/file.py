"""
Utility for validating uploaded files. Ensures only PDF files are accepted
based on their filename extension.
"""
def allowed_file(filename):
    """
    Checks if the uploaded file is a valid PDF based on its extension.

    Args:
        filename (str): The name of the uploaded file.

    Returns:
        bool: True if the file is a PDF, otherwise False.
    """
    return filename.lower().endswith(".pdf")
