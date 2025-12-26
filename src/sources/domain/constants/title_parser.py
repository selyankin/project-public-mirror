import re
from typing import Final

AREA_PATTERN: Final[re.Pattern[str]] = re.compile(
    r'(?P<value>\d+(?:[.,]\d+)?)\s*(?:м²|м2|кв\.?\s*м)',
    flags=re.IGNORECASE,
)

FLOORS_PATTERN: Final[re.Pattern[str]] = re.compile(
    r'(?:этаж\s*)?(?P<current>\d+)\s*/\s*(?P<total>\d+)\s*(?:эт\.?|этаж)?',
    flags=re.IGNORECASE,
)
