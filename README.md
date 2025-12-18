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
