from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    path="/",
    summary="Стандартная проверка работоспособности",
    description="Возвращает 'pong', если сервис запущен и отвечает на запросы."
)
async def ping():
    return {"ping": "pong"}
