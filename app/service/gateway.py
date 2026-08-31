from time import perf_counter

import httpx
from loguru import logger
from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
)

from app.core.config import get_settings
from app.schema.gateway import GatewayRequest

from app.core.error import (
    GatewayInvalidResponseError,
    GatewayResponseError,
    GatewayUnavailableError,
)

settings = get_settings()

RETRY_ATTEMPTS = 5
RETRY_WAIT_SECONDS = 2

RETRYABLE_EXCEPTIONS = (
    httpx.ConnectError,
    httpx.ConnectTimeout,
    httpx.ReadError,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
)


def log_gateway_retry(retry_state: RetryCallState) -> None:
    """Логирует повторную попытку обращения к шлюзу."""

    payload = retry_state.args[1]

    exception = (
        retry_state.outcome.exception()
        if retry_state.outcome
        else None
    )

    logger.warning(
        (
            "ЕВМИАС | повтор | попытка={}/{} | через={}с | "
            "class={} | method={} | error={}: {}"
        ),
        retry_state.attempt_number + 1,
        RETRY_ATTEMPTS,
        RETRY_WAIT_SECONDS,
        payload.params.c,
        payload.params.m,
        type(exception).__name__ if exception else "-",
        exception or "-",
    )


class GatewayService:
    """Сервис для работы со шлюзом ЕВМИАС."""

    GATEWAY_ENDPOINT = settings.gateway_request_endpoint

    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def make_request(
            self,
            payload: GatewayRequest,
    ) -> dict:
        started_at = perf_counter()

        logger.info(
            "ЕВМИАС | запрос | class={} | method={}",
            payload.params.c,
            payload.params.m,
        )

        try:
            response = await self._send_request(payload)


        except httpx.HTTPStatusError as exc:
            logger.error(
                (
                    "ЕВМИАС | ошибка ответа | class={} | method={} | "
                    "status={}"
                ),
                payload.params.c,
                payload.params.m,
                exc.response.status_code,
            )

            raise GatewayResponseError(
                status_code=exc.response.status_code,
            ) from exc

        except RETRYABLE_EXCEPTIONS as exc:
            logger.error(
                (
                    "ЕВМИАС | недоступен | class={} | method={} | "
                    "type={}"
                ),
                payload.params.c,
                payload.params.m,
                type(exc).__name__,
            )

            raise GatewayUnavailableError() from exc

        elapsed_ms = (perf_counter() - started_at) * 1000

        logger.info(
            (
                "ЕВМИАС | ответ | class={} | method={} | "
                "status={} | {:.2f} ms"
            ),
            payload.params.c,
            payload.params.m,
            response.status_code,
            elapsed_ms,
        )

        try:
            data = response.json() if response.content else {}

        except ValueError as exc:
            logger.error(
                (
                    "ЕВМИАС | некорректный ответ | class={} | method={} | "
                    "status={} | content_type={}"
                ),
                payload.params.c,
                payload.params.m,
                response.status_code,
                response.headers.get("content-type", "-"),
            )

            raise GatewayInvalidResponseError() from exc

        return data

    @retry(
        stop=stop_after_attempt(RETRY_ATTEMPTS),
        wait=wait_fixed(RETRY_WAIT_SECONDS),
        retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
        reraise=True,
        before_sleep=log_gateway_retry,
    )
    async def _send_request(
            self,
            payload: GatewayRequest,
    ) -> httpx.Response:
        response = await self._client.post(
            url=self.GATEWAY_ENDPOINT,
            json=payload.model_dump(),
        )

        response.raise_for_status()

        return response
