import hmac
from typing import Annotated

import httpx
from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import get_settings
from app.service.gateway import GatewayService


settings = get_settings()

api_key_header = APIKeyHeader(
    name="X-API-Key",
    scheme_name="APIKeyAuth",
    description="API-ключ для доступа к API",
)


async def verify_api_key(
    api_key: str = Security(api_key_header),
) -> str:
    """Проверяет API-ключ входящего запроса."""
    if not hmac.compare_digest(api_key, settings.app_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный API-ключ",
        )

    return api_key


APIKeyDep = Annotated[
    str,
    Depends(verify_api_key),
]


def get_gateway_client(
    request: Request,
) -> httpx.AsyncClient:
    """Возвращает общий HTTP-клиент шлюза."""
    return request.app.state.gateway_client


GatewayClientDep = Annotated[
    httpx.AsyncClient,
    Depends(get_gateway_client),
]


def get_gateway_service(
    client: GatewayClientDep,
) -> GatewayService:
    """Создаёт сервис для работы со шлюзом."""
    return GatewayService(client=client)


GatewayServiceDep = Annotated[
    GatewayService,
    Depends(get_gateway_service),
]