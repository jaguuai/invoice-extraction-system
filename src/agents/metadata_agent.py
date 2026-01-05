"""
Metadata Agent - Extracts invoice metadata using LLM
Uses API (OpenAI/Anthropic) - non-sensitive data
"""
from typing import Dict, Any
import json
import re

from src.agents.base_agent import BaseAgent, AgentType
from src.core.logging import logger


class MetadataAgent(BaseAgent):
    """
    Extract invoice metadata using LLM
    - Invoice number, date
    - Currency, language
    - Company names (not addresses!)
    """
    
    def __init__(self, llm_client):
        super().__init__("MetadataAgent", AgentType.EXTRACTION)
        self.llm = llm_client
    
    def process(self, context: Dict[str, Any]) -> tuple[Dict[str, Any], float]:
        """Extract metadata using LLM"""
        
        ocr_text = context.get('ocr_text', '')
        
        # Build prompt
        prompt = self._build_prompt(ocr_text)
        
        # Call LLM (API - non-sensitive)
        response = self.llm.generate(
            prompt=prompt,
            llm_type='api',  # API OK for metadata
            temperature=0.0,  # Deterministic
            max_tokens=300
        )
        
        if not response:
            logger.warning("LLM returned empty response")
            return {}, 0.5
        
        # Parse JSON response
        data = self._parse_response(response)
        
        # Calculate confidence
        confidence = self._calculate_confidence(data)
        
        return data, confidence
    
    def _build_prompt(self, ocr_text: str) -> str:
        """Build extraction prompt"""
        
        return f"""Extract invoice metadata from this OCR text.

OCR TEXT:
{ocr_text[:1000]}

Extract these fields:
- invoice_number: Invoice/document number
- invoice_date: Date (format: YYYY-MM-DD)
- currency: TRY, USD, EUR, etc
- seller_name: Seller company name only (no address!)
- buyer_name: Buyer company name only (no address!)

Return ONLY valid JSON:
{{
  "invoice_number": "...",
  "invoice_date": "YYYY-MM-DD",
  "currency": "TRY",
  "seller_name": "...",
  "buyer_name": "..."
}}

Rules:
- Use null for missing fields
- Date must be YYYY-MM-DD format
- Names only, NO addresses (privacy!)
"""
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM JSON response"""
        
        try:
            # Clean markdown
            cleaned = response.strip()
            cleaned = re.sub(r'```json\s*', '', cleaned)
            cleaned = re.sub(r'```\s*$', '', cleaned)
            
            # Parse JSON
            data = json.loads(cleaned)
            
            logger.debug(f"Parsed metadata: {data}")
            return data
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            logger.debug(f"Response was: {response}")
            return {}
    
    def _calculate_confidence(self, data: Dict) -> float:
        """Calculate extraction confidence"""
        
        required_fields = ['invoice_number', 'invoice_date', 'currency']
        found = sum(1 for f in required_fields if data.get(f))
        
        return found / len(required_fields)
