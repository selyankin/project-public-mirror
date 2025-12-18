"""Базовый класс декларативных моделей SQLAlchemy."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Общий Declarative Base для всех ORM-моделей."""

    pass
