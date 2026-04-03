from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user1_id: int
    user2_id: int
    created_at: datetime
    dialog_started: bool


class MatchDialogStartedRequest(BaseModel):
    match_id: int = Field(gt=0)
