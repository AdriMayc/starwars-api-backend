from app.pagination import build_self_url, build_links

def test_build_self_url_encodes_query():
    url = build_self_url("/people", {"page": 1, "page_size": 10, "q": "Luke Skywalker"})
    assert url == "/people?page=1&page_size=10&q=Luke+Skywalker"

def test_build_links_next_prev_with_total():
    links = build_links("/films", page=1, page_size=5, q=None, total=6)
    assert links["self"] == "/films?page=1&page_size=5"
    assert links["next"] == "/films?page=2&page_size=5"
    assert links["prev"] is None
