import re

PRELOADED_PATTERN = re.compile(
    r'window\.__preloadedState__\s*=\s*(\{.*?\})\s*;',
    flags=re.DOTALL,
)
