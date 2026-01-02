"""
Analysis Endpoint
PDF analysis with file upload support
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from pathlib import Path
import shutil
from datetime import datetime

from src.core.logging import logger
from src.core.config import settings
from src.services.pdf_analyzer import get_pdf_analyzer
from pydantic import BaseModel


router = APIRouter(prefix="/analyze", tags=["analyze"])


class AnalyzeRequest(BaseModel):
    """Request model for PDF analysis by filename"""
    file_name: str


class PageInfo(BaseModel):
    """Page information"""
    page_number: int
    page_type: str
    word_count: int
    image_count: int
    is_garbled: bool


class AnalyzeResponse(BaseModel):
    """Response model for PDF analysis"""
    success: bool
    file_name: str
    pdf_type: str
    page_count: int
    confidence: float
    page_type_counts: dict
    pages: list[PageInfo]


@router.post("/pdf", response_model=AnalyzeResponse)
async def analyze_pdf_by_name(request: AnalyzeRequest):
    """
    Analyze PDF by filename (must be uploaded first)
    """
    
    file_path = Path(settings.UPLOAD_DIR) / request.file_name
    
    if not file_path.exists():
        raise HTTPException(
            status_code=404, 
            detail=f"File not found: {request.file_name}"
        )
    
    if file_path.suffix.lower() != ".pdf":
        raise HTTPException(
            status_code=400, 
            detail="Not a PDF file"
        )
    
    try:
        logger.info(f"?? Analyzing PDF: {request.file_name}")
        
        analyzer = get_pdf_analyzer()
        analysis = analyzer.analyze(str(file_path))
        
        pages_info = [
            PageInfo(
                page_number=p.page_number,
                page_type=p.page_type,
                word_count=p.word_count,
                image_count=p.image_count,
                is_garbled=p.is_garbled
            )
            for p in analysis.pages
        ]
        
        logger.info(
            f"? Analysis complete: Type={analysis.pdf_type}, "
            f"Confidence={analysis.confidence:.2%}"
        )
        
        return AnalyzeResponse(
            success=True,
            file_name=request.file_name,
            pdf_type=analysis.pdf_type,
            page_count=analysis.page_count,
            confidence=analysis.confidence,
            page_type_counts=analysis.page_type_counts,
            pages=pages_info
        )
    
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Analysis failed: {str(e)}"
        )


@router.post("/upload-and-analyze", response_model=AnalyzeResponse)
async def upload_and_analyze_pdf(file: UploadFile = File(...)):
    """
    Upload PDF and analyze in one step (RECOMMENDED)
    
    This is the easiest way - just upload the file!
    """
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )
    
    try:
        # Generate safe filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file.filename}"
        
        # Create upload directory
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file
        file_path = upload_dir / safe_filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"? File uploaded: {safe_filename}")
        
        # Analyze immediately
        logger.info(f"?? Analyzing PDF: {safe_filename}")
        
        analyzer = get_pdf_analyzer()
        analysis = analyzer.analyze(str(file_path))
        
        pages_info = [
            PageInfo(
                page_number=p.page_number,
                page_type=p.page_type,
                word_count=p.word_count,
                image_count=p.image_count,
                is_garbled=p.is_garbled
            )
            for p in analysis.pages
        ]
        
        logger.info(
            f"? Analysis complete: Type={analysis.pdf_type}, "
            f"Confidence={analysis.confidence:.2%}"
        )
        
        return AnalyzeResponse(
            success=True,
            file_name=safe_filename,
            pdf_type=analysis.pdf_type,
            page_count=analysis.page_count,
            confidence=analysis.confidence,
            page_type_counts=analysis.page_type_counts,
            pages=pages_info
        )
    
    except Exception as e:
        logger.error(f"Upload and analysis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed: {str(e)}"
        )
