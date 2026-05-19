from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.order import OrderCreate, OrderUpdate, OrderResponse
from app.crud import order as crud

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/", response_model=list[OrderResponse])
async def get_orders(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await crud.get_all(db, skip, limit)


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: int, db: AsyncSession = Depends(get_db)):
    order = await crud.get_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(data: OrderCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await crud.create(db, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(order_id: int, data: OrderUpdate, db: AsyncSession = Depends(get_db)):
    order = await crud.update(db, order_id, data)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(order_id: int, db: AsyncSession = Depends(get_db)):
    if not await crud.delete(db, order_id):
        raise HTTPException(status_code=404, detail="Order not found")
