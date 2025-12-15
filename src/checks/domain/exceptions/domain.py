class DomainValidationError(ValueError):
    """Raised when domain invariants fail."""


class QueryInputError(ValueError):
    """Ошибка валидации входного запроса проверки."""
