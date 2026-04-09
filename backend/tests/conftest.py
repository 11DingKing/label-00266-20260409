"""
测试配置和fixtures
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from main import app


# 创建测试数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """覆盖数据库依赖"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


def reset_generation_task():
    """重置生成任务状态"""
    from app.services import generation_task
    with generation_task._task_lock:
        generation_task._generation_task = {
            "task_id": None,
            "status": "idle",
            "total": 0,
            "completed": 0,
            "current_title": "",
            "articles": [],
            "errors": [],
            "started_at": None,
            "finished_at": None,
            "params": {
                "count": 0,
                "keyword_ids": [],
                "use_knowledge_base": True
            }
        }


@pytest.fixture(scope="function")
def db():
    """创建测试数据库会话"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """创建测试客户端"""
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)
    
    # 重置生成任务状态
    reset_generation_task()
    
    with TestClient(app) as c:
        yield c
    
    # 测试后再次重置
    reset_generation_task()
    
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()
