"""
共享的数据库模型基类
所有模型都应该继承这个 Base
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """共享的数据库模型基类"""
    pass
