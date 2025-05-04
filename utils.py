import re
from datetime import datetime
from typing import List, Optional

DATE_PATTERNS = [
    r"\b(\d{4}-\d{2}-\d{2})\b",
    r"\b(\d{2}/\d{2}/\d{4})\b"
]

def extract_date(text: str) -> Optional[datetime]:
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, text)
        if match:
            try:
                return datetime.fromisoformat(match.group(1))
            except ValueError:
                pass
    return None

def extract_tags(text: str) -> List[str]:
    return re.findall(r"#(\w+)", text)
