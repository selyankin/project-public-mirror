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
