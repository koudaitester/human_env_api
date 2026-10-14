from fastapi import APIRouter, UploadFile, File, Query
from services.llama_service import llama_service
import base64
from services.log_service import logger
import re
from services.report_service import save_report
import json

router = APIRouter()

@router.post("/visual")
async def mold_visual(file: UploadFile = File(...)):
    img_bytes = await file.read()
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
    logger.info("霉菌检测视觉分析接口调用")
    # 调用实例方法
    result = await llama_service.analyze_mold_visual(img_b64)
    raw = re.sub(r'```(json)?', '', result["data"]).strip()
    result["data"] = raw
    logger.info(f"霉菌检测视觉分析结果: {result}")
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
    raw = re.sub(r'```(json)?', '', result["data"]).strip()

    # 字符串json转字典
    try:
        data_dict = json.loads(raw)
    except json.JSONDecodeError:
        data_dict = {}

    risk_level = data_dict.get("riskLevel", "未知风险等级")
    result["data"] = data_dict
    logger.info(f"霉菌检测全参数分析结果: {result}")

    try:
        # ✅ 这里修正：传入接口真实的温湿度 humidity -> hum
        await save_report(
            type_str="image",
            temp=temp,
            hum=humidity,
            thumbnail=None,
            result_json=result,
            risk_level=risk_level
        )
    except Exception as e:
        logger.exception("保存报告入库异常", exc_info=e)

    result["data"] = raw
    return result