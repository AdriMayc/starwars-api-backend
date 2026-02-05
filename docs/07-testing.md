# Testes

## Backend (pytest + respx)

Config: `pytest.ini` aponta `testpaths = src/tests` e `pythonpath = src`.

Rodar:
```bash
pytest -q
```

### O que está coberto no repo (arquivos reais)

Router:

- `test_router_health.py`
- `test_router_path_params.py`

CORS:

- `test_cors.py`

Envelope (Pydantic):

- `test_envelope_models.py`

Paginação (parse + links):

- `test_pagination.py`
- `test_pagination_utils.py`

Window pagination SWAPI:

- `test_swapi_window.py`

SWAPI client (timeout/retry/status/json):

- `test_swapi_client.py`

Cache TTL get_by_url:

- `test_swapi_cache.py`

ID attach util:

- `test_swapi_id_utils.py`

Handlers:

- `test_films_list.py`, `test_people_list.py`, `test_planets_list.py`, `test_starships_list.py`
- correlacionados: `test_film_characters.py`, `test_planet_residents.py`

---

## Frontend (Vitest)

Config:

`frontend/vite.config.ts` usa `environment: "jsdom"` e `setupFiles`.

Rodar:

```bash
cd frontend
npm run test
# ou
npm run test:run
```

### Cobertura relevante:

`frontend/src/utils/api.test.ts`:

- cache TTL (segunda chamada não chama fetch)
- dedupe (duas chamadas concorrentes = 1 fetch)
- abort por consumidor (um aborta, outro continua e preenche cache)

`frontend/src/App.test.tsx` (smoke)

### Detalhes

- API key no frontend não é segredo (exposição é esperada).
- Mitigação: restrição por HTTP Referrer + quota/rate limit no Gateway; alternativa: proxy server-side (Vercel function).