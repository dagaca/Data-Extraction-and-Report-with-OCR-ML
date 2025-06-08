# Data-Extraction-and-Report-with-OCR-ML

A modular, production-ready Flask API that ingests PDF invoices, extracts structured data via **pdfplumber** (with OCR fallback), enriches and formats it via an **Ollama LLM**, and generates both rule-based consistency reports and NLP-driven summaries.

---

## 🚀 Features

- **PDF → Text**  
  - Native extraction using `pdfplumber` for digital PDFs  
  - Fallback OCR with Tesseract + Poppler for scanned images  

- **Structured JSON Extraction**  
  - Ollama (Mistral) prompt drives conversion of raw text → JSON  
  - Enforces complete, machine-readable schema (POs, items, summary)  

- **Consistency Reporting**  
  - Rule-based item-level checks (`quantity × unit_price ≈ total_price`)  
  - Summary and VAT validation  
  - Duplicate PO detection  
  - LLM-powered natural-language summary  

- **REST API**  
  - **`POST /extract`** → returns structured invoice JSON  
  - **`POST /report`**  → returns hybrid consistency report + LLM summary  
  - API-Key protection via `x-api-key` header  
  - OpenAPI/Swagger-style docstrings for easy integration  

---

## 📦 Installation

1. **Clone project**  
   ```bash
   git clone https://github.com/your-org/invoice-extraction.git
   cd invoice-extraction
   ```


2. **Create virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate     # macOS/Linux  
   venv\Scripts\activate        # Windows
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Install system tools**

   * **Tesseract-OCR**
     Download & install from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki).
   * **Poppler**
     Windows: [poppler-windows releases](https://github.com/oschwartz10612/poppler-windows/releases).

---

## ⚙️ Configuration

Create a `.env` file in the project root:

```env
FLASK_ENV=development
API_KEY=your_api_key_here
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=mistral
```


* **API\_KEY** protects all endpoints
* **OLLAMA\_HOST** & **OLLAMA\_MODEL** configure your local Ollama server

---

## 🔧 Usage

1. **Start Ollama server**

   ```bash
   ollama serve
   ollama run mistral
   ```

2. **Launch Flask API**

   ```bash
   python run.py
   ```

3. **Test with cURL**

   ```bash
   curl -X POST http://localhost:5000/extract \
     -H "x-api-key: your_api_key_here" \
     -F "invoice=@/path/to/invoice.pdf"
   ```

   ```bash
   curl -X POST http://localhost:5000/report \
     -H "x-api-key: your_api_key_here" \
     -F "invoice=@/path/to/invoice.pdf"
   ```

---

## 🛠️ Endpoints

| Endpoint   | Method | Description                              |
| ---------- | ------ | ---------------------------------------- |
| `/extract` | POST   | Returns structured invoice JSON          |
| `/report`  | POST   | Returns consistency report + LLM summary |

**Headers**

```yaml
x-api-key: your_api_key_here
```

**Body (form-data)**

```yaml
invoice: <your-pdf-file>
```

---

## 📄 Schema Example

```json
{
  "supplier_info": "GLOBAL TECH SOLUTIONS LTD.",
  "po_numbers": ["526365", "360206"],
  "items": [
    {
      "product_code": "PRD-5976",
      "description": "Power Supply",
      "quantity": 39,
      "unit_price": 479.1,
      "total_price": 18684.9
    }
  ],
  "summary": {
    "subtotal": 11420.61,
    "vat": 2284.12,
    "total": 13704.73
  }
}
```

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch
3. Commit your changes
4. Open a Pull Request

---

## 📜 License

[MIT License](LICENSE)
