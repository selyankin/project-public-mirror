import re
from typing import Final

WHITESPACE_RE: Final[re.Pattern[str]] = re.compile(r"\s+")
COMMA_RE: Final[re.Pattern[str]] = re.compile(r"\s*,\s*")
