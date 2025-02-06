from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    """用户基础信息"""
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, pattern=r'^\d{11}$')
    remark: Optional[str] = None

class UserCreate(UserBase):
    """创建用户时的数据结构"""
    password: str = Field(..., min_length=6, max_length=50)
    is_agent: bool = False
    agent_id: Optional[int] = None
    auth_type: Optional[int] = Field(None, ge=1, le=3)  # 1=未实名 2=个人实名 3=企业实名
    auth_name: Optional[str] = None
    no: Optional[str] = None  # 证件号码

    @validator('auth_type')
    def validate_auth_type(cls, v, values):
        """验证认证类型"""
        if v is not None and values.get('is_agent') and not values.get('auth_name'):
            raise ValueError('代理商必须提供认证名称')
        return v

class UserLogin(BaseModel):
    """用户登录时的数据结构"""
    username: str
    password: str

class UserResponse(UserBase):
    """返回给前端的用户信息"""
    id: int
    status: int
    is_admin: bool = False
    is_agent: bool = False
    balance: float = 0.0
    agent_id: Optional[int] = None
    ipipv_username: Optional[str] = None
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserInDB(UserBase):
    """数据库中的用户信息"""
    id: int
    password: str
    status: int = 1
    is_admin: bool = False
    is_agent: bool = False
    balance: float = 0.0
    agent_id: Optional[int] = None
    ipipv_username: Optional[str] = None
    ipipv_password: Optional[str] = None
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 