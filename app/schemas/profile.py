from typing import Optional
from pydantic import BaseModel, Field


class ProfileBase(BaseModel):
    bio: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)
    avatar_url: Optional[str] = Field(None, max_length=500)


class ProfileCreate(ProfileBase):
    user_id: int


class ProfileUpdate(ProfileBase):
    pass


class ProfileResponse(ProfileBase):
    id: int
    user_id: int
    model_config = {"from_attributes": True}
