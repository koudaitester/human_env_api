# 原有报告接口不变
from fastapi import APIRouter, Query
from services.report_service import get_report_list, get_report_detail, get_conn
# 新增温湿度接口
from services.env_service import env_service
from pydantic import BaseModel, Field

router = APIRouter()

# 请求参数校验模型
class EnvAddSchema(BaseModel):
    temperature: float = Field(gt=-10, lt=60, description="温度范围 -10 ~ 60 ℃")
    humidity: float = Field(gt=0, lt=100, description="相对湿度 0~100 %")
    remark: str = ""

@router.post("/add")
async def add_env_record(env: EnvAddSchema):
    await env_service.save_env_data(env.temperature, env.humidity, env.remark)
    return {"ok": True, "msg": "环境数据保存成功"}

@router.get("/history")
async def get_env_history_api(start_time: str = None, end_time: str = None, limit: int = 100):
    data = await env_service.get_env_history(start_time, end_time, limit)
    return {"data": data}

@router.get("/risk")
async def env_risk_api(start_time:str=None, end_time:str=None, limit:int=100):
    analysis = await env_service.get_env_risk_analysis(start_time, end_time, limit)
    return analysis