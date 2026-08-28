import hmac

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import get_settings

settings = get_settings()

api_key_header = APIKeyHeader(
    name="X-API-Key",
    scheme_name="APIKeyAuth",
    description="API-ключ для доступа к API",
)


async def verify_api_key(
        api_key: str = Security(api_key_header),
) -> str:
    if not hmac.compare_digest(api_key, settings.app_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный API-ключ",
        )

    return api_key
