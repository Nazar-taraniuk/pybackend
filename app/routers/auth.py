from fastapi import APIRouter, HTTPException, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UpdateMeRequest
from app.schemas.user import UserResponse, UserUpdate
from app.schemas.order import OrderResponse
from app.crud import user as user_crud
from app.crud import order as order_crud
from app.auth import hash_password, verify_password, create_access_token, COOKIE_NAME
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED,
             summary="Реєстрація нового користувача")
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Реєстрація нового юзера.
    Пароль зберігається у вигляді bcrypt хешу з сіллю — оригінал ніде не зберігається.
    """
    if await user_crud.get_by_email(db, data.email):
        raise HTTPException(status_code=400, detail="Email вже зареєстровано")

    return await user_crud.create_with_password(
        db,
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
    )


@router.post("/login", response_model=TokenResponse, summary="Вхід в систему (JWT у куці)")
async def login(data: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    """
    Аутентифікація юзера.
    При успіху — JWT токен записується в HTTP-only куку.
    """
    user = await user_crud.get_by_email(db, data.email)
    if not user or not user.password_hash or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Невірний email або пароль")

    token = create_access_token(user.id)

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        max_age=60 * 60 * 24,
        samesite="lax",
    )
    return TokenResponse(access_token=token, user_id=user.id, name=user.name)


@router.post("/logout", summary="Вихід з системи (очищення куки)")
async def logout(response: Response):
    """Видаляємо JWT куку — юзер вийшов з системи."""
    response.delete_cookie(key=COOKIE_NAME)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse, summary="Мій профіль (тільки для авторизованих)")
async def get_me(current_user: User = Depends(get_current_user)):
    """Повертає дані поточного авторизованого юзера."""
    return current_user


@router.get("/my-orders", response_model=list[OrderResponse],
            summary="Мої замовлення (тільки для авторизованих)")
async def get_my_orders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Повертає всі замовлення поточного авторизованого юзера."""
    return await order_crud.get_by_user_id(db, current_user.id)


@router.put("/me", response_model=UserResponse, summary="Оновити свої дані")
async def update_me(
    data: UpdateMeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Авторизований юзер може оновити своє ім'я."""
    user = await user_crud.update(db, current_user.id, UserUpdate(name=data.name))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
