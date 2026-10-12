from typing import Any
from pydantic import BaseModel

class BaseService:
    """所有Service的基类，统一异常、返回封装"""
    @staticmethod
    def success(data: Any, msg: str = "ok") -> dict:
        return {"code": 200, "msg": msg, "data": data}

    @staticmethod
    def fail(msg: str, code: int = 400) -> dict:
        return {"code": code, "msg": msg, "data": None}
