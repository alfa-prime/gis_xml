import httpx

from app.core import get_settings
from app.schema.gateway import GatewayRequest


settings = get_settings()


class GatewayService:
    """Сервис для работы со шлюзом ЕВМИАС."""

    GATEWAY_ENDPOINT = settings.gateway_request_endpoint

    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def make_request(
        self,
        payload: GatewayRequest,
    ) -> dict:
        response = await self._client.post(
            url=self.GATEWAY_ENDPOINT,
            json=payload.model_dump(),
        )

        response.raise_for_status()

        return response.json() if response.content else {}