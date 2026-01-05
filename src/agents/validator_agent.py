"""
Validator Agent - Business logic validation
Pure rules, no LLM
"""
from typing import Dict, Any, List

from src.agents.base_agent import BaseAgent, AgentType
from src.core.logging import logger
from src.core.config import settings


class ValidatorAgent(BaseAgent):
    """
    Validate invoice data using business rules
    - VAT calculation
    - Arithmetic checks
    - Data completeness
    """
    
    def __init__(self):
        super().__init__("ValidatorAgent", AgentType.VALIDATION)
    
    def process(self, context: Dict[str, Any]) -> tuple[Dict[str, Any], float]:
        """Validate invoice data"""
        
        invoice_data = context.get('invoice_data', {})
        
        errors = []
        warnings = []
        
        # 1. VAT validation
        vat_ok = self._validate_vat(invoice_data, errors, warnings)
        
        # 2. Arithmetic validation
        arith_ok = self._validate_arithmetic(invoice_data, errors, warnings)
        
        # 3. Completeness
        complete_ok = self._validate_completeness(invoice_data, errors, warnings)
        
        # Calculate score
        checks_passed = sum([vat_ok, arith_ok, complete_ok])
        confidence = checks_passed / 3
        
        result = {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'checks': {
                'vat': vat_ok,
                'arithmetic': arith_ok,
                'completeness': complete_ok
            }
        }
        
        logger.info(
            f"Validation: {checks_passed}/3 checks passed, "
            f"{len(errors)} errors, {len(warnings)} warnings"
        )
        
        return result, confidence
    
    def _validate_vat(
        self, 
        data: Dict, 
        errors: List, 
        warnings: List
    ) -> bool:
        """Validate VAT calculation"""
        
        subtotal = data.get('subtotal')
        vat_total = data.get('vat_total')
        vat_rate = data.get('vat_rate', settings.VAT_RATE)
        
        if not subtotal or not vat_total:
            warnings.append("Missing VAT fields")
            return False
        
        expected_vat = subtotal * vat_rate
        diff = abs(vat_total - expected_vat)
        tolerance = subtotal * settings.ARITHMETIC_TOLERANCE
        
        if diff > tolerance:
            errors.append(
                f"VAT mismatch: expected {expected_vat:.2f}, "
                f"got {vat_total:.2f}"
            )
            return False
        
        return True
    
    def _validate_arithmetic(
        self, 
        data: Dict, 
        errors: List, 
        warnings: List
    ) -> bool:
        """Validate item arithmetic"""
        
        items = data.get('items', [])
        if not items:
            return True
        
        all_ok = True
        
        for item in items:
            qty = item.get('quantity')
            price = item.get('unit_price')
            total = item.get('gross_amount')
            
            if not (qty and price and total):
                continue
            
            expected = qty * price
            diff = abs(total - expected)
            
            if diff > expected * settings.ARITHMETIC_TOLERANCE:
                warnings.append(
                    f"Item arithmetic issue: {item.get('description')} "
                    f"({qty} × {price} ≠ {total})"
                )
                all_ok = False
        
        return all_ok
    
    def _validate_completeness(
        self, 
        data: Dict, 
        errors: List, 
        warnings: List
    ) -> bool:
        """Check data completeness"""
        
        required = ['invoice_number', 'invoice_date', 'grand_total']
        missing = [f for f in required if not data.get(f)]
        
        if missing:
            warnings.append(f"Missing required fields: {missing}")
            return False
        
        return True
