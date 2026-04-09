"""
系统配置模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.models.base import Base


class SystemConfig(Base):
    """系统配置表"""
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(100), nullable=False, unique=True, comment="配置键")
    config_value = Column(Text, nullable=False, comment="配置值")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    def __repr__(self):
        return f"<SystemConfig(id={self.id}, config_key={self.config_key})>"
