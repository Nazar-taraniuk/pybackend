from typing import Dict
from fastapi import APIRouter, HTTPException, status

from app.schemas.user import UserCreate, UserUpdate, UserResponse

router = APIRouter(
    prefix="/users",
    tags=["users"],
)

# Емуляція бази даних через звичайний словник
users_db: Dict[int, dict] = {}
next_id: int = 1


@router.get("/", response_model=list[UserResponse], summary="Отримати всіх юзерів")
async def get_users():
    """Повертає список всіх юзерів."""
    return list(users_db.values())


@router.get("/{user_id}", response_model=UserResponse, summary="Отримати юзера за ID")
async def get_user(user_id: int):
    """Повертає одного юзера по ID."""
    if user_id not in users_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return users_db[user_id]


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Створити юзера")
async def create_user(user: UserCreate):
    """Створює нового юзера. Email має бути унікальним."""
    global next_id

    # Перевірка унікальності email
    for existing in users_db.values():
        if existing["email"] == user.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )

    new_user = {"id": next_id, **user.model_dump()}
    users_db[next_id] = new_user
    next_id += 1
    return new_user


@router.put("/{user_id}", response_model=UserResponse, summary="Оновити юзера")
async def update_user(user_id: int, user: UserUpdate):
    """Оновлює поля юзера. Передавати тільки ті поля, що змінюються."""
    if user_id not in users_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    update_data = user.model_dump(exclude_unset=True)
    users_db[user_id].update(update_data)
    return users_db[user_id]


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Видалити юзера")
async def delete_user(user_id: int):
    """Видаляє юзера по ID."""
    if user_id not in users_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    del users_db[user_id]
