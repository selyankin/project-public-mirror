"""Заглушка клиента ФИАС для локальной разработки."""

from __future__ import annotations

from typing import Any

from checks.application.ports.fias_client import NormalizedAddress


class StubFiasClient:
    """Возвращает фиктивные ответы для предсказуемых запросов."""

    __slots__ = ()

    async def normalize_address(self, query: str) -> NormalizedAddress | None:
        """Детерминированный ответ для ограниченного набора запросов."""

        normalized = self._match(query)
        if normalized is None:
            return None

        return NormalizedAddress(
            source_query=query,
            normalized=normalized['normalized'],
            fias_id=normalized['fias_id'],
            confidence=normalized['confidence'],
            raw={
                'matched': normalized['normalized'],
                'rule': normalized['rule'],
            },
            fias_houseguid=normalized.get('fias_houseguid'),
            fias_aoguid=normalized.get('fias_aoguid'),
            postal_code=normalized.get('postal_code'),
            region_code=normalized.get('region_code'),
        )

    @staticmethod
    def _match(query: str) -> dict[str, Any] | None:
        lowered = query.lower()
        if 'москва' in lowered:
            return {
                'normalized': 'г. москва, ул. тверская, д. 1',
                'fias_id': 'moscow-001',
                'confidence': 0.95,
                'rule': 'contains:москва',
                'fias_houseguid': 'moscow-house-001',
                'fias_aoguid': 'moscow-ao-001',
                'postal_code': '101000',
                'region_code': '77',
            }

        if 'санкт-петербург' in lowered or 'спб' in lowered:
            return {
                'normalized': 'г. санкт-петербург, невский пр-т, д. 10',
                'fias_id': 'spb-010',
                'confidence': 0.9,
                'rule': 'contains:spb',
                'fias_houseguid': 'spb-house-010',
                'postal_code': '190000',
                'region_code': '78',
            }

        return None

    @staticmethod
    def search_address_item(value: str) -> dict[str, str]:
        """Совместимость со старым синхронным интерфейсом."""

        return {'value': value}
