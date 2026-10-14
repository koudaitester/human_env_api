from fastapi import APIRouter, UploadFile, File, Query
from services.llama_service import llama_service
import base64
from services.log_service import logger
import re

router = APIRouter()

@router.post("/visual")
async def mold_visual(file: UploadFile = File(...)):
    img_bytes = await file.read()
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
    logger.info("霉菌检测视觉分析接口调用")
    # 调用实例方法
    result = await llama_service.analyze_mold_visual(img_b64)
    raw = re.sub(r'```(json)?', '', result["data"]).strip ()
    result["data"] = raw
    return result

@router.post("/full")
async def mold_full(
    file: UploadFile = File(...),
    temp: float = Query(..., description="环境温度 ℃"),
    humidity: float = Query(..., description="相对湿度 %")
):
    img_bytes = await file.read()
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
    logger.info("霉菌检测全参数分析接口调用")
    result = await llama_service.analyze_mold_full(img_b64, temp, humidity)
    raw = re.sub(r'```(json)?', '', result["data"]).strip ()
    result["data"] = raw
    return result
