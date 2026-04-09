"""
AI文章自动生成与发布系统 - 主入口
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db
from app.core.logging import setup_logging
from app.core.exceptions import (
    global_exception_handler,
    app_exception_handler,
    validation_exception_handler,
    sqlalchemy_exception_handler,
    AppException
)
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from app.api.v1 import router as api_router
from app.core.scheduler import scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    setup_logging()
    init_db()
    scheduler.start()
    yield
    # 关闭时
    scheduler.shutdown()


app = FastAPI(
    title="AI文章自动生成与发布系统",
    description="基于DeepSeek API的自动文章生成与CMS发布系统",
    version="1.0.0",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册异常处理器
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)

# 注册路由
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    """健康检查"""
    return {"status": "ok", "message": "AI文章自动生成与发布系统运行中"}


@app.get("/health")
async def health():
    """健康检查端点"""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG
    )
