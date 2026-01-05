"""
Base Agent - Abstract class for all agents
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass
from enum import Enum
import time

from src.core.logging import logger


class AgentType(str, Enum):
    """Agent types for tracking"""
    EXTRACTION = "extraction"
    VALIDATION = "validation"
    ENRICHMENT = "enrichment"


@dataclass
class AgentResult:
    """Standard agent result format"""
    success: bool
    data: Dict[str, Any]
    confidence: float
    errors: list
    execution_time: float
    agent_name: str


class BaseAgent(ABC):
    """
    Abstract base agent
    All agents inherit from this
    """
    
    def __init__(self, name: str, agent_type: AgentType):
        self.name = name
        self.agent_type = agent_type
        logger.info(f"🤖 Agent initialized: {name} ({agent_type})")
    
    def execute(self, context: Dict[str, Any]) -> AgentResult:
        """
        Execute agent with timing & error handling
        """
        start_time = time.time()
        
        try:
            logger.info(f"▶️  {self.name} starting...")
            
            # Call agent-specific logic
            data, confidence = self.process(context)
            
            execution_time = time.time() - start_time
            
            logger.info(
                f"✅ {self.name} complete "
                f"(confidence={confidence:.2%}, time={execution_time:.2f}s)"
            )
            
            return AgentResult(
                success=True,
                data=data,
                confidence=confidence,
                errors=[],
                execution_time=execution_time,
                agent_name=self.name
            )
        
        except Exception as e:
            execution_time = time.time() - start_time
            
            logger.error(f"❌ {self.name} failed: {e}")
            
            return AgentResult(
                success=False,
                data={},
                confidence=0.0,
                errors=[str(e)],
                execution_time=execution_time,
                agent_name=self.name
            )
    
    @abstractmethod
    def process(self, context: Dict[str, Any]) -> tuple[Dict[str, Any], float]:
        """
        Agent-specific processing logic
        
        Args:
            context: Shared context (OCR text, tokens, etc)
        
        Returns:
            (extracted_data, confidence_score)
        """
        pass
