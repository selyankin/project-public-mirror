from pydantic import BaseModel


class CheckIn(BaseModel):
    """Incoming payload with raw address."""

    address: str
