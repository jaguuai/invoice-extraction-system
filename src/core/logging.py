"""
Logging Configuration
Professional logging setup using Loguru
Supports console and file output with rotation
"""
from loguru import logger
import sys
from pathlib import Path
from src.core.config import settings


def setup_logging():
    """
    Configure logging for the application
    - Console output with colors
    - File output with rotation
    - Automatic project-relative log directory
    """

    # Remove default handler
    logger.remove()

    # ============================
    # FIX: DYNAMIC LOG DIRECTORY
    # ============================
    # Proje kökünü bul -> src/core/logging.py → src → project root
    project_root = Path(__file__).resolve().parents[2]
    log_dir = project_root / "logs"   # /app/logs YOK ARTIK
    log_dir.mkdir(parents=True, exist_ok=True)

    # Console handler (colorized)
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
               "<level>{message}</level>",
        level=settings.LOG_LEVEL,
        colorize=True,
    )

    # File handler (all logs)
    logger.add(
        log_dir / "app.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation=settings.LOG_ROTATION,
        retention=settings.LOG_RETENTION,
        compression="zip",
        enqueue=True,
    )

    # File handler (errors only)
    logger.add(
        log_dir / "error.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation=settings.LOG_ROTATION,
        retention=settings.LOG_RETENTION,
        compression="zip",
        enqueue=True,
    )

    logger.info("🚀 Logging system initialized")
    logger.debug(f"Environment: {settings.ENV}")
    logger.debug(f"Log level: {settings.LOG_LEVEL}")

    return logger


# Initialize logging on module import
log = setup_logging()


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def log_api_request(method: str, path: str, status_code: int, duration_ms: float):
    """Log API request with details"""
    logger.info(
        f"API {method} {path} - Status: {status_code} - Duration: {duration_ms:.2f}ms"
    )


def log_agent_execution(agent_name: str, status: str, duration_ms: float):
    """Log agent execution"""
    logger.info(
        f"Agent [{agent_name}] - Status: {status} - Duration: {duration_ms:.2f}ms"
    )


def log_llm_call(model: str, prompt_length: int, response_length: int, duration_ms: float):
    """Log LLM API call"""
    logger.debug(
        f"LLM Call [{model}] - Prompt: {prompt_length} chars - "
        f"Response: {response_length} chars - Duration: {duration_ms:.2f}ms"
    )


def log_error(error: Exception, context: str = ""):
    """Log error with traceback"""
    logger.exception(f"Error in {context}: {str(error)}")
