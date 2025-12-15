from src.risks.domain.constants.signals import DEFINITIONS, ORDERED_CODES
from src.risks.domain.signals_catalog import SignalDefinition


def get_signal_definition(code: str) -> SignalDefinition:
    """Return signal definition by code."""

    try:
        return DEFINITIONS[code]
    except KeyError as exc:
        raise KeyError(f"Signal definition not found: {code!r}") from exc


def all_signal_definitions() -> tuple[SignalDefinition, ...]:
    """Return all signal definitions in stable order."""

    return tuple(DEFINITIONS[code] for code in ORDERED_CODES)
