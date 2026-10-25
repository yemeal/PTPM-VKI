from pydantic import BaseModel, ConfigDict


class BaseQuery[ResultT](BaseModel):
    """базовый запрос чтения с типом результата"""

    model_config = ConfigDict(
        frozen=True, extra="forbid", validate_default=True
    )
