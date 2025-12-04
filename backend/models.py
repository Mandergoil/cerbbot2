from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    media: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    featured: bool = False


class ProductCreate(ProductBase):
    id: Optional[str] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    media: Optional[str] = None
    description: Optional[str] = None
    featured: Optional[bool] = None


class Product(ProductBase):
    id: str


class ProductsResponse(BaseModel):
    items: List[Product]


class ProductResponse(BaseModel):
    item: Product


class AdminRequest(BaseModel):
    username: str


class AdminsResponse(BaseModel):
    admins: List[str]


class AuthRequest(BaseModel):
    intent: str = "exchange"
    username: Optional[str] = None
    token: Optional[str] = None
    password: Optional[str] = None


class AuthResponse(BaseModel):
    bearer: str
    expiresInMinutes: int


class TokenResponse(BaseModel):
    token: str
    expiresInMinutes: int


class UserResponse(BaseModel):
    user: dict
