from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import Gender, SearchCityMode


class ProfileCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    age: int = Field(ge=18, le=100)
    gender: Gender
    city: str = Field(min_length=1, max_length=128)
    bio: str | None = None
    interests: str | None = None
    preferred_gender: Gender | None = None
    preferred_age_min: int | None = Field(default=None, ge=18, le=100)
    preferred_age_max: int | None = Field(default=None, ge=18, le=100)

    @model_validator(mode="after")
    def validate_preferred_age_range(self):
        if self.preferred_age_min is not None and self.preferred_age_max is not None:
            if self.preferred_age_min > self.preferred_age_max:
                raise ValueError("preferred_age_min must be less than or equal to preferred_age_max")
        return self


class ProfileUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    age: int | None = Field(default=None, ge=18, le=100)
    gender: Gender | None = None
    city: str | None = Field(default=None, min_length=1, max_length=128)
    bio: str | None = None
    interests: str | None = None
    preferred_gender: Gender | None = None
    preferred_age_min: int | None = Field(default=None, ge=18, le=100)
    preferred_age_max: int | None = Field(default=None, ge=18, le=100)

    @model_validator(mode="after")
    def validate_preferred_age_range(self):
        if self.preferred_age_min is not None and self.preferred_age_max is not None:
            if self.preferred_age_min > self.preferred_age_max:
                raise ValueError("preferred_age_min must be less than or equal to preferred_age_max")
        return self


class ProfileSearchModeRequest(BaseModel):
    search_city_mode: SearchCityMode


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    name: str
    age: int
    gender: Gender
    city: str
    bio: str | None
    interests: str | None
    preferred_gender: Gender | None
    preferred_age_min: int | None
    preferred_age_max: int | None
    search_city_mode: SearchCityMode
