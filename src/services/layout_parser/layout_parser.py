from typing import List
from .models import OCRLine, LineType


class LayoutParser:
    """
    Minimal layout parser.
    Şimdilik her satırı TABLE_ROW olarak işaretler.
    """

    def parse(self, ocr_result) -> List[OCRLine]:
        lines: List[OCRLine] = []

        for text in ocr_result.text.splitlines():
            if not text.strip():
                continue

            lines.append(
                OCRLine(
                    text=text.strip(),
                    line_type=LineType.TABLE_ROW
                )
            )

        return lines
