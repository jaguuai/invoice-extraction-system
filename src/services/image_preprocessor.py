"""
Image Preprocessor - STRONG + SAFE VERSION
Deskew guarded to prevent 90° disasters
"""
import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from dataclasses import dataclass
from typing import List

from src.core.logging import logger


@dataclass
class PreprocessingResult:
    original: Image.Image
    processed: Image.Image
    enhancements: List[str]
    quality_score: float


class ImagePreprocessor:
    """Powerful but SAFE preprocessing for OCR"""

    def preprocess(self, image: Image.Image) -> PreprocessingResult:
        enhancements = []

        # 1️⃣ grayscale
        img = image.convert("L")

        # 2️⃣ contrast
        img = ImageEnhance.Contrast(img).enhance(2.2)
        enhancements.append("contrast_boost")

        # 3️⃣ sharpen
        img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
        enhancements.append("sharpen")

        cv_img = np.array(img)

        # 4️⃣ adaptive threshold (keep moderate)
        cv_img = cv2.adaptiveThreshold(
            cv_img, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31, 11
        )
        enhancements.append("adaptive_threshold")

        # 5️⃣ denoise
        cv_img = cv2.fastNlMeansDenoising(cv_img, h=20)
        enhancements.append("denoise")

        # -------------------------------
        # 6️⃣ SAFE DESKEW (GUARDED)
        # -------------------------------
        angle = 0.0
        try:
            coords = np.column_stack(np.where(cv_img < 255))
            if len(coords) > 500:  # enough signal
                raw_angle = cv2.minAreaRect(coords)[-1]

                if raw_angle < -45:
                    angle = -(90 + raw_angle)
                else:
                    angle = -raw_angle

                # 🚨 GUARD
                if abs(angle) <= 5.0:
                    (h, w) = cv_img.shape[:2]
                    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
                    cv_img = cv2.warpAffine(cv_img, M, (w, h), borderValue=255)
                    enhancements.append(f"deskew_{angle:.2f}")
                else:
                    enhancements.append(f"deskew_skipped_{angle:.1f}")

        except Exception as e:
            logger.warning(f"Deskew failed safely: {e}")

        # back to PIL
        final_img = Image.fromarray(cv_img)

        # 7️⃣ quality score
        sharp = cv2.Laplacian(cv_img, cv2.CV_64F).var()
        contrast = cv_img.std()
        quality = min((sharp / 120) * 0.6 + (contrast / 90) * 0.4, 1.0)

        logger.info(
            f"🛠 Preprocessed Image → Enhancements={enhancements}, Quality={quality:.2f}"
        )

        return PreprocessingResult(
            original=image,
            processed=final_img,
            enhancements=enhancements,
            quality_score=quality
        )


_image_preprocessor = None

def get_image_preprocessor() -> ImagePreprocessor:
    global _image_preprocessor
    if _image_preprocessor is None:
        _image_preprocessor = ImagePreprocessor()
    return _image_preprocessor
