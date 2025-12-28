"""Проверка StubRosreestrClient."""

from sources.rosreestr.stub_client import ROSREESTR_FIXTURE, StubRosreestrClient


def test_stub_get_object_found():
    client = StubRosreestrClient()
    response = client.get_object(
        cadastral_number=list(ROSREESTR_FIXTURE.keys())[0]
    )
    assert response.found is True
    assert response.object is not None
    assert response.object.cadNumber == list(ROSREESTR_FIXTURE.keys())[0]


def test_stub_get_object_not_found():
    client = StubRosreestrClient()
    response = client.get_object(cadastral_number='random')
    assert response.found is False
    assert response.object is None


def test_stub_find_cadastrals_by_address():
    client = StubRosreestrClient()
    result = client.find_cadastrals(address='г. Москва')
    assert result == list(ROSREESTR_FIXTURE.keys())
    assert client.find_cadastrals(address='   ') == []
