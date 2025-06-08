"""
This module validates invoice data using:
- Rule-based consistency checks for quantities, totals, and PO numbers
- Natural language summary analysis via Ollama (LLM)

It supports flexible field names using fuzzy matching to handle
varied invoice formats.
"""
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_HOST = os.getenv("OLLAMA_HOST")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")


# Normalized field name variations
FIELD_MAP = {
    "subtotal": [
        "subtotal", "sub_total", "sub total", "amount_before_tax"
    ],
    "vat": ["vat", "tax", "value_added_tax"],
    "total": ["total", "grand_total", "amount_due"],
    "items": ["items", "line_items", "products"],
    "unit_price": [
        "unit_price", "unit cost", "unit", "price_per_unit"
    ],
    "quantity": ["quantity", "qty", "amount"],
    "total_price": [
        "total_price", "line_total", "total amount", "price"
    ],
    "po_numbers": [
        "po_numbers", "po_ids", "purchase_orders", "po_list"
    ]
}


def resolve_field(data: dict, candidates: list):
    """
    Resolves a field value from a dictionary based on candidate aliases.

    Args:
        data (dict): Dictionary containing the data.
        candidates (list): Field name aliases to try.

    Returns:
        any: Value of the resolved field or None if not found.
    """
    for candidate in candidates:
        for key in data:
            if key.lower().strip().replace(" ", "_") == \
               candidate.replace(" ", "_"):
                return data[key]
    return None


def call_ollama_for_consistency_summary(data: dict):
    """
    Sends invoice JSON to Ollama and gets a natural language summary.

    Args:
        data (dict): Parsed invoice data.

    Returns:
        str: LLM-generated summary or error message.
    """
    prompt = f"""
You are a smart invoice checker assistant.

Based on the following invoice JSON, generate a natural language report:
- Detect if there are incorrect totals, mismatched VAT, or subtotal issues
- Mention if any line item calculations are wrong
- Note if there are duplicate PO numbers
- Do not explain what the fields mean, just analyze

INVOICE DATA:
{json.dumps(data, indent=2)}

Reply in professional English in less than 120 words.
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
        return response.json().get("response", "").strip()

    except Exception as e:
        return f"LLM summary generation failed: {e}"


def generate_consistency_report_with_llm(data: dict):
    """
    Generates a hybrid invoice consistency report using both rules and LLM.

    Args:
        data (dict): Parsed invoice JSON.

    Returns:
        dict: A report containing item-level checks, summary verification,
              PO duplicates, and a natural language LLM summary.
    """
    report = {
        "item_checks": [],
        "summary_check": {},
        "po_duplicates": [],
        "llm_summary": None
    }

    items = resolve_field(data, FIELD_MAP["items"]) or []
    subtotal_calc = 0.0

    for idx, item in enumerate(items):
        try:
            quantity = float(
                resolve_field(item, FIELD_MAP["quantity"]) or 0.0
            )
            unit_price = float(
                resolve_field(item, FIELD_MAP["unit_price"]) or 0.0
            )
            total_price = float(
                resolve_field(item, FIELD_MAP["total_price"]) or 0.0
            )

            expected_total = round(quantity * unit_price, 2)
            is_consistent = abs(total_price - expected_total) < 0.01

            report["item_checks"].append({
                "index": idx,
                "product_code": item.get("product_code", f"item_{idx}"),
                "expected_total": expected_total,
                "actual_total": total_price,
                "match": is_consistent
            })

            subtotal_calc += total_price

        except Exception as e:
            report["item_checks"].append({
                "index": idx,
                "product_code": item.get("product_code", f"item_{idx}"),
                "error": f"Invalid item values: {e}"
            })

    summary = resolve_field(data, ["summary", "totals", "amounts"]) or {}

    summary_subtotal = resolve_field(summary, FIELD_MAP["subtotal"]) or 0.0
    summary_vat = resolve_field(summary, FIELD_MAP["vat"]) or 0.0
    summary_total = resolve_field(summary, FIELD_MAP["total"]) or 0.0

    expected_total = round(subtotal_calc + float(summary_vat), 2)
    is_total_consistent = abs(
        expected_total - float(summary_total)
    ) < 0.01

    report["summary_check"] = {
        "calculated_subtotal": round(subtotal_calc, 2),
        "summary_subtotal": summary_subtotal,
        "summary_vat": summary_vat,
        "summary_total": summary_total,
        "expected_total": expected_total,
        "match": is_total_consistent
    }

    po_list = resolve_field(data, FIELD_MAP["po_numbers"]) or []
    report["po_duplicates"] = list(
        set([po for po in po_list if po_list.count(po) > 1])
    )

    report["llm_summary"] = call_ollama_for_consistency_summary(data)

    return report
