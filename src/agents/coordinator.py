"""
Agent Coordinator - Orchestrates multi-agent pipeline
"""
from typing import Dict, Any
from dataclasses import dataclass

from src.agents.metadata_agent import MetadataAgent
from src.agents.privacy_agent import PrivacyAgent
from src.agents.validator_agent import ValidatorAgent
from src.models.invoice import InvoiceData, PartyInfo, InvoiceItem
from src.services.llm_client import get_llm_client
from src.core.logging import logger


@dataclass
class CoordinatorResult:
    """Final orchestration result"""
    invoice: InvoiceData
    metadata: Dict[str, Any]
    validation: Dict[str, Any]
    agent_results: Dict[str, Any]


class AgentCoordinator:
    """
    Multi-agent coordinator
    Orchestrates extraction → validation → enrichment
    """
    
    def __init__(self):
        logger.info("🎭 Initializing Agent Coordinator...")
        
        # Get LLM client
        self.llm = get_llm_client()
        
        # Initialize agents
        self.metadata_agent = MetadataAgent(self.llm)
        self.privacy_agent = PrivacyAgent(self.llm)
        self.validator_agent = ValidatorAgent()
        
        logger.info("✅ All agents initialized")
    
    def coordinate(
        self, 
        ocr_text: str, 
        table_items: list
    ) -> CoordinatorResult:
        """
        Coordinate multi-agent extraction
        
        Pipeline:
        1. Metadata Agent (API LLM)
        2. Privacy Agent (Ollama)
        3. Validator Agent (Rules)
        4. Assembly
        """
        
        logger.info("🎬 Starting agent coordination...")
        
        # Build context
        context = {
            'ocr_text': ocr_text,
            'table_items': table_items
        }
        
        # STEP 1: Metadata extraction (API)
        metadata_result = self.metadata_agent.execute(context)
        metadata = metadata_result.data
        
        # STEP 2: Privacy extraction (Ollama)
        privacy_result = self.privacy_agent.execute(context)
        privacy = privacy_result.data
        
        # STEP 3: Assemble invoice
        invoice = self._assemble_invoice(metadata, privacy, table_items)
        
        # STEP 4: Validation
        context['invoice_data'] = invoice.dict()
        validation_result = self.validator_agent.execute(context)
        validation = validation_result.data
        
        logger.info("🎉 Agent coordination complete")
        
        return CoordinatorResult(
            invoice=invoice,
            metadata=metadata,
            validation=validation,
            agent_results={
                'metadata': metadata_result.dict() if hasattr(metadata_result, 'dict') else metadata_result.__dict__,
                'privacy': privacy_result.dict() if hasattr(privacy_result, 'dict') else privacy_result.__dict__,
                'validation': validation_result.dict() if hasattr(validation_result, 'dict') else validation_result.__dict__
            }
        )
    
    def _assemble_invoice(
        self, 
        metadata: Dict, 
        privacy: Dict, 
        table_items: list
    ) -> InvoiceData:
        """Assemble final invoice"""
        
        # Build seller
        seller = PartyInfo(
            name=metadata.get('seller_name'),
            address=privacy.get('seller_address'),
            tax_id=privacy.get('seller_tax_id'),
            phone=privacy.get('seller_phone'),
            email=privacy.get('seller_email')
        )
        
        # Build buyer
        buyer = PartyInfo(
            name=metadata.get('buyer_name'),
            address=privacy.get('buyer_address'),
            tax_id=privacy.get('buyer_tax_id'),
            phone=privacy.get('buyer_phone'),
            email=privacy.get('buyer_email')
        )
        
        # Convert items
        items = [
            InvoiceItem(
                description=item.description,
                quantity=item.quantity,
                unit_price=item.unit_price,
                gross_amount=item.total_price,
                confidence=item.confidence
            )
            for item in table_items
        ]
        
        # Calculate totals from items
        subtotal = sum(item.total_price for item in table_items)
        vat_rate = 0.18
        vat_total = subtotal * vat_rate
        grand_total = subtotal + vat_total
        
        # Build invoice
        invoice = InvoiceData(
            invoice_number=metadata.get('invoice_number'),
            invoice_date=metadata.get('invoice_date'),
            currency=metadata.get('currency', 'TRY'),
            seller=seller,
            buyer=buyer,
            items=items,
            subtotal=subtotal,
            vat_rate=vat_rate,
            vat_total=vat_total,
            grand_total=grand_total
        )
        
        return invoice


_coordinator = None

def get_coordinator() -> AgentCoordinator:
    global _coordinator
    if _coordinator is None:
        _coordinator = AgentCoordinator()
    return _coordinator
