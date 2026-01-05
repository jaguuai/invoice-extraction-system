from dataclasses import dataclass
from enum import Enum
from typing import List


class LineType(str, Enum):
    TABLE_ROW = "table_row"
    UNKNOWN = "unknown"


@dataclass
class OCRLine:
    text: str
    line_type: LineType
