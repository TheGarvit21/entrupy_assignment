from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class SourceEnum(str, Enum):
    GRAILED = "grailed"
    FASHIONPHILE = "fashionphile"
    ONESD_IBS = "1stdibs"


# User Schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


# Product Schemas
class PriceHistoryResponse(BaseModel):
    id: int
    price: float
    currency: str
    recorded_at: datetime

    class Config:
        from_attributes = True


class ProductCreate(BaseModel):
    external_id: str
    source: SourceEnum
    name: str
    url: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    current_price: float
    currency: str = "USD"


class ProductUpdate(BaseModel):
    current_price: Optional[float] = None
    category: Optional[str] = None
    description: Optional[str] = None


class ProductDetail(BaseModel):
    id: int
    external_id: str
    source: SourceEnum
    name: str
    url: Optional[str]
    category: Optional[str]
    description: Optional[str]
    current_price: float
    currency: str
    created_at: datetime
    updated_at: datetime
    last_fetched: Optional[datetime]
    price_history: List[PriceHistoryResponse]

    class Config:
        from_attributes = True


class ProductResponse(BaseModel):
    id: int
    external_id: str
    source: SourceEnum
    name: str
    url: Optional[str]
    category: Optional[str]
    current_price: float
    currency: str
    updated_at: datetime

    class Config:
        from_attributes = True


# Price Alert Schemas
class PriceAlertCreate(BaseModel):
    product_id: int
    threshold_price: Optional[float] = None
    alert_type: str = "any_change"  # "price_drop", "price_increase", "any_change"


class PriceAlertResponse(BaseModel):
    id: int
    product_id: int
    threshold_price: Optional[float]
    alert_type: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Analytics Schemas
class AggregateStats(BaseModel):
    total_products: int
    products_by_source: dict
    avg_price_by_category: dict
    total_price_changes_today: int


# API Response
class Token(BaseModel):
    access_token: str
    token_type: str


class PaginatedResponse(BaseModel):
    items: List[ProductResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
