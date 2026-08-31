from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.error import (
    GatewayResponseError,
    GatewayUnavailableError,
)


def get_request_id(request: Request) -> str:
    """Возвращает идентификатор текущего HTTP-запроса."""
    return getattr(request.state, "request_id", "-")


async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
) -> JSONResponse:
    """Обрабатывает ожидаемые HTTP-ошибки."""
    request_id = get_request_id(request)

    logger.bind(request_id=request_id).warning(
        "HTTP ошибка | status={} | detail={}",
        exc.status_code,
        exc.detail,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(
            {
                "detail": exc.detail,
                "request_id": request_id,
            }
        ),
        headers=exc.headers,
    )


async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
) -> JSONResponse:
    """Обрабатывает ошибки валидации входных данных."""
    request_id = get_request_id(request)

    logger.bind(request_id=request_id).warning(
        "Ошибка валидации | errors={}",
        exc.errors(),
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=jsonable_encoder(
            {
                "detail": "Ошибка валидации данных",
                "errors": exc.errors(),
                "request_id": request_id,
            }
        ),
    )


async def unexpected_exception_handler(
        request: Request,
        exc: Exception,
) -> JSONResponse:
    """Обрабатывает необработанные исключения приложения."""
    request_id = get_request_id(request)

    logger.bind(request_id=request_id).opt(exception=exc).error(
        "Необработанная ошибка | type={} | {}",
        type(exc).__name__,
        exc,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Внутренняя ошибка сервера",
            "request_id": request_id,
        },
        headers={
            "X-Request-ID": request_id,
        },
    )


async def gateway_unavailable_exception_handler(
    request: Request,
    exc: GatewayUnavailableError,
) -> JSONResponse:
    """Обрабатывает недоступность шлюза ЕВМИАС."""
    request_id = get_request_id(request)

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "detail": "Шлюз ЕВМИАС временно недоступен",
            "request_id": request_id,
        },
    )


async def gateway_response_exception_handler(
    request: Request,
    exc: GatewayResponseError,
) -> JSONResponse:
    """Обрабатывает ошибочный HTTP-ответ шлюза ЕВМИАС."""
    request_id = get_request_id(request)

    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={
            "detail": "Ошибка ответа шлюза ЕВМИАС",
            "upstream_status": exc.status_code,
            "request_id": request_id,
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Регистрирует глобальные обработчики исключений."""
    app.exception_handler(StarletteHTTPException)(http_exception_handler)
    app.exception_handler(RequestValidationError)(validation_exception_handler)

    app.exception_handler(GatewayUnavailableError)(
        gateway_unavailable_exception_handler
    )
    app.exception_handler(GatewayResponseError)(
        gateway_response_exception_handler
    )

    app.exception_handler(Exception)(unexpected_exception_handler)
