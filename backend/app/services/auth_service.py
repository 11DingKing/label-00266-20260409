"""
认证服务
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User

# 简单的token存储（生产环境建议用Redis）
_tokens: dict[str, dict] = {}

TOKEN_EXPIRE_HOURS = 24


def hash_password(password: str) -> str:
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """验证密码"""
    return hash_password(password) == password_hash


def create_token(user_id: int, username: str) -> str:
    """创建token"""
    token = secrets.token_urlsafe(32)
    _tokens[token] = {
        "user_id": user_id,
        "username": username,
        "expires": datetime.now() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    }
    return token


def verify_token(token: str) -> Optional[dict]:
    """验证token"""
    if token not in _tokens:
        return None
    token_data = _tokens[token]
    if datetime.now() > token_data["expires"]:
        del _tokens[token]
        return None
    return token_data


def remove_token(token: str):
    """移除token"""
    _tokens.pop(token, None)


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """验证用户"""
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    if not user.is_active:
        return None
    return user


def init_default_user(db: Session):
    """初始化默认用户"""
    existing = db.query(User).filter(User.username == "admin").first()
    if not existing:
        user = User(
            username="admin",
            password_hash=hash_password("admin123")
        )
        db.add(user)
        db.commit()
