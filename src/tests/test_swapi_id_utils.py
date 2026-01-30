import pytest

from clients.utils import InvalidSwapiUrl, attach_id, extract_id


@pytest.mark.parametrize(
    "url, expected",
    [
        ("https://swapi.dev/api/people/1/", 1),
        ("https://swapi.dev/api/planets/10/", 10),
        ("https://swapi.dev/api/starships/12/", 12),
        ("https://swapi.dev/api/films/2", 2),
    ],
)
def test_extract_id_success(url, expected):
    assert extract_id(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        "",
        None,
        "https://swapi.dev/api/people/",         # sem id
        "https://swapi.dev/api/people/abc/",     # id não numérico
        "/people/1/",                             # faltou /api/
        "https://swapi.dev/api/people/1/extra",  # extra path
    ],
)
def test_extract_id_invalid(url):
    with pytest.raises(InvalidSwapiUrl):
        extract_id(url)  # type: ignore[arg-type]
        

def test_attach_id_returns_new_dict_and_keeps_fields():
    original = {"name": "Luke", "url": "https://swapi.dev/api/people/1/"}
    out = attach_id(original)

    assert out["id"] == 1
    assert out["name"] == "Luke"
    assert out["url"] == original["url"]
    assert out is not original
    assert "id" not in original  # não mutou
