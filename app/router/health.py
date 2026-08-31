from fastapi import APIRouter, Security

from app.core.dependencies import GatewayServiceDep
from app.core.dependencies import verify_api_key
from app.schema.gateway import GatewayRequest

router = APIRouter(
    prefix="/health",
    tags=["Health"],
    dependencies=[Security(verify_api_key)],
)


@router.get(
    path="/",
    summary="Стандартная проверка работоспособности",
    description="Возвращает 'pong', если сервис запущен и отвечает на запросы.",
)
async def ping():
    return {"ping": "pong"}


@router.post(
    path="/gateway",
    summary="Проверка связи со шлюзом API",
    description=(
            "Отправляет тестовый запрос на API-шлюз "
            "для проверки связи и аутентификации."
    ),
)
async def check_gateway_connection(
        gateway_service: GatewayServiceDep,
):
    payload = GatewayRequest.model_validate(
        {
            "params": {
                "c": "Common",
                "m": "getCurrentDateTime",
            },
            "data": {
                "is_activerulles": "true",
            },
        }
    )

    return await gateway_service.make_request(payload)
