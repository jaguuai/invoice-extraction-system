"""
PDF Text Extractor
Native text extraction from PDF files
Works with 'text' type pages from PDFAnalyzer
"""
from dataclasses import dataclass
from typing import List, Optional, Dict
from pathlib import Path
import fitz  # PyMuPDF

from src.core.logging import logger


@dataclass
class PageText:
    """Text extraction result for single page"""
    page_number: int
    text: str
    char_count: int
    word_count: int
    is_empty: bool


@dataclass
class DocumentText:
    """Complete document text extraction result"""
    file_path: str
    page_count: int
    pages: List[PageText]
    combined_text: str
    total_chars: int
    total_words: int
    extraction_method: str = "native"


class PDFTextExtractor:
    """
    Native PDF text extractor
    
    Extracts searchable text from PDF files using PyMuPDF.
    Fast and efficient for 'text' type pages.
    
    Usage:
        extractor = get_pdf_text_extractor()
        
        # Extract all pages
        result = extractor.extract("invoice.pdf")
        
        # Extract specific pages
        result = extractor.extract("invoice.pdf", pages=[1, 2])
        
        # Extract single page
        page = extractor.extract_page("invoice.pdf", 1)
    """
    
    def __init__(self):
        logger.debug("PDFTextExtractor initialized")
    
    def extract(self, pdf_path: str, pages: Optional[List[int]] = None) -> DocumentText:
        """
        Extract text from PDF
        
        Args:
            pdf_path: Path to PDF file
            pages: Optional list of page numbers (1-indexed)
                   If None, extracts all pages
        
        Returns:
            DocumentText with extracted content
        """
        
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        logger.info(f"📄 Extracting text from: {pdf_path}")
        
        doc = fitz.open(pdf_path)
        page_count = len(doc)
        
        # Determine which pages to extract
        if pages is None:
            pages_to_extract = range(page_count)
        else:
            # Convert 1-indexed to 0-indexed and validate
            pages_to_extract = [
                p - 1 for p in pages 
                if 0 < p <= page_count
            ]
        
        logger.debug(f"Extracting {len(pages_to_extract)} pages")
        
        # Extract each page
        page_results: List[PageText] = []
        
        for page_idx in pages_to_extract:
            page_num = page_idx + 1
            page = doc[page_idx]
            
            page_result = self._extract_page(page, page_num)
            page_results.append(page_result)
            
            logger.debug(
                f"Page {page_num}: {page_result.char_count} chars, "
                f"{page_result.word_count} words"
            )
        
        doc.close()
        
        # Combine all pages
        combined_text = self._combine_pages(page_results)
        total_chars = sum(p.char_count for p in page_results)
        total_words = sum(p.word_count for p in page_results)
        
        result = DocumentText(
            file_path=str(pdf_path),
            page_count=page_count,
            pages=page_results,
            combined_text=combined_text,
            total_chars=total_chars,
            total_words=total_words,
            extraction_method="native"
        )
        
        logger.info(
            f"✅ Extraction complete: {total_chars} chars, "
            f"{total_words} words from {len(page_results)} pages"
        )
        
        return result
    
    def extract_page(self, pdf_path: str, page_number: int) -> PageText:
        """
        Extract text from single page
        
        Args:
            pdf_path: Path to PDF file
            page_number: Page number (1-indexed)
        
        Returns:
            PageText for the specified page
        """
        
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        doc = fitz.open(pdf_path)
        
        if page_number < 1 or page_number > len(doc):
            doc.close()
            raise ValueError(
                f"Invalid page number {page_number}. "
                f"PDF has {len(doc)} pages."
            )
        
        page = doc[page_number - 1]
        result = self._extract_page(page, page_number)
        
        doc.close()
        
        logger.info(
            f"✅ Page {page_number}: {result.char_count} chars, "
            f"{result.word_count} words"
        )
        
        return result
    
    def _extract_page(self, page: fitz.Page, page_number: int) -> PageText:
        """Extract text from single page object"""
        
        # Extract text
        text = page.get_text("text")
        
        # Clean and count
        text = text.strip()
        char_count = len(text)
        word_count = len(text.split()) if text else 0
        is_empty = char_count == 0
        
        return PageText(
            page_number=page_number,
            text=text,
            char_count=char_count,
            word_count=word_count,
            is_empty=is_empty
        )
    
    def _combine_pages(self, pages: List[PageText]) -> str:
        """Combine page texts into single document"""
        
        parts = []
        
        for page in pages:
            if not page.is_empty:
                # Add page separator
                parts.append(f"\n--- Sayfa {page.page_number} ---\n")
                parts.append(page.text)
        
        return "\n".join(parts).strip()
    
    def extract_metadata(self, pdf_path: str) -> Dict:
        """
        Extract PDF metadata
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            Dictionary with PDF metadata
        """
        
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        doc = fitz.open(pdf_path)
        
        metadata = {
            "page_count": len(doc),
            "format": doc.metadata.get("format", ""),
            "title": doc.metadata.get("title", ""),
            "author": doc.metadata.get("author", ""),
            "subject": doc.metadata.get("subject", ""),
            "keywords": doc.metadata.get("keywords", ""),
            "creator": doc.metadata.get("creator", ""),
            "producer": doc.metadata.get("producer", ""),
            "creation_date": doc.metadata.get("creationDate", ""),
            "mod_date": doc.metadata.get("modDate", ""),
        }
        
        doc.close()
        
        logger.debug(f"Metadata extracted: {len(metadata)} fields")
        
        return metadata


# Singleton instance
_pdf_text_extractor = None

def get_pdf_text_extractor() -> PDFTextExtractor:
    """Get PDF text extractor singleton instance"""
    global _pdf_text_extractor
    if _pdf_text_extractor is None:
        _pdf_text_extractor = PDFTextExtractor()
    return _pdf_text_extractor