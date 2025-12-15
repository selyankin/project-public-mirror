from risks.domain.signals_catalog import SignalDefinition

DEFINITIONS: dict[str, SignalDefinition] = {
    "address_incomplete": SignalDefinition(
        {
            "code": "address_incomplete",
            "title": "Incomplete address",
            "description": (
                "The provided address looks incomplete for reliable checks"
            ),
            "severity": "medium",
        },
    ),
    "possible_apartments": SignalDefinition(
        {
            "code": "possible_apartments",
            "title": "Possible apartments",
            "description": (
                "Address text may indicate apartments; "
                "legal status may differ"
            ),
            "severity": "medium",
        },
    ),
    "hostel_keyword": SignalDefinition(
        {
            "code": "hostel_keyword",
            "title": "Hostel / dormitory indication",
            "description": "Address text may indicate a dormitory format",
            "severity": "high",
        },
    ),
    "residential_complex_hint": SignalDefinition(
        {
            "code": "residential_complex_hint",
            "title": "Residential complex mentioned",
            "description": (
                "The query mentions a residential complex; "
                "verify developer and project data"
            ),
            "severity": "low",
        },
    ),
}

ORDERED_CODES: tuple[str, ...] = (
    "address_incomplete",
    "possible_apartments",
    "hostel_keyword",
    "residential_complex_hint",
)
