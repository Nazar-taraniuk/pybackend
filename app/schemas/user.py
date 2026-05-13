from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Спільні поля для всіх схем юзера."""
    name: str = Field(..., min_length=1, max_length=100, description="Ім'я користувача")
    email: EmailStr = Field(..., description="Email користувача")


class UserCreate(UserBase):
    """Схема для створення юзера (POST)."""
    pass


class UserUpdate(BaseModel):
    """Схема для оновлення юзера (PUT) — всі поля необов'язкові."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None


class UserResponse(UserBase):
    """Схема відповіді — містить id."""
    id: int

    model_config = {"from_attributes": True}
