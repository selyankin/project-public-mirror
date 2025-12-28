"""Заглушка клиента Росреестра."""

from __future__ import annotations

from sources.rosreestr.constants.stub import ROSREESTR_FIXTURE
from sources.rosreestr.dto import RosreestrApiResponse
from sources.rosreestr.ports import RosreestrClientPort


class StubRosreestrClient(RosreestrClientPort):
    """Возвращает заранее подготовленные ответы."""

    __slots__ = ()

    def get_object(self, *, cadastral_number: str) -> RosreestrApiResponse:
        """Вернуть фиктивный объект по кадастровому номеру."""

        if cadastral_number in ROSREESTR_FIXTURE:
            return RosreestrApiResponse(
                status=200,
                found=True,
                object=ROSREESTR_FIXTURE[cadastral_number],
            )

        return RosreestrApiResponse(status=200, found=False, object=None)
