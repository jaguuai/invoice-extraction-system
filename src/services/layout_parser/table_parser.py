from dataclasses import dataclass
from typing import List, Dict
import re

from src.services.paddle_ocr_service import OCRToken


@dataclass
class InvoiceItem:
    description: str
    quantity: int
    unit_price: float
    total_price: float
    confidence: float


class BBoxTableParser:
    """
    Bounding-box based invoice table parser
    Delivery-safe version
    """

    HEADER_KEYWORDS = {
        "tarih", "vergi", "daire", "sayın", "seri",
        "irsaliye", "toplam", "kdv", "genel",
        "no", "vd"
    }

    def parse(self, tokens: List[OCRToken], page_width: float) -> List[InvoiceItem]:
        rows = self._group_rows(tokens)
        items: List[InvoiceItem] = []

        for row in rows:
            item = self._parse_row(row, page_width)
            if item:
                items.append(item)

        return items

    # -------------------------------------------------

    def _group_rows(self, tokens: List[OCRToken], y_threshold: float = 12) -> List[List[OCRToken]]:
        rows: List[List[OCRToken]] = []

        for tok in sorted(tokens, key=lambda t: t.center_y):
            placed = False
            for row in rows:
                if abs(row[0].center_y - tok.center_y) < y_threshold:
                    row.append(tok)
                    placed = True
                    break
            if not placed:
                rows.append([tok])

        return rows

    # -------------------------------------------------

    def _parse_row(self, row: List[OCRToken], page_width: float) -> InvoiceItem | None:
        text_joined = " ".join(t.text.lower() for t in row)

        # 🚫 HEADER / METADATA FILTER
        if any(k in text_joined for k in self.HEADER_KEYWORDS):
            return None

        cols: Dict[str, List[str]] = {
            "desc": [],
            "qty": [],
            "unit": [],
            "total": []
        }

        for tok in row:
            text = tok.text.strip()
            if not text:
                continue

            x_ratio = tok.center_x / page_width

            if x_ratio < 0.35:
                cols["desc"].append(text)
            elif x_ratio < 0.50:
                cols["qty"].append(text)
            elif x_ratio < 0.70:
                cols["unit"].append(text)
            else:
                cols["total"].append(text)

        # must look like a real row
        if not cols["desc"] or not cols["unit"] or not cols["total"]:
            return None

        description = " ".join(cols["desc"])
        description = description.replace("Örün", "Ürün").replace("0rün", "Ürün")

        qty = self._safe_number(cols["qty"], default=1, cast=int)
        unit_price = self._safe_number(cols["unit"])
        total_price = self._safe_number(cols["total"])

        if qty <= 0 or unit_price <= 0 or total_price <= 0:
            return None

        diff = abs(qty * unit_price - total_price)
        confidence = 0.95 if diff < 1 else 0.85

        return InvoiceItem(
            description=description,
            quantity=qty,
            unit_price=unit_price,
            total_price=total_price,
            confidence=confidence
        )

    # -------------------------------------------------

    def _safe_number(self, parts: List[str], default: float = 0.0, cast=float):
        joined = " ".join(parts)
        nums = re.findall(r"\d+(?:[.,]\d+)?", joined)
        if not nums:
            return default
        try:
            return cast(nums[0].replace(",", "."))
        except Exception:
            return default
