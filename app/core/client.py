import httpx
from fastapi import FastAPI
from loguru import logger

from app.core.config import get_settings


async def init_gateway_client(app: FastAPI) -> None:
    """Создаёт HTTP-клиент для работы со шлюзом ЕВМИАС."""
    settings = get_settings()

    app.state.gateway_client = httpx.AsyncClient(
        base_url=settings.gateway_url,
        headers={
            "X-API-KEY": settings.gateway_api_key,
            "X-Session-ID": settings.gateway_session_id,
        },
        timeout=settings.request_timeout,
        verify=False,
    )

    logger.info(
        "Gateway client initialized | base_url={}",
        settings.gateway_url,
    )


async def shutdown_gateway_client(app: FastAPI) -> None:
    """Закрывает HTTP-клиент шлюза ЕВМИАС."""
    if hasattr(app.state, "gateway_client"):
        await app.state.gateway_client.aclose()
        logger.info("Gateway client closed")
