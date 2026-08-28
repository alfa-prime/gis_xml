from fastapi import APIRouter, Security

from app.core.dependencies import verify_api_key

router = APIRouter(prefix="/health", tags=["Health"], dependencies=[Security(verify_api_key)])


@router.get(
    path="/",
    summary="Стандартная проверка работоспособности",
    description="Возвращает 'pong', если сервис запущен и отвечает на запросы."
)
async def ping():
    return {"ping": "pong"}


@router.get("/validate")
async def validate(value: int):
    return {"value": value}

@router.get("/error")
async def error():
    raise RuntimeError("Тестовая ошибка")

