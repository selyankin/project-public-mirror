# Flaffy Coding Style (for AI assistants)

## General
- Prefer DDD + SOLID. Keep boundaries between domain/application/infrastructure/presentation.
- Avoid leaking infrastructure types into domain. Domain is pure Python.
- Use single quotes for strings.
- Use trailing commas where appropriate (multi-line args, dicts, lists, tuples).
- Prefer ~80 chars per line when reasonable; split long expressions into multiple lines.
- Each module starts with a short module docstring describing purpose.
- Add docstrings for public classes and public methods/functions.
- Type annotate parameters and return types.
- Data models (domain entities, value objects, DTOs) should be plain Python classes (no pydantic/dataclasses) unless explicitly requested.
- Keep comments rare. Code should be self-explanatory; comment only non-obvious intent.

## Architecture
- Modules are bounded contexts: src/<module>/{domain,application,infrastructure,presentation}
- Domain:
  - entities/, value_objects/, events/, services/, policies/, ports/
  - No FastAPI, SQLAlchemy, HTTP clients, or DB models here.
- Application:
  - use_cases/ orchestrate flows, call ports, map DTOs.
  - commands/queries optional; keep it simple unless needed.
- Infrastructure:
  - SQLAlchemy repositories implement domain ports.
  - HTTP adapters for external sources implement gateways.
  - Settings, logging, caching live here.
- Presentation:
  - FastAPI routers, schemas, presenters.
  - Converts HTTP input/output to/from application DTOs.

## Error handling
- Use explicit domain exceptions + application exceptions.
- In FastAPI layer, convert exceptions to HTTP errors via handlers.

## Async & DB
- Use asyncio-first approach.
- Use SQLAlchemy 2.0 async patterns (AsyncSession).
- Keep transactions in application layer (unit of work) or dedicated service.

## Testing
- Unit tests target domain + application.
- Integration tests cover repositories + API routes.

## Output expectations
- When generating code, show full file contents with paths.
- Keep code minimal but production-friendly (logging hooks, dependency injection points).
