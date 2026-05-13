from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class AlertCreate(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    target_price: float
    direction: str = Field(pattern=r"^(price_above|price_below|daily_change_above|daily_change_below)$")

    @model_validator(mode="after")
    def validate_target(self) -> "AlertCreate":
        if self.direction in ("price_above", "price_below") and self.target_price <= 0:
            raise ValueError("target_price must be > 0 for price alerts")
        return self


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
