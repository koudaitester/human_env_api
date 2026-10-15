# 原有报告接口不变
from fastapi import APIRouter, Query
from services.report_service import get_report_list, get_report_detail, get_conn
# 新增温湿度接口
from services.env_service import env_service

router = APIRouter()

@router.post("/add")
async def add_env_record(temperature: float, humidity: float, remark: str = ""):
    await env_service.save_env_data(temperature, humidity, remark)
    return {"ok": True, "msg": "环境数据保存成功"}

@router.get("/history")
async def get_env_history_api(start_time: str = None, end_time: str = None, limit: int = 100):
    data = await env_service.get_env_history(start_time, end_time, limit)
    return {"data": data}