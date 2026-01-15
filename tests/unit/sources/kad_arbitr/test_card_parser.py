"""Проверка парсинга HTML карточки дела kad.arbitr.ru."""

from sources.kad_arbitr.card_parser import parse_case_card_html


def test_parse_case_card_html_extracts_case_number_and_participants() -> None:
    html = (
        '<html><body>'
        '<div>Дело № А40-1/2025</div>'
        '<div>Арбитражный суд города Москвы</div>'
        '<div>Истец: ООО Ромашка ИНН 7701234567 ОГРН 1027700123456</div>'
        '<div>Ответчик: ООО Лютик ИНН 7712345678</div>'
        '</body></html>'
    )

    result = parse_case_card_html(case_id='123', html=html)

    assert result.case_number == 'А40-1/2025'
    assert result.court == 'Арбитражный суд города Москвы'
    assert len(result.participants) == 2
    assert result.participants[0].role == 'plaintiff'
    assert result.participants[0].inn == '7701234567'
    assert result.participants[0].ogrn == '1027700123456'
    assert result.participants[1].role == 'defendant'
    assert result.participants[1].inn == '7712345678'


def test_parse_case_card_html_extracts_inn_ogrn_from_next_line() -> None:
    html = (
        '<html><body>'
        '<div>Истец: ООО Ромашка</div>'
        '<div>ИНН: 7701234567, ОГРН: 1027700123456</div>'
        '</body></html>'
    )

    result = parse_case_card_html(case_id='123', html=html)

    assert result.participants[0].inn == '7701234567'
    assert result.participants[0].ogrn == '1027700123456'


def test_parse_case_card_html_handles_missing_fields() -> None:
    html = '<html><body>Нет данных</body></html>'

    result = parse_case_card_html(case_id='missing', html=html)

    assert result.case_number is None
    assert result.court is None
    assert result.participants == []
