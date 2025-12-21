# Flaffy


## Database migrations

Alembic is configured for async SQLAlchemy. Use the standard commands:

```
alembic revision --autogenerate -m 'short message'
alembic upgrade head
```

The DSN is taken from the `DB_DSN`/`DATABASE_URL` environment variables, so
no credentials are stored in `alembic.ini`. When the application runs with
`STORAGE_MODE=db`, you must provide `DB_DSN` explicitly via the environment.

## FIAS integration

The default setup uses the stub client. To call the real FIAS API, provide:

- `FIAS_MODE=api`
- `FIAS_BASE_URL=https://<fias-host>`
- `FIAS_TOKEN=<api token>`
- optional tuning: `FIAS_SUGGEST_ENDPOINT`, `FIAS_TIMEOUT_SECONDS`,
  `FIAS_RETRIES`, `FIAS_RETRY_BACKOFF_SECONDS`, `FIAS_CONCURRENCY_LIMIT`

After enabling the API mode, the `/v1/check` endpoint returns an extra block:

```json
{
  "score": 0,
  "level": "LOW",
  "signals": [],
  "address_confidence": "high",
  "address_source": "fias",
  "check_id": "c50c7e5c-1c0d-4fdd-a7fd-7a8060adfe66",
  "fias": {
    "source_query": "г. Москва, ул. Тверская, 1",
    "normalized": "г. москва, ул. тверская, д. 1",
    "fias_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "confidence": 0.95
  }
}
```

In environments without credentials the service falls back to the stub client.

## Reports modules

The `/v1/reports` endpoint accepts a list of module ids. When omitted the
request defaults to `['base_summary', 'address_quality']`. Available modules:

- `base_summary` — краткое резюме по проверке (обязательный минимум)
- `address_quality` — дополнительные данные о нормализации адреса
- `risk_signals` — перечень всех активных сигналов
- `fias_normalization` — расширенный FIAS-блок (платный, зависит от первых двух)

Module validation is strict: unknown ids or an empty list produce HTTP 400
with a response such as:

```json
{
  "detail": {
    "message": "unknown module: risk_ai",
    "modules": ["risk_ai"]
  }
}
```

Paid modules require enabling `REPORTS_ALLOW_PAID_MODULES=true`; otherwise
the API returns HTTP 402 with a similar payload. Example request body:

```json
{
  "check_id": "1f394e39-5082-4cae-b2da-1c53aae4cdd6",
  "modules": ["base_summary", "address_quality"]
}
```

## Integration tests

End-to-end tests live under `tests/integration` and run the real FastAPI app
with Postgres and the FIAS stub client. To execute them:

1. Provide a reachable Postgres DSN via `DB_DSN`, for example
   `export DB_DSN=postgresql+asyncpg://postgres:postgres@localhost:5432/flaffy`.
2. Run `pytest -m integration`.

Fixtures automatically apply Alembic migrations and truncate the tables before
each test, so the flow `/v1/check -> /v1/reports` remains deterministic. Paid
modules are disabled by default; set `REPORTS_ALLOW_PAID_MODULES=true` in your
environment (or `.env`) if you want to experiment with them locally. See the
section above for the list of available module ids.
