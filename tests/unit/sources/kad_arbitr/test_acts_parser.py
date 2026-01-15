"""Проверка парсинга актов из HTML kad.arbitr.ru."""

from sources.kad_arbitr.acts_parser import parse_case_acts_html


def test_parse_case_acts_html_extracts_pdf_links() -> None:
    html = (
        '<html><body>'
        '<a href="https://kad.arbitr.ru/Document/Pdf/123/456/act.pdf'
        '?isAddStamp=True">Решение 10.01.2026</a>'
        '<a href="https://kad.arbitr.ru/Document/Pdf/123/789/act2.pdf'
        '?isAddStamp=True">Определение 05.12.2025</a>'
        '</body></html>'
    )

    result = parse_case_acts_html(case_id='123', html=html)

    assert len(result.acts) == 2
    assert result.acts[0].act_id == '456'
    assert result.acts[0].act_type == 'decision'
    assert result.acts[0].act_date is not None
    assert result.acts[0].pdf_url is not None
    assert 'Document/Pdf' in result.acts[0].pdf_url
    assert result.acts[1].act_id == '789'
    assert result.acts[1].act_type == 'determination'


def test_parse_case_acts_html_handles_empty() -> None:
    result = parse_case_acts_html(case_id='123', html='')

    assert result.acts == []
