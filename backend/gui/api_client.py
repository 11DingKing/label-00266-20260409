"""
API 客户端 - 与后端通信
"""
import os
import requests
from typing import Optional, Any


class APIClient:
    """后端 API 客户端"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv("API_BASE_URL", "http://localhost:8000/api")
    
    def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """发送请求"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = requests.request(method, url, timeout=60, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            raise Exception("请求超时，请稍后重试")
        except requests.exceptions.ConnectionError:
            raise Exception("无法连接到服务器，请检查后端服务是否启动")
        except requests.exceptions.HTTPError as e:
            try:
                error_detail = e.response.json().get("detail", str(e))
            except:
                error_detail = str(e)
            raise Exception(f"请求失败: {error_detail}")
        except Exception as e:
            raise Exception(f"请求错误: {e}")
    
    def get(self, endpoint: str, params: dict = None) -> dict:
        return self._request("GET", endpoint, params=params)
    
    def post(self, endpoint: str, json: dict = None, data: dict = None, files: dict = None) -> dict:
        return self._request("POST", endpoint, json=json, data=data, files=files)
    
    def put(self, endpoint: str, json: dict = None) -> dict:
        return self._request("PUT", endpoint, json=json)
    
    def delete(self, endpoint: str) -> dict:
        return self._request("DELETE", endpoint)


def format_datetime(iso_string: Optional[str]) -> str:
    """格式化 ISO 日期时间字符串"""
    if not iso_string:
        return "-"
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return iso_string


def get_status_text(status: str) -> str:
    """获取状态文本"""
    texts = {
        "pending": "待发布",
        "published": "已发布",
        "failed": "失败",
        "success": "成功",
        "running": "运行中",
        "completed": "已完成"
    }
    return texts.get(status, status)
