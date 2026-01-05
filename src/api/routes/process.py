# encoding: utf-8

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import shutil
from datetime import datetime

from pydantic import BaseModel
from typing import List, Optional

from src.core.logging import logger
from src.core.config import settings

from src.services.image_preprocessor import get_image_preprocessor
from src.services.paddle_ocr_service import get_paddle_ocr_service
from src.services.orchestrator.invoice_orchestrator import InvoiceOrchestrator


router = APIRouter(prefix="/process", tags=["process"])


# -----------------------------
# CONSTANTS
# -----------------------------

TEXT_EXTENSIONS = {".txt", ".md", ".csv"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}


# -----------------------------
# RESPONSE MODELS
# -----------------------------

class InvoiceItemResponse(BaseModel):
    description: str
    quantity: float
    unit_price: float
    total_price: float
    confidence: float


class ProcessResponse(BaseModel):
    success: bool
    file_name: str
    file_type: str
    processing_method: str

    text: str
    char_count: int
    word_count: int
    ocr_confidence: Optional[float] = None
    page_count: int

    items: List[InvoiceItemResponse]


# -----------------------------
# ENDPOINT
# -----------------------------

@router.post("/", response_model=ProcessResponse)
async def process_file(file: UploadFile = File(...)):
    try:
        file_path, safe_filename = _save_upload(file)
        suffix = file_path.suffix.lower()

        logger.info(f"📄 Processing file: {safe_filename}")

        # -------------------------
        # TEXT FILE → DIRECT READ
        # -------------------------
        if suffix in TEXT_EXTENSIONS:
            logger.info("📝 Text file detected → OCR bypass")

            text = file_path.read_text(encoding="utf-8", errors="ignore")

            return ProcessResponse(
                success=True,
                file_name=safe_filename,
                file_type="text",
                processing_method="direct_text",

                text=text,
                char_count=len(text),
                word_count=len(text.split()),
                ocr_confidence=None,
                page_count=1,

                items=[]
            )

        # -------------------------
        # IMAGE FILE → OCR
        # -------------------------
        if suffix in IMAGE_EXTENSIONS:
            return await _process_image(file_path, safe_filename)

        # -------------------------
        # UNSUPPORTED FILE
        # -------------------------
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {suffix}"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Processing failed")
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# HELPERS
# -----------------------------

def _save_upload(file: UploadFile):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / safe_filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return file_path, safe_filename


# -----------------------------
# IMAGE PIPELINE
# -----------------------------

async def _process_image(file_path: Path, filename: str) -> ProcessResponse:
    logger.info("🖼️ Image → OCR → TABLE")

    from PIL import Image

    image = Image.open(file_path)

    preprocessor = get_image_preprocessor()
    processed = preprocessor.preprocess(image).processed

    ocr = get_paddle_ocr_service()
    ocr_result = ocr.extract_from_image(processed)

    orchestrator = InvoiceOrchestrator()
    pipeline = orchestrator.run(
        ocr_text=ocr_result.text,
        ocr_tokens=ocr_result.tokens
    )

    return ProcessResponse(
        success=True,
        file_name=filename,
        file_type="image",
        processing_method="ocr",

        text=ocr_result.text,
        char_count=ocr_result.char_count,
        word_count=ocr_result.word_count,
        ocr_confidence=ocr_result.confidence,
        page_count=1,

        items=pipeline["items"]
    )
