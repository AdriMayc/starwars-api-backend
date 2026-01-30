# src/clients/utils.py
from __future__ import annotations

import re


# Ex.: https://swapi.dev/api/people/1/
# Ex.: http://swapi.dev/api/films/2
_ID_RE = re.compile(r"/api/(?P<resource>[a-zA-Z_]+)/(?P<id>\d+)/?$")


class InvalidSwapiUrl(ValueError):
    """URL da SWAPI inválida para extração de ID."""


def extract_id(url: str) -> int:
    """
    Extrai o ID numérico do campo `url` retornado pela SWAPI.

    Regras:
    - aceita com ou sem trailing slash
    - exige padrão /api/<resource>/<id>[/]
    - retorna int (não str)
    """
    if not url or not isinstance(url, str):
        raise InvalidSwapiUrl("URL must be a non-empty string")

    m = _ID_RE.search(url.strip())
    if not m:
        raise InvalidSwapiUrl(f"Cannot extract id from url: {url}")

    return int(m.group("id"))


def attach_id(item: dict) -> dict:
    """
    Retorna um novo dict com `id` derivado de `item["url"]`.
    - não muta o dict original (evita efeitos colaterais em testes)
    """
    if not isinstance(item, dict):
        raise TypeError("item must be a dict")

    url = item.get("url")
    item_id = extract_id(url)
    return {**item, "id": item_id}
