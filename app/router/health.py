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
