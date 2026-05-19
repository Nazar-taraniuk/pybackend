from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Схема для реєстрації нового юзера."""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, description="Мінімум 6 символів")


class LoginRequest(BaseModel):
    """Схема для входу."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Відповідь при успішній аутентифікації."""
    access_token: str
    token_type: str = "bearer"
    user_id: int
    name: str


class UpdateMeRequest(BaseModel):
    """Оновлення профілю поточного користувача."""
    name: str = Field(..., min_length=1, max_length=100)
