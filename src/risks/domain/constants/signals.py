from src.risks.domain.signals_catalog import SignalDefinition

DEFINITIONS: dict[str, SignalDefinition] = {
    'address_incomplete': SignalDefinition(
        {
            'code': 'address_incomplete',
            'title': 'Incomplete address',
            'description': (
                'The provided address looks incomplete for reliable checks'
            ),
            'severity': 'medium',
        },
    ),
    'possible_apartments': SignalDefinition(
        {
            'code': 'possible_apartments',
            'title': 'Possible apartments',
            'description': (
                'Address text may indicate apartments; '
                'legal status may differ'
            ),
            'severity': 'medium',
        },
    ),
    'hostel_keyword': SignalDefinition(
        {
            'code': 'hostel_keyword',
            'title': 'Hostel / dormitory indication',
            'description': 'Address text may indicate a dormitory format',
            'severity': 'high',
        },
    ),
    'residential_complex_hint': SignalDefinition(
        {
            'code': 'residential_complex_hint',
            'title': 'Residential complex mentioned',
            'description': (
                'The query mentions a residential complex; '
                'verify developer and project data'
            ),
            'severity': 'low',
        },
    ),
    'url_not_supported_yet': SignalDefinition(
        {
            'code': 'url_not_supported_yet',
            'title': 'URL checks are not supported yet',
            'description': (
                'The provided URL cannot be processed at the moment'
            ),
            'severity': 'low',
        },
    ),
    'query_type_not_supported': SignalDefinition(
        {
            'code': 'query_type_not_supported',
            'title': 'Query type is not supported yet',
            'description': (
                'This query type is not supported in the current version'
            ),
            'severity': 'low',
        },
    ),
    'query_not_address_like': SignalDefinition(
        {
            'code': 'query_not_address_like',
            'title': 'Query is not address-like',
            'description': ('The provided text does not look like an address'),
            'severity': 'medium',
        },
    ),
}

ORDERED_CODES: tuple[str, ...] = (
    'address_incomplete',
    'possible_apartments',
    'hostel_keyword',
    'residential_complex_hint',
    'url_not_supported_yet',
    'query_type_not_supported',
    'query_not_address_like',
)
