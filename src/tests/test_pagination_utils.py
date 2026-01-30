import pytest

from app.pagination import PaginationError, build_links, parse_pagination


def test_parse_pagination_defaults():
    page, page_size = parse_pagination({})
    assert page == 1
    assert page_size == 10


@pytest.mark.parametrize("query", [{"page": "0"}, {"page": 0}])
def test_parse_pagination_page_invalid(query):
    with pytest.raises(PaginationError):
        parse_pagination(query)


@pytest.mark.parametrize("query", [{"page_size": "0"}, {"page_size": 0}, {"page_size": "51"}])
def test_parse_pagination_page_size_invalid(query):
    with pytest.raises(PaginationError):
        parse_pagination(query)


def test_build_links_with_total():
    links = build_links("/films", page=1, page_size=10, q=None, total=11)
    assert links["self"] == "/films?page=1&page_size=10"
    assert links["next"] == "/films?page=2&page_size=10"
    assert links["prev"] is None

    links2 = build_links("/films", page=2, page_size=10, q=None, total=11)
    assert links2["prev"] == "/films?page=1&page_size=10"
    assert links2["next"] is None
