# Paginação e filtros

## Query params suportados
Implementação: `src/app/pagination.py`

- `page`: int >= 1
- `page_size`: int 1..50
- `q`: string

`links.self/next/prev` são gerados por `build_links()`.

---

## SWAPI pagina em 10: "window pagination"
A SWAPI entrega `results` em páginas fixas de 10 (`page=1..N`).  
Este projeto implementa uma "janela" (`page_size` até 50) buscando **somente** as páginas upstream necessárias.

Implementação: `src/app/swapi_window.py`
- `UPSTREAM_PAGE_SIZE = 10`
- calcula `up_start/up_end` para cobrir o range solicitado
- busca páginas SWAPI e recorta a janela final

### Observação importante (comportamento real da SWAPI)
O código trata que a SWAPI pode retornar **404** quando `page` está fora do range (em vez de `results=[]`).
- Para listagens, isso é interpretado como "fim da lista".
- Se ocorrer no primeiro upstream page (`up_start`), o erro sobe (porque o request foi inválido para aquele range).

---

## Onde window pagination é usada
- `people`, `planets`, `starships`: usam `fetch_window()`
- `films`: faz **uma única chamada** e pagina localmente (lista pequena)

---

## Filtro `q`
- Listagens (`people/planets/starships/films`):
  - `q` é mapeado para `search` na SWAPI (`params["search"] = q`)
- Correlacionados (`characters/residents`):
  - `q` é filtro local por substring em `name`, aplicado **após** montar a janela paginada.
  - trade-off: `total` continua sendo o total de URLs do relacionamento, não o total pós-filtro.
