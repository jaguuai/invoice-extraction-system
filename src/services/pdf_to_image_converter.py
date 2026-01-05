"""
PDF to Image Converter
Converts PDF pages to images for OCR processing
Uses pdf2image library with configurable DPI
"""
from pdf2image import convert_from_path
from PIL import Image
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

from src.core.logging import logger
from src.core.config import settings


@dataclass
class ImageConversionResult:
    """Result of PDF to image conversion"""
    pdf_path: str
    page_count: int
    images: List[Image.Image]
    dpi: int
    format: str = "PNG"


class PDFToImageConverter:
    """
    Convert PDF pages to images
    
    Converts PDF files to PIL Image objects for OCR processing.
    Optimized for Turkish invoice OCR with configurable DPI.
    
    Usage:
        converter = get_pdf_to_image_converter()
        result = converter.convert("invoice.pdf")
        
        for i, image in enumerate(result.images):
            # Process image with OCR
            pass
    """
    
    def __init__(self, dpi: Optional[int] = None):
        """
        Initialize converter
        
        Args:
            dpi: Image resolution (default from settings)
        """
        self.dpi = dpi or settings.OCR_DPI
        logger.debug(f"PDFToImageConverter initialized (DPI={self.dpi})")
    
    def convert(
        self, 
        pdf_path: str, 
        pages: Optional[List[int]] = None,
        dpi: Optional[int] = None
    ) -> ImageConversionResult:
        """
        Convert PDF to images
        
        Args:
            pdf_path: Path to PDF file
            pages: Optional list of page numbers (1-indexed)
                   If None, converts all pages
            dpi: Optional DPI override
        
        Returns:
            ImageConversionResult with PIL Images
        """
        
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        use_dpi = dpi or self.dpi
        
        logger.info(f"🖼️  Converting PDF to images: {Path(pdf_path).name}")
        logger.info(f"DPI: {use_dpi}")
        
        try:
            # Convert PDF to images
            if pages:
                # Convert specific pages
                logger.debug(f"Converting pages: {pages}")
                images = convert_from_path(
                    pdf_path,
                    dpi=use_dpi,
                    fmt='png',
                    thread_count=2,
                    first_page=min(pages),
                    last_page=max(pages)
                )
            else:
                # Convert all pages
                images = convert_from_path(
                    pdf_path,
                    dpi=use_dpi,
                    fmt='png',
                    thread_count=2
                )
            
            logger.info(f"✅ Converted {len(images)} pages to images")
            
            return ImageConversionResult(
                pdf_path=str(pdf_path),
                page_count=len(images),
                images=images,
                dpi=use_dpi,
                format="PNG"
            )
        
        except Exception as e:
            logger.error(f"PDF to image conversion failed: {str(e)}")
            raise
    
    def convert_single_page(
        self, 
        pdf_path: str, 
        page_number: int,
        dpi: Optional[int] = None
    ) -> Image.Image:
        """
        Convert single PDF page to image
        
        Args:
            pdf_path: Path to PDF file
            page_number: Page number (1-indexed)
            dpi: Optional DPI override
        
        Returns:
            PIL Image object
        """
        
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        use_dpi = dpi or self.dpi
        
        logger.info(f"🖼️  Converting page {page_number} to image")
        
        try:
            images = convert_from_path(
                pdf_path,
                dpi=use_dpi,
                fmt='png',
                first_page=page_number,
                last_page=page_number
            )
            
            if not images:
                raise ValueError(f"Failed to convert page {page_number}")
            
            logger.info(f"✅ Page {page_number} converted successfully")
            
            return images[0]
        
        except Exception as e:
            logger.error(f"Page conversion failed: {str(e)}")
            raise
    
    def save_images(
        self, 
        images: List[Image.Image], 
        output_dir: str,
        base_name: str = "page"
    ) -> List[str]:
        """
        Save images to disk
        
        Args:
            images: List of PIL Images
            output_dir: Output directory path
            base_name: Base name for files (default: "page")
        
        Returns:
            List of saved file paths
        """
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        saved_paths = []
        
        for i, image in enumerate(images, 1):
            filename = f"{base_name}_{i}.png"
            file_path = output_path / filename
            
            image.save(file_path, "PNG")
            saved_paths.append(str(file_path))
            
            logger.debug(f"Saved: {filename}")
        
        logger.info(f"✅ Saved {len(saved_paths)} images to {output_dir}")
        
        return saved_paths
    
    def get_image_info(self, image: Image.Image) -> dict:
        """
        Get image information
        
        Args:
            image: PIL Image
        
        Returns:
            Dictionary with image metadata
        """
        
        return {
            "size": image.size,
            "width": image.width,
            "height": image.height,
            "mode": image.mode,
            "format": image.format or "PNG"
        }


# Singleton instance
_pdf_to_image_converter = None

def get_pdf_to_image_converter(dpi: Optional[int] = None) -> PDFToImageConverter:
    """Get PDF to image converter singleton instance"""
    global _pdf_to_image_converter
    if _pdf_to_image_converter is None:
        _pdf_to_image_converter = PDFToImageConverter(dpi=dpi)
    return _pdf_to_image_converter
