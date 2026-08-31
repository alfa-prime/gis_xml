from typing import Any

from pydantic import BaseModel, Field


class RequestParams(BaseModel):
    c: str = Field(
        ...,
        description="Класс",
    )
    m: str = Field(
        ...,
        description="Метод",
    )


class GatewayRequest(BaseModel):
    params: RequestParams
    data: dict[str, Any]