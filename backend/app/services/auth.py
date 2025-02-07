from datetime import datetime, timedelta
from typing import Optional
import jwt
from jwt import PyJWTError
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from ..models.user import User
from ..database import SessionLocal
import logging
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import SECRET_KEY, ALGORITHM
from app.core.security import verify_password, get_password_hash
import os

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/login",  # 修改为实际的登录接口路径
    auto_error=False  # 允许自定义错误消息
)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    try:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=180)  # 默认180天过期
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        logger.debug(f"Created access token for user: {data.get('sub')}")
        return encoded_jwt
    except Exception as e:
        logger.error(f"创建访问令牌失败: {str(e)}")
        return None

def verify_token(token: str):
    """验证令牌"""
    try:
        logger.info(f"[Auth Service] Verifying token: {token[:10]}...")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.info(f"[Auth Service] Token decoded successfully: {payload}")
        return payload
    except PyJWTError as e:
        logger.error(f"[Auth Service] Token verification failed: {str(e)}")
        return None

async def authenticate_user(username: str, password: str, db: Session) -> Optional[User]:
    """验证用户"""
    try:
        logger.debug(f"开始认证用户: {username}")
        
        # 从数据库中查询用户
        user = db.query(User).filter(User.username == username).first()
        if not user:
            logger.debug(f"用户 {username} 不存在")
            return None
            
        # 验证密码
        logger.debug(f"开始验证密码: password={password}, user.password={user.password}")
        if verify_password(password, user.password):
            logger.debug("用户密码验证成功")
            # 更新最后登录时间
            user.last_login_at = datetime.utcnow()
            db.commit()
            return user
        else:
            logger.debug("用户密码验证失败")
            return None
            
    except Exception as e:
        logger.error(f"认证过程发生错误: {str(e)}")
        logger.exception("详细错误信息:")
        return None

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    x_app_key: str = Header(None, alias="X-App-Key"),
    x_app_secret: str = Header(None, alias="X-App-Secret"),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """获取当前用户"""
    logger.info("[Auth Service] Getting current user")
    
    # 如果有X-App-Key和X-App-Secret，优先使用这些进行认证
    if x_app_key and x_app_secret:
        logger.info("[Auth Service] Using API key authentication")
        if x_app_key == os.getenv('APP_ID', "AK20241120145620") and \
           x_app_secret == os.getenv('APP_SECRET', "bf3ffghlt0hpc4omnvc2583jt0fag6a4"):
            logger.info("[Auth Service] API key authentication successful")
            return User(
                id=0,
                username="system",
                password="",
                email="system@example.com",
                is_admin=True,
                status="active",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        else:
            logger.warning("[Auth Service] Invalid API key or secret")
    
    if not token:
        logger.error("[Auth Service] No token provided")
        return None
        
    try:
        logger.debug("开始验证访问令牌")
        
        try:
            logger.debug(f"开始解码令牌: {token}")
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            logger.debug(f"令牌解码结果: {payload}")
            if user_id is None:
                logger.error("令牌中没有用户ID")
                return None
        except PyJWTError:
            logger.error("令牌解码失败")
            return None
            
        try:
            user_id_int = int(user_id)
            user = db.query(User).filter(User.id == user_id_int).first()
            if user is None:
                logger.error(f"找不到用户ID: {user_id_int}")
                return None
            return user
        except ValueError:
            logger.error(f"无效的用户ID格式: {user_id}")
            return None
    except Exception as e:
        logger.error(f"验证访问令牌时发生错误: {str(e)}")
        return None 