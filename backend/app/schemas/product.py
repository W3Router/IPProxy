from pydantic import BaseModel, condecimal, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

class ProductPriceBase(BaseModel):
    id: int
    type: str  # 'dynamic' | 'static'
    area: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    ipRange: Optional[str] = None
    price: Decimal = Field(default=Decimal('0'), decimal_places=4)
    isGlobal: bool = True
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: lambda v: float(v)
        }
        alias_generator = lambda x: x[0].lower() + x[1:] if x else x  # 驼峰命名转换

class ProductPriceUpdate(BaseModel):
    id: int
    price: condecimal(max_digits=10, decimal_places=4)

class ProductPriceUpdateRequest(BaseModel):
    is_global: bool
    agent_id: Optional[int]
    prices: List[ProductPriceUpdate]

    class Config:
        from_attributes = True

class ProductPriceResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: List[ProductPriceBase]

    class Config:
        from_attributes = True

class ImportPriceItem(BaseModel):
    type: str  # 'dynamic' | 'static'
    area: str
    country: str
    city: str
    ip_range: Optional[str]
    price: condecimal(max_digits=10, decimal_places=1)

class BatchImportRequest(BaseModel):
    prices: List[ImportPriceItem]

    class Config:
        from_attributes = True

class ImportResult(BaseModel):
    total: int
    success: int
    failed: int

    class Config:
        from_attributes = True 