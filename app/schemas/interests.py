from pydantic import BaseModel, ConfigDict, Field, field_validator


class InterestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class ProfileInterestsUpdateRequest(BaseModel):
    interest_ids: list[int] = Field(default_factory=list)

    @field_validator("interest_ids")
    @classmethod
    def validate_interest_ids_unique(cls, value: list[int]) -> list[int]:
        if len(value) != len(set(value)):
            raise ValueError("interest_ids must not contain duplicates")
        return value
