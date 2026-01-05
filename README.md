# Invoice Extraction System – Multi-Agent AI Architecture

AI-powered invoice extraction system designed with a **modular multi-agent orchestration architecture**.
The system combines OCR, rule-based validation, and LLM-powered reasoning to extract, validate, and enrich invoice data from PDFs and images.

---

## 🚀 Key Features

- Unified API endpoint for PDF & image processing
- Intelligent routing (text PDF vs scanned PDF vs image)
- PaddleOCR with image preprocessing
- Rule-based arithmetic and structural validation
- LLM-powered semantic parsing (Ollama / OpenAI)
- Privacy-aware design (KVKK / GDPR ready)
- Modular multi-agent architecture

---

## 🧠 System Architecture

```
┌──────────────────────────────────────────────────┐
│          MULTI-AGENT ORCHESTRATOR                │
└──────────────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼

┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  EXTRACTION │  │ VALIDATION  │  │  ENRICHMENT │
│   AGENTS    │  │   AGENTS    │  │   AGENTS    │
└─────────────┘  └─────────────┘  └─────────────┘
        │             │             │
    ┌───┴───┐     ┌───┴───┐     ┌───┴───┐
    ▼       ▼     ▼       ▼     ▼       ▼

METADATA  TABLE  ARITHMETIC PRIVACY  SEMANTIC
AGENT    AGENT    AGENT    AGENT     AGENT
(API)    (RULE)   (RULE)   (OLLAMA)  (API)
```

---

## 🎯 Multi-Agent Orchestrator

The orchestrator coordinates all agents and allows partial success instead of total failure.

Responsibilities:
- Controls agent execution order
- Shares context between agents
- Handles fallback logic
- Produces unified structured output

---

## 🔍 Extraction Agents

### Metadata Agent
Extracts invoice-level metadata using heuristics and rules.

### Table Agent
Extracts line items using OCR tokens and spatial layout.

---

## ✅ Validation Agents

### Arithmetic Agent
Validates totals, VAT, and line consistency with tolerance.

### Privacy Agent
Detects sensitive personal data for KVKK / GDPR compliance.

---

## ✨ Enrichment Agents

### Semantic Agent
Normalizes item descriptions and improves downstream usability.

---

## 🌐 API Endpoint

```
POST /api/v1/process
```

Input:
- PDF / Image / TXT

Output:
```json
{
  "success": true,
  "file_name": "invoice.pdf",
  "file_type": "image",
  "processing_method": "ocr",
  "text": "...",
  "char_count": 1200,
  "word_count": 210,
  "ocr_confidence": 0.92,
  "page_count": 1,
  "items": []
}
```

---

## 🧪 Development Status

- OCR pipeline: ✅ Stable
- Rule-based validation: ✅ Stable
- LLM integration: ⚠️ Environment dependent (CPU Ollama timeout risk)

---

## 🏁 Conclusion

This project demonstrates real-world AI system design with hybrid rule-based and LLM-driven agents.
