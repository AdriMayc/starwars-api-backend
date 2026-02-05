# Segurança

## API Key no Gateway (x-api-key)
Arquivo: `openapi-gateway.yaml`

- `securitySchemes.api_key`:
  - type: `apiKey`
  - in: `header`
  - name: `x-api-key`
- `security` global aplica em todas as rotas.

## Restrição por referrer (browser)
Como o consumidor é um SPA (browser), a mitigação correta para exposição de key é:
- restringir a API Key no GCP por **HTTP referrer** (domínio da Vercel).

## CORS
Implementação: `src/app/main.py`
- Preflight `OPTIONS` retorna 204 e headers:
  - `Access-Control-Allow-Methods: GET,OPTIONS`
  - `Access-Control-Allow-Headers: accept,content-type,x-api-key,x-request-id`
  - `Access-Control-Allow-Origin`: ecoa `Origin` se existir; caso contrário usa `*`
  - `Vary: Origin`
