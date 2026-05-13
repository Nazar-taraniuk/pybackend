from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class OrderItemBase(BaseModel):
    product_id: int
    quantity: int = 1


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemResponse(OrderItemBase):
    id: int
    order_id: int
    model_config = {"from_attributes": True}


class OrderBase(BaseModel):
    user_id: int
    status: str = "pending"


class OrderCreate(BaseModel):
    user_id: int
    items: list[OrderItemCreate]


class OrderUpdate(BaseModel):
    status: Optional[str] = None


class OrderResponse(OrderBase):
    id: int
    created_at: datetime
    items: list[OrderItemResponse] = []
    model_config = {"from_attributes": True}
