"""Исключения домена отчётов."""


class ReportDomainError(Exception):
    """Базовая ошибка домена отчётов."""


class ReportNotFoundError(ReportDomainError):
    """Отчёт не найден."""


class CheckResultNotFoundError(ReportDomainError):
    """Снимок проверки по check_id не найден."""
