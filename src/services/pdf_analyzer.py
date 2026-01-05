"""
PDF Analyzer v4.0 - Simplified Production Version
Simplified classification: text, image, broken
Page-level analysis for granular routing
"""
import fitz  # PyMuPDF
import unicodedata
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, field
from src.core.logging import logger


@dataclass
class PageAnalysis:
    """Analysis result for single page"""
    page_number: int
    page_type: str  # 'text', 'image', 'broken'
    has_text: bool
    has_images: bool
    word_count: int
    char_count: int
    image_count: int
    is_garbled: bool
    garbled_reasons: List[str] = field(default_factory=list)
    image_coverage: float = 0.0
    letter_ratio: float = 0.0


@dataclass
class PDFAnalysis:
    """Complete PDF analysis result"""
    pdf_type: str  # 'text', 'image', 'broken'
    page_count: int
    pages: List[PageAnalysis]
    total_words: int
    total_images: int
    confidence: float
    page_type_counts: Dict[str, int]  # Count per type
    analysis_details: Dict


class PDFAnalyzer:
    """
    Simplified PDF analyzer v4.0
    
    Classification:
    - text: Has searchable text (good quality)
    - image: Scanned/image-only (needs OCR)
    - broken: Garbled or empty
    
    Page-level analysis for granular routing.
    """
    
    # Thresholds
    MIN_WORDS_FOR_TEXT = 5
    MIN_CHARS_FOR_VALID_WORD = 2
    MIN_LETTER_RATIO_FOR_TEXT = 0.40
    
    # Garbled detection
    REPLACEMENT_HARD = 0.05
    REPLACEMENT_SOFT = 0.01
    CONTROL_CHAR_THRESHOLD = 0.02
    FORMAT_CHAR_THRESHOLD = 0.05
    SINGLE_CHAR_THRESHOLD = 0.70
    LETTER_RATIO_VERY_LOW = 0.20
    LETTER_RATIO_LOW = 0.30
    
    def __init__(self):
        logger.debug("PDFAnalyzer v4.0 (simplified) initialized")
    
    def analyze(self, pdf_path: str) -> PDFAnalysis:
        """Analyze PDF with simplified classification"""
        
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        logger.info(f"🔍 Analyzing PDF: {pdf_path}")
        
        doc = fitz.open(pdf_path)
        
        page_analyses = []
        total_words = 0
        total_images = 0
        
        for page_num in range(len(doc)):
            page_analysis = self._analyze_page(doc[page_num], page_num + 1)
            page_analyses.append(page_analysis)
            total_words += page_analysis.word_count
            total_images += page_analysis.image_count
        
        doc.close()
        
        # Determine PDF type from page types
        pdf_type = self._determine_pdf_type(page_analyses)
        confidence = self._calculate_confidence(page_analyses, pdf_type)
        
        # Count page types
        page_type_counts = {
            'text': sum(1 for p in page_analyses if p.page_type == 'text'),
            'image': sum(1 for p in page_analyses if p.page_type == 'image'),
            'broken': sum(1 for p in page_analyses if p.page_type == 'broken'),
        }
        
        details = self._build_details(page_analyses, pdf_type)
        
        analysis = PDFAnalysis(
            pdf_type=pdf_type,
            page_count=len(page_analyses),
            pages=page_analyses,
            total_words=total_words,
            total_images=total_images,
            confidence=confidence,
            page_type_counts=page_type_counts,
            analysis_details=details
        )
        
        logger.info(
            f"✅ Analysis: Type={pdf_type}, Confidence={confidence:.2%}, "
            f"Text={page_type_counts['text']}, Image={page_type_counts['image']}, "
            f"Broken={page_type_counts['broken']}"
        )
        
        return analysis
    
    def _analyze_page(self, page: fitz.Page, page_number: int) -> PageAnalysis:
        """Analyze single page and classify as text/image/broken"""
        
        # Extract words
        words_data = page.get_text("words")
        raw_words = [
            w[4] for w in words_data 
            if len(w) > 4 and isinstance(w[4], str)
        ]
        
        valid_words = [w for w in raw_words if len(w) >= self.MIN_CHARS_FOR_VALID_WORD]
        word_count = len(valid_words)
        
        # Images
        image_list = page.get_images(full=True)
        image_count = len(image_list)
        has_images = image_count > 0
        
        # Performance optimization: skip text extraction for obvious scans
        if word_count == 0 and has_images:
            text = ""
            char_count = 0
            letter_ratio = 0.0
        else:
            text = page.get_text("text")
            stripped = text.strip()
            char_count = len(stripped)
            
            non_space_count = sum(1 for c in stripped if not c.isspace())
            letter_count = sum(
                1 for c in stripped 
                if unicodedata.category(c).startswith("L")
            )
            letter_ratio = letter_count / max(non_space_count, 1)
        
        # Has meaningful text?
        has_text = (
            (word_count >= self.MIN_WORDS_FOR_TEXT) 
            or 
            (char_count >= 80 and letter_ratio >= self.MIN_LETTER_RATIO_FOR_TEXT)
        )
        
        # Garbled check
        is_garbled, garbled_reasons = self._is_text_garbled(
            text=text,
            raw_words=raw_words,
            valid_words=valid_words,
            char_count=char_count,
            word_count=word_count,
            letter_ratio=letter_ratio
        )
        
        # Image coverage
        image_coverage = self._calculate_image_coverage(page, image_list)
        
        # Determine page type
        page_type = self._classify_page(
            has_text=has_text,
            has_images=has_images,
            is_garbled=is_garbled
        )
        
        logger.debug(
            f"Page {page_number}: Type={page_type}, Words={word_count}, "
            f"Images={image_count}, Garbled={is_garbled}"
        )
        
        return PageAnalysis(
            page_number=page_number,
            page_type=page_type,
            has_text=has_text,
            has_images=has_images,
            word_count=word_count,
            char_count=char_count,
            image_count=image_count,
            is_garbled=is_garbled,
            garbled_reasons=garbled_reasons,
            image_coverage=image_coverage,
            letter_ratio=letter_ratio
        )
    
    def _classify_page(self, has_text: bool, has_images: bool, is_garbled: bool) -> str:
        """
        Classify single page
        
        Rules:
        - text: Has good text (with or without images)
        - image: No text, has images (needs OCR)
        - broken: Garbled text OR no content
        """
        
        if has_text and not is_garbled:
            return "text"  # Has searchable text
        
        elif not has_text and has_images:
            return "image"  # Scanned/image-only
        
        else:
            return "broken"  # Garbled or empty
    
    def _is_text_garbled(
        self,
        text: str,
        raw_words: List[str],
        valid_words: List[str],
        char_count: int,
        word_count: int,
        letter_ratio: float
    ) -> Tuple[bool, List[str]]:
        """Detect garbled text"""
        
        reasons = []
        t = (text or "").strip()
        
        if not t:
            return False, reasons
        
        # Non-whitespace denominator
        denom = sum(1 for c in t if not c.isspace())
        n = max(denom, 1)
        
        # 1. Replacement chars
        repl_count = t.count("\ufffd")
        repl_ratio = repl_count / n
        
        if repl_ratio >= self.REPLACEMENT_HARD:
            return True, ["replacement_hard"]
        
        if repl_ratio >= self.REPLACEMENT_SOFT:
            reasons.append("replacement_soft")
        
        # 2. Control vs Format
        cc_count = 0
        cf_count = 0
        
        for c in t:
            if c in ["\n", "\r", "\t", " "]:
                continue
            cat = unicodedata.category(c)
            if cat == "Cc":
                cc_count += 1
            elif cat == "Cf":
                cf_count += 1
        
        cc_ratio = cc_count / n
        cf_ratio = cf_count / n
        
        if cc_ratio > self.CONTROL_CHAR_THRESHOLD:
            return True, ["control_chars_high"]
        
        if cf_ratio > self.FORMAT_CHAR_THRESHOLD:
            reasons.append("format_chars_suspicious")
        
        # 3. Single-char tokens
        single_chars = sum(1 for w in raw_words if len(w.strip()) == 1)
        raw_word_count = max(len(raw_words), 1)
        single_ratio = single_chars / raw_word_count
        
        if single_ratio > self.SINGLE_CHAR_THRESHOLD:
            return True, ["single_char_tokens_high"]
        
        # 4. Letter ratio
        if letter_ratio < self.LETTER_RATIO_VERY_LOW:
            return True, ["letter_ratio_very_low"]
        
        if letter_ratio < self.LETTER_RATIO_LOW and word_count < 5:
            return True, ["letter_ratio_low_and_few_words"]
        
        # 5. Char/word mismatch
        if char_count > 100 and word_count < 5:
            return True, ["char_word_mismatch"]
        
        # 6. Soft signals
        if "replacement_soft" in reasons and word_count < 10:
            return True, ["replacement_soft_plus_low_words"]
        
        if "format_chars_suspicious" in reasons and word_count < 10:
            return True, ["format_chars_plus_low_words"]
        
        return False, reasons
    
    def _calculate_image_coverage(self, page: fitz.Page, image_list: List) -> float:
        """Calculate image coverage"""
        
        if not image_list:
            return 0.0
        
        try:
            page_area = page.rect.width * page.rect.height
            total_image_area = 0
            
            for img_index in range(len(image_list)):
                try:
                    img_rects = page.get_image_rects(image_list[img_index][0])
                    for rect in img_rects:
                        total_image_area += rect.width * rect.height
                except:
                    pass
            
            coverage = min(total_image_area / page_area, 1.0)
            return coverage
        except:
            return 0.5 if len(image_list) > 0 else 0.0
    
    def _determine_pdf_type(self, pages: List[PageAnalysis]) -> str:
        """
        Determine PDF type from page types
        
        Rules:
        - text: Majority are text pages
        - image: Majority are image pages
        - broken: Majority are broken OR all broken
        """
        
        if not pages:
            return "broken"
        
        text_pages = sum(1 for p in pages if p.page_type == 'text')
        image_pages = sum(1 for p in pages if p.page_type == 'image')
        broken_pages = sum(1 for p in pages if p.page_type == 'broken')
        
        total = len(pages)
        
        # All broken
        if broken_pages == total:
            return "broken"
        
        # Majority broken
        if broken_pages / total > 0.5:
            return "broken"
        
        # Majority text
        if text_pages / total >= 0.5:
            return "text"
        
        # Majority image
        if image_pages / total >= 0.5:
            return "image"
        
        # Mixed: more text than image → text
        if text_pages > image_pages:
            return "text"
        else:
            return "image"
    
    def _calculate_confidence(self, pages: List[PageAnalysis], pdf_type: str) -> float:
        """Calculate confidence"""
        
        if pdf_type == "broken":
            return 0.0
        
        total = len(pages)
        matching = sum(1 for p in pages if p.page_type == pdf_type)
        
        return matching / total
    
    def _build_details(self, pages: List[PageAnalysis], pdf_type: str) -> Dict:
        """Build analysis details"""
        
        return {
            'page_types': {
                p.page_number: p.page_type 
                for p in pages
            },
            'content_stats': {
                'avg_words_per_page': sum(p.word_count for p in pages) / len(pages),
                'avg_images_per_page': sum(p.image_count for p in pages) / len(pages),
                'avg_letter_ratio': sum(p.letter_ratio for p in pages) / len(pages),
                'total_words': sum(p.word_count for p in pages),
                'total_images': sum(p.image_count for p in pages),
            },
            'garbled_reasons_per_page': {
                p.page_number: p.garbled_reasons 
                for p in pages if p.garbled_reasons
            }
        }
    
    def print_analysis(self, analysis: PDFAnalysis):
        """Pretty print"""
        
        print("\n" + "="*70)
        print("📊 PDF ANALYSIS REPORT v4.0 (Simplified)")
        print("="*70)
        print(f"📄 PDF Type: {analysis.pdf_type.upper()}")
        print(f"📈 Confidence: {analysis.confidence:.1%}")
        print(f"\n📑 Total Pages: {analysis.page_count}")
        print(f"📝 Total Words: {analysis.total_words}")
        print(f"🖼️  Total Images: {analysis.total_images}")
        
        print(f"\n📊 Page Type Breakdown:")
        for page_type, count in analysis.page_type_counts.items():
            emoji = {'text': '📝', 'image': '🖼️', 'broken': '⚠️'}.get(page_type, '❓')
            print(f"   {emoji} {page_type.capitalize()}: {count}")
        
        print(f"\n🎯 Per-Page Types:")
        page_types = analysis.analysis_details['page_types']
        for page_num, page_type in page_types.items():
            emoji = {'text': '📝', 'image': '🖼️', 'broken': '⚠️'}.get(page_type, '❓')
            print(f"   Page {page_num}: {emoji} {page_type}")
        
        garbled = analysis.analysis_details.get('garbled_reasons_per_page', {})
        if garbled:
            print(f"\n⚠️  Garbled Pages:")
            for page_num, reasons in garbled.items():
                print(f"   Page {page_num}: {', '.join(reasons)}")
        
        print("="*70 + "\n")


_pdf_analyzer = None

def get_pdf_analyzer() -> PDFAnalyzer:
    global _pdf_analyzer
    if _pdf_analyzer is None:
        _pdf_analyzer = PDFAnalyzer()
    return _pdf_analyzer