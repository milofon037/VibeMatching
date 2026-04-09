from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import SwipeAction


class SwipeRequest(BaseModel):
    to_profile_id: int = Field(gt=0)


class SwipeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    from_user_id: int
    to_profile_id: int
    action: SwipeAction
    created_at: datetime
