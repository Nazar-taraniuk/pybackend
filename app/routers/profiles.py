from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.profile import ProfileCreate, ProfileUpdate, ProfileResponse
from app.crud import profile as crud

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/{profile_id}", response_model=ProfileResponse)
async def get_profile(profile_id: int, db: AsyncSession = Depends(get_db)):
    profile = await crud.get_by_id(db, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.get("/user/{user_id}", response_model=ProfileResponse)
async def get_profile_by_user(user_id: int, db: AsyncSession = Depends(get_db)):
    profile = await crud.get_by_user_id(db, user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.post("/", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(data: ProfileCreate, db: AsyncSession = Depends(get_db)):
    if await crud.get_by_user_id(db, data.user_id):
        raise HTTPException(status_code=400, detail="Profile for this user already exists")
    return await crud.create(db, data)


@router.put("/{profile_id}", response_model=ProfileResponse)
async def update_profile(profile_id: int, data: ProfileUpdate, db: AsyncSession = Depends(get_db)):
    profile = await crud.update(db, profile_id, data)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(profile_id: int, db: AsyncSession = Depends(get_db)):
    if not await crud.delete(db, profile_id):
        raise HTTPException(status_code=404, detail="Profile not found")
