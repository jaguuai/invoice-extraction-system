import unicodedata
from collections import Counter
import difflib


class OCRNormalizer:
    """
    OCR sonrası EVRENSEL metin temizleme katmanı
    - Dil kuralı yok
    - Keyword yok
    - LLM yok
    """

    def normalize(self, text: str) -> str:
        if not text:
            return text

        # 1️⃣ Unicode normalization (Ş, Ü, İ kurtarılır)
        text = unicodedata.normalize("NFC", text)

        lines = text.splitlines()

        # 2️⃣ Kırık satırları birleştir (Ş + ule → Şule)
        lines = self._merge_broken_lines(lines)

        # 3️⃣ Kelime bazlı çoğunluk oylaması (Ürün / Orün / Örün)
        words = " ".join(lines).split()
        words = self._majority_vote(words)

        return " ".join(words)

    def _merge_broken_lines(self, lines):
        merged = []
        buffer = ""

        for line in lines:
            line = line.strip()
            if len(line) <= 2:
                buffer += line
            else:
                if buffer:
                    merged.append(buffer + " " + line)
                    buffer = ""
                else:
                    merged.append(line)

        if buffer:
            merged.append(buffer)

        return merged

    def _majority_vote(self, words):
        counter = Counter(words)
        canonical = {}

        for w in counter:
            if w in canonical:
                continue

            group = [
                other for other in counter
                if difflib.SequenceMatcher(None, w, other).ratio() > 0.85
            ]

            winner = max(group, key=lambda x: counter[x])

            for g in group:
                canonical[g] = winner

        return [canonical[w] for w in words]
