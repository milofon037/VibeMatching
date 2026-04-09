from pydantic import BaseModel, ConfigDict, Field


class PhotoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    profile_id: int
    photo_url: str
    position: int


class PhotoUploadResponse(BaseModel):
    photo: PhotoResponse


class PhotoDeleteResponse(BaseModel):
    deleted: bool = True
    photo_id: int


class PhotoUploadMeta(BaseModel):
    position: int | None = Field(default=None, ge=1)
