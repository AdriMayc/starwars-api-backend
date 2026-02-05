# Observabilidade e erros

## request_id
- O backend lê `x-request-id` do header; se não vier, gera UUID.
- O request_id aparece em `meta.request_id` do envelope.

Implementação: `src/app/main.py` + `src/schemas/common.py`

---

## Códigos de erro (implementação real)
Os handlers retornam `errors: [ {code, message, details?} ]` e status coerente.

Principais códigos usados:
- `VALIDATION_ERROR` (page/page_size inválidos)
- `NOT_FOUND` (rota inexistente no router)
- `METHOD_NOT_ALLOWED` (router)
- `UPSTREAM_TIMEOUT` (timeout SWAPI)
- `UPSTREAM_BAD_RESPONSE` (JSON inválido ou erro ao parsear)
- `UPSTREAM_NOT_FOUND` (SWAPI 404)
- `UPSTREAM_ERROR` (SWAPI 429/5xx ou 4xx não-429)

Mapeamento típico de HTTP:
- 400: validação query
- 404: rota inexistente (router) / recurso inexistente (upstream)
- 405: método não permitido
- 502: erro upstream / resposta inválida
- 504: timeout upstream
