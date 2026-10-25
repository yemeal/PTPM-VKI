from pydantic import BaseModel, ConfigDict


class BaseCommand[ResultT](BaseModel):
    """базовая команда с типом результата"""

    model_config = ConfigDict(
        frozen=True, extra="forbid", validate_default=True
    )
