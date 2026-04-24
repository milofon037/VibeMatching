from pydantic import BaseModel, Field


class RankCandidate(BaseModel):
    profile_id: int
    base_rank: float = Field(ge=0, le=1)
    interests: list[int] = Field(default_factory=list)


class RankFeedRequest(BaseModel):
    user_id: int
    excluded_ids: list[int] = Field(default_factory=list)
    limit: int = Field(default=20, ge=1, le=100)
    user_interest_ids: list[int] = Field(default_factory=list)
    candidates: list[RankCandidate] = Field(default_factory=list)


class RankFeedResponse(BaseModel):
    ranked_profile_ids: list[int]
