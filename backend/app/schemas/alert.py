from datetime import datetime

from pydantic import BaseModel, Field


class AlertCreate(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    target_price: float = Field(gt=0)
    direction: str = Field(pattern=r"^(above|below)$")


class AlertResponse(BaseModel):
    id: int
    user_id: int
    symbol: str
    target_price: float
    direction: str
    is_triggered: bool
    created_at: datetime
    triggered_at: datetime | None = None

    model_config = {"from_attributes": True}
