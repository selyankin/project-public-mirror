"""Построение ключей идемпотентности для проверок."""

from __future__ import annotations

import hashlib
import json
from typing import Literal


def build_check_cache_key(
    *,
    input_kind: Literal['address', 'url'],
    input_value: str,
    fias_mode: str,
    version: str = 'v1',
    address_type: int = 1,
) -> str:
    """Построить детерминированный ключ кэша проверки адреса."""

    payload = {
        'kind': input_kind,
        'value': input_value,
        'fias_mode': fias_mode,
        'version': version,
        'address_type': address_type,
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()
