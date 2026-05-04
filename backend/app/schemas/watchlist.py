from datetime import datetime

from pydantic import BaseModel, Field


class WatchlistAdd(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)


class WatchlistResponse(BaseModel):
    id: int
    user_id: int
    symbol: str
    created_at: datetime

    model_config = {"from_attributes": True}
