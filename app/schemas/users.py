from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserRegisterRequest(BaseModel):
    telegram_id: int = Field(gt=0)
    referral_code: str | None = Field(default=None, max_length=64)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    telegram_id: int
    created_at: datetime
    last_active_at: datetime
    referral_code: str | None
    invited_by: int | None
    complaints_count: int
    status: str


class UserActivityResponse(BaseModel):
    user_id: int
    last_active_at: datetime
