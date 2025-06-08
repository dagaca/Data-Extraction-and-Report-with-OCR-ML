"""
Extracts text content from PDF files using two-step strategy:
- First attempts native text extraction via pdfplumber (for digital PDFs)
- Falls back to OCR using Tesseract + pdf2image for scanned documents
"""
import pdfplumber
import pytesseract
from pdf2image import convert_from_path

# Path to the Tesseract executable (adjust if needed)
pytesseract.pytesseract.tesseract_cmd = (
    r"C:/Program Files/Tesseract-OCR/tesseract.exe"
)

# Path to the Poppler bin directory (required by pdf2image)
POPPLER_PATH = r"C:/Release-24.08.0-0/poppler-24.08.0/Library/bin"


def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a given PDF file.

    Tries text extraction with pdfplumber first. If no meaningful content is
    found (e.g. scanned image), it falls back to OCR using Tesseract.

    Args:
        pdf_path (str): Path to the PDF file on disk.

    Returns:
        str: Extracted text from the PDF, or error message on OCR failure.
    """
    text = ""

    # Try extracting text using pdfplumber
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception:
        text = ""

    # If result is weak or empty, try OCR fallback
    if not text.strip() or len(text.replace("\n", "").strip()) < 20:
        print("Falling back to OCR via Tesseract...")
        try:
            images = convert_from_path(
                pdf_path, poppler_path=POPPLER_PATH
            )
            text = ""
            for img in images:
                text += pytesseract.image_to_string(img) + "\n"
        except Exception as e:
            return f"OCR failed: {str(e)}"

    return text
