from pydantic import BaseModel


class CheckIn(BaseModel):
    """Унифицированный входной запрос."""

    type: str
    query: str


class LegacyCheckIn(BaseModel):
    """Устаревший формат входа с адресом."""

    address: str
