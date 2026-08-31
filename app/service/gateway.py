import httpx
import logging
from loguru import logger
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
)

from app.core.config import get_settings
from app.schema.gateway import GatewayRequest


settings = get_settings()
retry_logger = logging.getLogger(__name__)

RETRYABLE_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.ReadError,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
)


class GatewayService:
    """Сервис для работы со шлюзом ЕВМИАС."""

    GATEWAY_ENDPOINT = settings.gateway_request_endpoint

    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
        reraise=True,
        before_sleep=before_sleep_log(
            retry_logger,
            logging.WARNING,
        ),
    )
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