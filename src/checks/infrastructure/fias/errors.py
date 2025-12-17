"""Исключения транспортного слоя ФИАС."""


class FiasError(Exception):
    """Базовое исключение клиента ФИАС."""


class FiasTimeoutError(FiasError):
    """Сетевая операция превысила таймаут."""


class FiasTransportError(FiasError):
    """Ошибка транспорта при обращении к ФИАС."""


class FiasServerError(FiasError):
    """Сервер ФИАС вернул 500."""

    def __init__(self, description: str) -> None:
        """Сохранить описание ошибки ФИАС."""

        self.description = description
        super().__init__(description)


class FiasUnexpectedStatus(FiasError):
    """Сервер вернул неожиданный статус."""

    def __init__(self, status_code: int, body_snippet: str) -> None:
        """Сохранить описание неожиданного ответа."""

        self.status_code = status_code
        self.body_snippet = body_snippet
        message = f'FIAS status {status_code}: {body_snippet}'
        super().__init__(message)
