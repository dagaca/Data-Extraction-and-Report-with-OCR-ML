"""
Defines all authentication routes in one file with logging and Swagger documentation.
"""
import os
from flask import request, jsonify
from app import app
from common.decorators import require_api_key
from config.log_config import configure_logging, log_request_info, log_response_info
from app.utils.ocr import extract_text_from_pdf
from app.utils.file import allowed_file
from app.utils.ollama_extract import ask_ollama_for_invoice_json
from app.utils.ollama_report import generate_consistency_report_with_llm

# Configure logging
configure_logging(app)
log_request_info(app)
log_response_info(app)

@app.route("/health", methods=["GET"])
def health_check():
    """
    This endpoint performs a health check to verify that the service is running correctly.

    -------
    tags:
      - System
    responses:
      '200':
        description: Service is healthy.
        content:
          application/json:
            schema:
              type: object
              properties:
                healthy:
                  type: string
                  example: Ok
    """
    app.logger.info("✅ Health check endpoint accessed.")
    return jsonify({"healthy": "Ok"}), 200

@app.route("/extract", methods=["POST"])
@require_api_key
def extract_invoice():
    """
    Invoice Extraction Endpoint (LLM + OCR)

    ---
    tags:
      - Invoice Extraction
    parameters:
      - name: x-api-key
        in: header
        required: true
        schema:
          type: string
        description: API key for authentication.

      - name: invoice
        in: formData
        required: true
        type: file
        description: Upload a PDF invoice file.

    responses:
      200:
        description: JSON extracted successfully.
      401:
        description: Unauthorized.
      400:
        description: Invalid file or request.
    """
    file = request.files.get("invoice")
    if not file or not allowed_file(file.filename):
        return jsonify({"error": "Missing or invalid PDF file"}), 400

    path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(path)

    text = extract_text_from_pdf(path)
    extracted_data = ask_ollama_for_invoice_json(text)

    return jsonify({
        "extracted_data": extracted_data,
        "text": text
    })

@app.route("/report", methods=["POST"])
@require_api_key
def report_invoice():
    """
    Generate Consistency Report from Extracted Invoice Data (LLM + OCR)

    ---
    tags:
      - Invoice Consistency Report
    parameters:
      - name: x-api-key
        in: header
        required: true
        schema:
          type: string
        description: API key for authentication.

      - name: invoice
        in: formData
        required: true
        type: file
        description: Upload a PDF invoice file.

    responses:
      200:
        description: Consistency report generated successfully.
        content:
          application/json:
            example:
              consistency_report:
                item_checks:
                  - index: 0
                    product_code: "PRD-123"
                    expected_total: 125.0
                    actual_total: 125.0
                    match: true
                summary_check:
                  calculated_subtotal: 125.0
                  summary_subtotal: 125.0
                  summary_vat: 25.0
                  summary_total: 150.0
                  expected_total: 150.0
                  match: true
                po_duplicates: ["PO-001"]
                llm_summary: "Line items and totals are consistent. One PO number is duplicated."
      401:
        description: Unauthorized - Invalid or missing API key.
      400:
        description: Bad Request - Missing or invalid PDF file.
    """
    file = request.files.get("invoice")
    if not file or not allowed_file(file.filename):
        return jsonify({"error": "Missing or invalid PDF file"}), 400

    path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
    file.save(path)

    # Step 1: Extract raw text from PDF (with fallback OCR if needed)
    text = extract_text_from_pdf(path)

    # Step 2: Ask Ollama LLM to extract structured invoice data
    extracted_data = ask_ollama_for_invoice_json(text)

    # Step 3: Generate rule-based + LLM-assisted consistency report
    report = generate_consistency_report_with_llm(extracted_data)

    return jsonify({
        "consistency_report": report
    })
