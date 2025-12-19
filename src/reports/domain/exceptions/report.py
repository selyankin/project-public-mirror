"""Исключения домена отчётов."""


class ReportDomainError(Exception):
    """Базовая ошибка домена отчётов."""


class ReportNotFoundError(ReportDomainError):
    """Отчёт не найден."""


class CheckResultNotFoundError(ReportDomainError):
    """Снимок проверки по check_id не найден."""


class ReportModuleError(ReportDomainError):
    """Ошибка, связанная с модулями отчёта."""


class ReportModuleNotFoundError(ReportModuleError):
    """Запрошенный модуль не зарегистрирован."""

    def __init__(self, module_id: str) -> None:
        super().__init__(f'unknown module: {module_id}')
        self.module_ids = [module_id]


class ReportModulePaymentRequiredError(ReportModuleError):
    """Оплачиваемый модуль недоступен без оплаты."""

    def __init__(self, module_id: str) -> None:
        super().__init__(f'payment required for module: {module_id}')
        self.module_ids = [module_id]


class ReportInvalidModulesError(ReportModuleError):
    """Неверно задан список модулей."""

    def __init__(
        self,
        message: str,
        module_ids: list[str] | None = None,
    ) -> None:
        super().__init__(message)
        self.module_ids = module_ids or []
