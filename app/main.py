from fastapi import FastAPI

from app.router import health_router
from app.core.config import get_settings
from app.core.logging import configure_logger
from app.core.middleware import LoggingMiddleware

settings = get_settings()
configure_logger(settings.logs_level)

tags_metadata = []

app = FastAPI(
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

app.add_middleware(LoggingMiddleware)
app.include_router(health_router)
