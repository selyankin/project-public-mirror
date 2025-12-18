"""FastAPI application bootstrap utilities."""

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from checks.api.routes.check import router as check_router
from reports.api.routes import router as reports_router
from shared.kernel.logging import get_logger, setup_logging
from shared.kernel.settings import get_settings

RouterFactory = Callable[[], APIRouter]


def _health_router() -> APIRouter:
    router = APIRouter()

    @router.get('/health')
    async def health() -> dict[str, str]:
        return {'status': 'ok'}

    return router


COMMON_ROUTER_FACTORIES: tuple[RouterFactory, ...] = (_health_router,)

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
            logger.info('app_shutdown')

    app = FastAPI(
        title=settings.SERVICE_NAME,
        debug=settings.DEBUG,
        lifespan=lifespan,
    )

    for factory in COMMON_ROUTER_FACTORIES:
        app.include_router(factory())

    for factory in ROUTER_FACTORIES:
        app.include_router(factory[0], prefix=factory[1], tags=factory[2])

    return app
