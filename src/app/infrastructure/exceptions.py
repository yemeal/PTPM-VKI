class InfrastructureError(Exception):
    """базовое исключение слоя инфраструктуры"""


class ForumFetchError(InfrastructureError):
    """ошибка загрузки страницы форума или фида"""

    def __init__(
        self,
        message: str = "Failed to fetch forum page",
        status_code: int = 502,
        upstream_status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.upstream_status_code = upstream_status_code
