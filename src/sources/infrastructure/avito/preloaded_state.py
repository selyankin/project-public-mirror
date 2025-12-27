"""Утилита извлечения window.__preloadedState__ из HTML."""

from __future__ import annotations

from sources.domain.exceptions import ListingParseError

MARKER = 'window.__preloadedState__'


def extract_preloaded_state_json(html: str) -> str:
    """Вернуть JSON из window.__preloadedState__."""

    marker_idx = html.find(MARKER)
    if marker_idx == -1:
        raise ListingParseError('preloaded state not found')

    eq_idx = html.find('=', marker_idx + len(MARKER))
    if eq_idx == -1:
        raise ListingParseError('preloaded state assignment not found')

    brace_idx = html.find('{', eq_idx)
    if brace_idx == -1:
        raise ListingParseError('preloaded state json not found')

    return _extract_braced_object(html, brace_idx)


def _extract_braced_object(text: str, start_idx: int) -> str:
    """Извлечь JSON-объект с балансом фигурных скобок."""

    depth = 0
    in_string = False
    escaped = False

    for idx in range(start_idx, len(text)):
        char = text[idx]
        if in_string:
            if escaped:
                escaped = False
                continue

            if char == '\\':
                escaped = True
                continue

            if char == '"':
                in_string = False

            continue

        if char == '"':
            in_string = True
            continue

        if char == '{':
            depth += 1

        elif char == '}':
            depth -= 1
            if depth == 0:
                return text[start_idx : idx + 1]

    raise ListingParseError('unterminated preloaded state json')
