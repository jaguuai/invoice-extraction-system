"""
PaddleOCR Service - With Bounding Boxes (SAFE VERSION)

- Lazy import (Docker-safe)
- No import-time crash
- Structured OCR tokens
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Any, Tuple

import numpy as np
from PIL import Image

from src.core.logging import logger


# =====================================================
# LAZY IMPORT (CRITICAL)
# =====================================================
try:
    from paddleocr import PaddleOCR
except ImportError:
    PaddleOCR = None
    logger.warning("⚠️ PaddleOCR not installed. OCR will be disabled.")


# =====================================================
# DATA MODELS
# =====================================================
@dataclass
class OCRToken:
    """Single OCR detection with position"""
    text: str
    confidence: float
    bbox: Tuple[float, float, float, float]  # (x0, y0, x1, y1)
    center_x: float
    center_y: float


@dataclass
class OCRResult:
    text: str
    confidence: float
    char_count: int
    word_count: int
    line_count: int
    tokens: List[OCRToken]


# =====================================================
# SERVICE
# =====================================================
class PaddleOCRService:
    """PaddleOCR with structured token output"""

    def __init__(self):
        if PaddleOCR is None:
            raise RuntimeError(
                "PaddleOCR is not installed in this environment. "
                "OCR feature is disabled."
            )

        logger.info("🧠 Initializing PaddleOCR...")

        self.ocr: Optional[PaddleOCR] = None
        self.lang_used: Optional[str] = None

        for lang in ("tr", "latin", "en"):
            try:
                logger.info(f"🔍 Trying OCR lang='{lang}'")
                self.ocr = PaddleOCR(use_angle_cls=True, lang=lang)
                self.lang_used = lang
                logger.info(f"✅ PaddleOCR initialized (lang={lang})")
                break
            except Exception as e:
                logger.warning(f"⚠️ OCR lang '{lang}' failed: {e}")

        if self.ocr is None:
            raise RuntimeError("❌ PaddleOCR initialization failed for all languages")

    # -------------------------------------------------
    # SINGLE IMAGE
    # -------------------------------------------------
    def extract_from_image(self, image: Image.Image) -> OCRResult:
        try:
            img = np.array(image)

            if img.ndim == 2:
                img = np.stack([img] * 3, axis=-1)
            elif img.ndim == 3 and img.shape[2] == 4:
                img = img[:, :, :3]

            logger.info("🖼 Running OCR...")
            raw = self.ocr.ocr(img)

            tokens = self._parse_tokens(raw)

            text_lines = [t.text for t in tokens]
            full_text = "\n".join(text_lines)

            confidences = [t.confidence for t in tokens]
            avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

            return OCRResult(
                text=full_text,
                confidence=avg_conf,
                char_count=len(full_text),
                word_count=len(full_text.split()) if full_text else 0,
                line_count=len(text_lines),
                tokens=tokens,
            )

        except Exception as e:
            logger.error(f"❌ OCR failed: {e}", exc_info=True)
            return OCRResult("", 0.0, 0, 0, 0, [])

    # -------------------------------------------------
    # TOKEN PARSER
    # -------------------------------------------------
    def _parse_tokens(self, raw: Any) -> List[OCRToken]:
        tokens: List[OCRToken] = []

        if not raw or not isinstance(raw, list):
            return tokens

        data = raw[0]

        # New PaddleOCR dict format
        if isinstance(data, dict):
            texts = data.get("rec_texts", [])
            scores = data.get("rec_scores", [])
            boxes = data.get("rec_boxes", [])

            for i, text in enumerate(texts):
                text = str(text).strip()
                if not text:
                    continue

                conf = float(scores[i]) if i < len(scores) else 0.9

                if i < len(boxes):
                    x0, y0, x1, y1 = map(float, boxes[i])
                else:
                    x0, y0, x1, y1 = 0.0, 0.0, 100.0, 20.0

                tokens.append(
                    OCRToken(
                        text=text,
                        confidence=conf,
                        bbox=(x0, y0, x1, y1),
                        center_x=(x0 + x1) / 2,
                        center_y=(y0 + y1) / 2,
                    )
                )

        # Old PaddleOCR list format
        elif isinstance(data, list):
            for item in data:
                try:
                    box = item[0]
                    text, conf = item[1]
                    text = str(text).strip()
                    if not text:
                        continue

                    xs = [p[0] for p in box]
                    ys = [p[1] for p in box]

                    x0, y0 = min(xs), min(ys)
                    x1, y1 = max(xs), max(ys)

                    tokens.append(
                        OCRToken(
                            text=text,
                            confidence=float(conf),
                            bbox=(x0, y0, x1, y1),
                            center_x=(x0 + x1) / 2,
                            center_y=(y0 + y1) / 2,
                        )
                    )
                except Exception:
                    continue

        tokens.sort(key=lambda t: (t.center_y, t.center_x))
        return tokens

    # -------------------------------------------------
    # MULTI PAGE
    # -------------------------------------------------
    def extract_from_images(self, images: List[Image.Image]) -> OCRResult:
        all_tokens: List[OCRToken] = []
        texts, confs = [], []

        for idx, img in enumerate(images, 1):
            res = self.extract_from_image(img)
            if res.text:
                texts.append(f"\n--- PAGE {idx} ---\n{res.text}")
                confs.append(res.confidence)
                all_tokens.extend(res.tokens)

        combined = "\n".join(texts)
        avg_conf = sum(confs) / len(confs) if confs else 0.0

        return OCRResult(
            text=combined,
            confidence=avg_conf,
            char_count=len(combined),
            word_count=len(combined.split()) if combined else 0,
            line_count=len(texts),
            tokens=all_tokens,
        )


# =====================================================
# SINGLETON
# =====================================================
_paddle_ocr_service: PaddleOCRService | None = None


def get_paddle_ocr_service() -> PaddleOCRService:
    global _paddle_ocr_service
    if _paddle_ocr_service is None:
        _paddle_ocr_service = PaddleOCRService()
    return _paddle_ocr_service
