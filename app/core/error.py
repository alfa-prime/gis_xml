class GatewayError(Exception):
    """Базовая ошибка взаимодействия со шлюзом ЕВМИАС."""


class GatewayUnavailableError(GatewayError):
    """Шлюз ЕВМИАС недоступен."""


class GatewayResponseError(GatewayError):
    """Шлюз ЕВМИАС вернул ошибочный HTTP-ответ."""

    def __init__(self, status_code: int):
        self.status_code = status_code
        super().__init__(f"Gateway returned HTTP {status_code}")