from src.services.llm_client import get_llm_client

from src.core.logging import logger

class InvoiceOrchestrator:

    def run(self, ocr_text: str, ocr_tokens=None):
        logger.info("🤖 Calling LLM for invoice parsing")

        llm = get_llm_client()

        prompt = f"""
You are an invoice parser.

Extract invoice line items from the text below.

Return ONLY valid JSON in this format:
{{
  "items": [
    {{
      "description": "string",
      "quantity": number,
      "unit_price": number,
      "total_price": number,
      "confidence": number
    }}
  ]
}}

Invoice Text:
{ocr_text}
"""

        response = llm.complete(prompt)

        logger.info("🤖 LLM response received")

        try:
            return response
        except Exception as e:
            logger.error(f"LLM parse failed: {e}")
            return {"items": []}
