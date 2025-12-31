"""
PDF Analyzer v3.3.2 - Production Grade (Stability + Perf Patch)
Based on v3.3.1 with minimal, additive changes only.

Changes (only additions / tiny edits):
1) FIX: letter_ratio denominator uses non-whitespace char count (more stable than char_count)
2) FIX: garbled ratio denominators use non-whitespace char count for consistency
3) PERF: avoid page.get_text("text") for likely-scanned pages (no words + has images)
"""
import fitz  # PyMuPDF
import unicodedata
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from src.core.logging import logger


@dataclass
class PageAnalysis:
    """Enhanced analysis result for a single page"""
    page_number: int
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
    pdf_type: str
    page_count: int
    total_images: int
    total_words: int
    total_chars: int
    pages: List[PageAnalysis]
    confidence: float
    recommended_strategy: str
    analysis_details: Dict


class PDFAnalyzer:
    """
    Production-grade PDF analyzer v3.3.2

    v3.3.2 patch:
    - letter_ratio uses non-whitespace denominator
    - garbled ratios use non-whitespace denominator (consistent)
    - perf: skip get_text("text") for likely-scanned pages (no words + has images)
    """

    # Thresholds
    MIN_WORDS_FOR_TEXT = 5
    MIN_CHARS_FOR_VALID_WORD = 2
    MIN_LETTER_RATIO_FOR_TEXT = 0.40
    IMAGE_COVERAGE_THRESHOLD = 0.30
    HYBRID_PAGES_MIN_RATIO = 0.15
    HYBRID_PAGES_MIN_COUNT = 2

    # Garbled detection
    REPLACEMENT_HARD = 0.05
    REPLACEMENT_SOFT = 0.01
    CONTROL_CHAR_THRESHOLD = 0.02
    FORMAT_CHAR_THRESHOLD = 0.05
    SINGLE_CHAR_THRESHOLD = 0.70
    LETTER_RATIO_VERY_LOW = 0.20
    LETTER_RATIO_LOW = 0.30

    def __init__(self):
        logger.debug("PDFAnalyzer v3.3.2 initialized")

    def analyze(self, pdf_path: str) -> PDFAnalysis:
        """Analyze PDF comprehensively"""
        try:
            if not Path(pdf_path).exists():
                raise FileNotFoundError(f"PDF not found: {pdf_path}")

            logger.info(f"🔍 Analyzing PDF: {pdf_path}")

            doc = fitz.open(pdf_path)

            page_analyses = []
            total_words = 0
            total_chars = 0
            total_images = 0

            for page_num in range(len(doc)):
                page_analysis = self._analyze_page(doc[page_num], page_num + 1)
                page_analyses.append(page_analysis)
                total_words += page_analysis.word_count
                total_chars += page_analysis.char_count
                total_images += page_analysis.image_count

            doc.close()

            pdf_type = self._determine_pdf_type(page_analyses)
            confidence = self._calculate_confidence(page_analyses, pdf_type)
            strategy = self._recommend_strategy(pdf_type, page_analyses)
            details = self._build_details(page_analyses, pdf_type)

            analysis = PDFAnalysis(
                pdf_type=pdf_type,
                page_count=len(page_analyses),
                total_images=total_images,
                total_words=total_words,
                total_chars=total_chars,
                pages=page_analyses,
                confidence=confidence,
                recommended_strategy=strategy,
                analysis_details=details
            )

            logger.info(
                f"✅ Analysis complete: Type={pdf_type}, Strategy={strategy}, "
                f"Confidence={confidence:.2%}"
            )

            return analysis

        except Exception as e:
            logger.error(f"PDF analysis failed: {str(e)}")
            raise

    def _analyze_page(self, page: fitz.Page, page_number: int) -> PageAnalysis:
        """Analyze single page"""

        # Extract words first (used for scan shortcut)
        words_data = page.get_text("words")
        raw_words = [
            w[4] for w in words_data
            if len(w) > 4 and isinstance(w[4], str)
        ]

        valid_words = [w for w in raw_words if len(w) >= self.MIN_CHARS_FOR_VALID_WORD]
        word_count = len(valid_words)

        # Images (needed for scan shortcut + coverage)
        image_list = page.get_images(full=True)
        image_count = len(image_list)
        has_images = image_count > 0

        # PERF PATCH: If likely scanned (no words + has images), skip expensive text extraction
        if word_count == 0 and has_images:
            text = ""
            char_count = 0
            non_space_count = 0
            letter_ratio = 0.0
        else:
            text = page.get_text("text")
            stripped = text.strip()
            char_count = len(stripped)

            # FIX: non-whitespace denominator for letter ratio
            non_space_count = sum(1 for c in stripped if not c.isspace())

            letter_count = sum(
                1 for c in stripped
                if unicodedata.category(c).startswith("L")
            )
            letter_ratio = letter_count / max(non_space_count, 1)

        # has_text with letter_ratio check
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

        image_coverage = self._calculate_image_coverage(page, image_list)

        logger.debug(
            f"Page {page_number}: Words={word_count}, Chars={char_count}, "
            f"LetterRatio={letter_ratio:.2%}, Images={image_count}, "
            f"Coverage={image_coverage:.2%}, Garbled={is_garbled}"
        )

        return PageAnalysis(
            page_number=page_number,
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

        # FIX: consistent denominator (non-whitespace)
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

        # 4. Letter ratio (already computed on non-space denom)
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
        """Determine PDF type"""

        if not pages:
            return "broken"

        digital_pages = []
        hybrid_pages = []
        image_only_pages = []
        broken_pages = []

        for page in pages:
            if page.has_text and not page.is_garbled:
                if not page.has_images or page.image_coverage < self.IMAGE_COVERAGE_THRESHOLD:
                    digital_pages.append(page)
                else:
                    hybrid_pages.append(page)

            elif not page.has_text and page.has_images:
                image_only_pages.append(page)

            elif page.has_text and page.is_garbled:
                broken_pages.append(page)

            else:
                broken_pages.append(page)

        total_pages = len(pages)

        logger.debug(
            f"Classification: Digital={len(digital_pages)}, "
            f"Hybrid={len(hybrid_pages)}, ImageOnly={len(image_only_pages)}, "
            f"Broken={len(broken_pages)}"
        )

        if len(broken_pages) == total_pages:
            return "broken"

        if len(broken_pages) / total_pages > 0.5:
            return "broken"

        if len(digital_pages) == total_pages:
            return "digital"

        if len(image_only_pages) == total_pages:
            return "image_only"

        hybrid_ratio = len(hybrid_pages) / total_pages
        has_enough_hybrid = (
            len(hybrid_pages) >= self.HYBRID_PAGES_MIN_COUNT
            or hybrid_ratio >= self.HYBRID_PAGES_MIN_RATIO
        )

        if has_enough_hybrid:
            return "hybrid"

        if len(digital_pages) > 0 and len(image_only_pages) > 0:
            return "hybrid"

        if len(digital_pages) / total_pages >= 0.7:
            return "digital"

        if len(image_only_pages) / total_pages >= 0.7:
            return "image_only"

        return "hybrid"

    def _calculate_confidence(self, pages: List[PageAnalysis], pdf_type: str) -> float:
        """Calculate confidence"""

        if pdf_type == "broken":
            return 0.0

        total_pages = len(pages)
        consistent_pages = 0

        for page in pages:
            if pdf_type == "digital":
                if page.has_text and not page.is_garbled:
                    if not page.has_images or page.image_coverage < self.IMAGE_COVERAGE_THRESHOLD:
                        consistent_pages += 1

            elif pdf_type == "image_only":
                if not page.has_text and page.has_images:
                    consistent_pages += 1

            elif pdf_type == "hybrid":
                if page.has_text and not page.is_garbled:
                    consistent_pages += 1
                elif not page.has_text and page.has_images:
                    consistent_pages += 1

        confidence = consistent_pages / total_pages
        return confidence

    def _recommend_strategy(self, pdf_type: str, pages: List[PageAnalysis]) -> str:
        """Recommend strategy"""

        if pdf_type == "digital":
            return "native"

        elif pdf_type == "image_only":
            return "ocr"

        elif pdf_type == "hybrid":
            strategies = [self._get_page_strategy(p) for p in pages]

            if "hybrid" in strategies:
                return "hybrid"
            elif "native" in strategies and "ocr" in strategies:
                return "hybrid"
            elif all(s == "native" for s in strategies):
                return "native"
            else:
                return "hybrid"

        else:
            return "ocr"

    def _build_details(self, pages: List[PageAnalysis], pdf_type: str) -> Dict:
        """Build details"""

        digital = [
            p for p in pages
            if p.has_text and not p.is_garbled
            and (not p.has_images or p.image_coverage < self.IMAGE_COVERAGE_THRESHOLD)
        ]

        hybrid = [
            p for p in pages
            if p.has_text and not p.is_garbled
            and p.has_images and p.image_coverage >= self.IMAGE_COVERAGE_THRESHOLD
        ]

        image_only = [
            p for p in pages
            if not p.has_text and p.has_images
        ]

        broken = [
            p for p in pages
            if p.is_garbled or (not p.has_text and not p.has_images)
        ]

        return {
            'page_breakdown': {
                'digital': len(digital),
                'hybrid': len(hybrid),
                'image_only': len(image_only),
                'broken': len(broken),
            },
            'content_stats': {
                'avg_words_per_page': sum(p.word_count for p in pages) / len(pages),
                'avg_images_per_page': sum(p.image_count for p in pages) / len(pages),
                'avg_image_coverage': sum(p.image_coverage for p in pages) / len(pages),
                'avg_letter_ratio': sum(p.letter_ratio for p in pages) / len(pages),
                'total_words': sum(p.word_count for p in pages),
                'total_images': sum(p.image_count for p in pages),
            },
            'quality_indicators': {
                'has_searchable_text': sum(p.word_count for p in pages) > 20,
                'has_images': sum(p.image_count for p in pages) > 0,
                'has_garbled_pages': any(p.is_garbled for p in pages),
                'has_hybrid_pages': len(hybrid) > 0,
                'likely_scanned': pdf_type in ['image_only', 'hybrid'],
            },
            'page_strategies': {
                p.page_number: self._get_page_strategy(p)
                for p in pages
            },
            'garbled_reasons_per_page': {
                p.page_number: p.garbled_reasons
                for p in pages if p.garbled_reasons
            }
        }

    def _get_page_strategy(self, page: PageAnalysis) -> str:
        """Get page strategy"""

        if page.has_text and not page.is_garbled:
            if page.has_images and page.image_coverage >= self.IMAGE_COVERAGE_THRESHOLD:
                return "hybrid"
            return "native"
        elif page.has_images:
            return "ocr"
        else:
            return "skip"

    def print_analysis(self, analysis: PDFAnalysis):
        """Pretty print"""

        print("\n" + "="*70)
        print("📊 PDF ANALYSIS REPORT v3.3.2")
        print("="*70)
        print(f"📄 PDF Type: {analysis.pdf_type.upper()}")
        print(f"🎯 Strategy: {analysis.recommended_strategy.upper()}")
        print(f"📈 Confidence: {analysis.confidence:.1%}")
        print(f"\n📑 Pages: {analysis.page_count}")
        print(f"📝 Total Words: {analysis.total_words}")
        print(f"🖼️  Total Images: {analysis.total_images}")

        print(f"\n📊 Page Breakdown:")
        breakdown = analysis.analysis_details['page_breakdown']
        for page_type, count in breakdown.items():
            print(f"   {page_type.capitalize()}: {count}")

        print(f"\n📈 Content Stats:")
        stats = analysis.analysis_details['content_stats']
        print(f"   Avg words/page: {stats['avg_words_per_page']:.1f}")
        print(f"   Avg letter ratio: {stats['avg_letter_ratio']:.1%}")
        print(f"   Avg image coverage: {stats['avg_image_coverage']:.1%}")

        print(f"\n🎯 Per-Page Strategy:")
        strategies = analysis.analysis_details['page_strategies']
        for page_num, strategy in strategies.items():
            emoji = {'native': '📝', 'hybrid': '🔀', 'ocr': '🖼️', 'skip': '⏭️'}.get(strategy, '❓')
            print(f"   Page {page_num}: {emoji} {strategy}")

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
