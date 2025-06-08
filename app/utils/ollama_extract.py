"""
This module contains helper functions to extract structured invoice data
from raw PDF text using the Ollama LLM API. It handles prompt creation,
response cleaning, and safe JSON extraction from model output.
"""
import requests  # For sending HTTP requests to the Ollama API
import json      # For parsing JSON responses
import re        # For cleaning raw LLM response using regex
import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_HOST = os.getenv("OLLAMA_HOST")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")


def clean_ollama_response(raw):
    """
    Cleans the raw response string returned by the Ollama model.

    Removes:
    - <think>...</think> tags
    - ```json ... ``` code blocks
    - // style comments
    - Leading/trailing whitespace

    Args:
        raw (str): The raw response text from the LLM

    Returns:
        str: Cleaned version of the LLM response
    """
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL)
    raw = re.sub(r"```json.*?```", "", raw, flags=re.DOTALL)
    raw = re.sub(r"//.*", "", raw)
    return raw.strip()


def ask_ollama_for_invoice_json(text):
    """
    Sends extracted invoice text to Ollama LLM to receive a valid JSON.

    Prompts the model to generate structured output with:
    - supplier_info
    - po_numbers
    - items (with product_code, quantity, price, etc.)
    - summary (subtotal, vat, total)

    Args:
        text (str): Raw invoice text extracted from PDF

    Returns:
        dict: Parsed structured JSON if successful, or raw_response
    """
    prompt = f"""
You are a highly accurate invoice parser.

Extract the following invoice text into a fully structured and complete 
JSON object with the following schema:

{{
  "supplier_info": "...",
  "po_numbers": ["..."],
  "items": [
    {{
      "product_code": "...",
      "description": "...",
      "quantity": ...,
      "unit_price": ...,
      "total_price": ...
    }}
  ],
  "summary": {{
    "subtotal": ...,
    "vat": ...,
    "total": ...
  }}
}}

⚠️ VERY IMPORTANT:
- DO NOT skip, shorten, or summarize any line items.
- DO NOT use "...", "and more", or "truncated".
- INCLUDE EVERY product/item as seen in the invoice text.
- DO NOT include markdown formatting like ```json
- DO NOT write explanations, headers, or natural language

Return ONLY the final JSON, strictly valid and machine-readable.

INVOICE TEXT:
{text}

### JSON:
"""

    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            }
        )

        if response.status_code != 200:
            return {"raw_response": response.text}

        resp_json = response.json()
        raw = resp_json.get("response", "")

        if not raw.strip():
            return {"raw_response": ""}

        raw_clean = clean_ollama_response(raw)

        # Extract JSON block between first '{' and last '}'
        start = raw_clean.find("{")
        end = raw_clean.rfind("}") + 1

        if start == -1 or end == 0:
            return {"raw_response": raw_clean}

        json_text = raw_clean[start:end]

        # Fix edge cases like: "payment_terms": {"net 30"} ⇒ "payment_terms": "net 30"
        json_text = re.sub(
            r'"payment_terms"\s*:\s*\{\s*"([^"]+)"\s*\}',
            r'"payment_terms": "\1"',
            json_text
        )

        # Remove trailing commas before ] or }
        json_text = re.sub(r",\s*(\]|\})", r"\1", json_text)

        return json.loads(json_text)

    except Exception:
        return {"raw_response": raw_clean}
