import time
import uuid

from loguru import logger
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class LoggingMiddleware:
    """Логирует входящие HTTP-запросы и результаты их обработки."""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = uuid.uuid4().hex[:8]
        scope.setdefault("state", {})
        scope["state"]["request_id"] = request_id

        method = scope["method"]
        path = scope["path"]

        client = scope.get("client")
        client_ip = client[0] if client else "-"

        started_at = time.perf_counter()
        status_code = 500

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code

            if message["type"] == "http.response.start":
                status_code = message["status"]

                headers = list(message.get("headers", []))
                headers.append(
                    (b"x-request-id", request_id.encode("utf-8"))
                )
                message["headers"] = headers

            await send(message)

        with logger.contextualize(request_id=request_id):
            logger.info(
                "Запрос | {} {} | client={}",
                method,
                path,
                client_ip,
            )

            try:
                await self.app(
                    scope,
                    receive,
                    send_wrapper,
                )
            finally:
                elapsed = (time.perf_counter() - started_at) * 1000

                logger.info(
                    "Ответ | {} {} | status={} | {:.2f} ms",
                    method,
                    path,
                    status_code,
                    elapsed,
                )
