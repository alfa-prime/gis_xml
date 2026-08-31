from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.router import health_router
from app.core.config import get_settings
from app.core.exception import register_exception_handlers
from app.core.logging import configure_logger
from app.core.middleware import LoggingMiddleware

from app.core.client import (
    init_gateway_client,
    shutdown_gateway_client,
)

settings = get_settings()
configure_logger(settings.logs_level)

tags_metadata = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_gateway_client(app)
    yield
    await shutdown_gateway_client(app)


app = FastAPI(
    lifespan=lifespan,
    tags=tags_metadata,
    root_path="/gis_oms",
    title="GIS-OMS",
    description="GIS-OMS",
    version="0.1.0",
    # для разработки вводим API KEY один раз, в проде УБРАТЬ!
    swagger_ui_parameters={
        "persistAuthorization": True
    },
)

register_exception_handlers(app)
app.add_middleware(LoggingMiddleware)
app.include_router(health_router)
