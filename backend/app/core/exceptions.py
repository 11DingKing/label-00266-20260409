"""
全局异常处理
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)


class AppException(Exception):
    """应用基础异常"""
    def __init__(self, message: str, code: int = 500):
        self.message = message
        self.code = code
        super().__init__(self.message)


class APIException(AppException):
    """API异常"""
    pass


class FileReadException(AppException):
    """文件读取异常"""
    pass


class DeepSeekAPIException(AppException):
    """DeepSeek API调用异常"""
    pass


class CMSConnectionException(AppException):
    """CMS连接异常"""
    pass


async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "服务器内部错误",
            "detail": str(exc)
        }
    )


async def app_exception_handler(request: Request, exc: AppException):
    """应用异常处理器"""
    logger.error(f"应用异常: {exc.message}")
    return JSONResponse(
        status_code=exc.code,
        content={
            "success": False,
            "message": exc.message
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """参数验证异常处理器"""
    logger.warning(f"参数验证失败: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "参数验证失败",
            "detail": exc.errors()
        }
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """数据库异常处理器"""
    logger.error(f"数据库异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "数据库操作失败",
            "detail": str(exc)
        }
    )
