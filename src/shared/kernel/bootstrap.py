"""FastAPI application bootstrap utilities."""

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

import httpx
from fastapi import APIRouter, FastAPI, HTTPException
from sqlalchemy import text

from checks.api.routes.check import router as check_router
from reports.api.routes import router as reports_router
from shared.kernel.db import create_engine, create_sessionmaker, session_scope
from shared.kernel.fias_client_factory import get_fias_client
from shared.kernel.logging import get_logger, setup_logging
from shared.kernel.repositories import configure_repositories
from shared.kernel.settings import get_settings

RouterFactory = Callable[[], APIRouter]


def _health_router(session_factory) -> APIRouter:
    router = APIRouter()

    @router.get('/health')
    async def health() -> dict[str, str]:
        return {'status': 'ok'}

    @router.get('/health/db')
    async def db_health() -> dict[str, str]:
        """Проверить соединение с БД."""

        try:
            async with session_scope(session_factory) as session:
                await session.execute(text('select 1'))
        except Exception as exc:
            raise HTTPException(
                status_code=503, detail='db_unavailable'
            ) from exc

        return {'status': 'ok'}

    return router


ROUTER_FACTORIES = (
    (
        check_router,
        '/v1',
        ['check'],
    ),
    (
        reports_router,
        '/v1',
        ['reports'],
    ),
)


def create_app() -> FastAPI:
    """Create and configure a FastAPI application instance."""

    setup_logging()
    settings = get_settings()
    logger = get_logger()
    engine = create_engine(settings)
    session_factory = create_sessionmaker(engine)
    configure_repositories(session_factory)
    fias_http_client: httpx.AsyncClient | None = None

    if settings.FIAS_MODE == 'api' and settings.FIAS_BASE_URL:
        fias_http_client = httpx.AsyncClient(
            base_url=settings.FIAS_BASE_URL.rstrip('/'),
        )

    fias_client = get_fias_client(settings, fias_http_client)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        logger.info(
            'app_startup env=%s service=%s',
            settings.APP_ENV,
            settings.SERVICE_NAME,
        )
        try:
            yield
        finally:
            if fias_http_client is not None:
                await fias_http_client.aclose()
            await engine.dispose()
            logger.info('app_shutdown')

    app = FastAPI(
        title=settings.SERVICE_NAME,
        debug=settings.DEBUG,
        lifespan=lifespan,
    )
    app.state.db_engine = engine
    app.state.db_session_factory = session_factory
    app.state.fias_client = fias_client
    app.state.fias_http_client = fias_http_client

    app.include_router(_health_router(session_factory))

    for factory in ROUTER_FACTORIES:
        app.include_router(factory[0], prefix=factory[1], tags=factory[2])

    return app
