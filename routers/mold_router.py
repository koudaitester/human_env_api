from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from services.llama_service import llama_service
import base64
from services.log_service import logger
import re
from services.report_service import save_report
import json
from typing import Annotated
from utils.deps import get_current_user

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
    current_user = Depends(get_current_user),
    temp: float = Query(..., description="环境温度 ℃"),
    humidity: float = Query(..., description="相对湿度 %")
):
    img_bytes = await file.read()
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
    logger.info("霉菌检测全参数分析接口调用")
    # current_user 是dict，包含 id, username
    user_id = current_user["id"]
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
            risk_level=risk_level,
            user_id=user_id # type: ignore
        )
    except Exception as e:
        logger.exception("保存报告入库异常", exc_info=e)

    result["data"] = raw
    return result

# 多图综合评估接口：一组图片，同房间，返回一份汇总结果
@router.post("/analyze_group")
async def analyze_group_images(
    images: Annotated[list[UploadFile], File(description="多张同房间图片，最多5张")],
    temperature: float | None = None,
    humidity: float | None = None
):
    MAX_IMG_COUNT = 5
    if len(images) > MAX_IMG_COUNT:
        raise HTTPException(status_code=400, detail=f"单次最多上传{MAX_IMG_COUNT}张同房间照片")
    if len(images) < 1:
        raise HTTPException(status_code=400, detail="至少上传一张图片")

    img_b64_list = []
    filenames = []
    for upload_file in images:
        file_bytes = await upload_file.read()
        b64_str = base64.b64encode(file_bytes).decode("utf-8")
        img_b64_list.append(b64_str)
        filenames.append(upload_file.filename)

    # 调用一次，送入全部图片
    result = await llama_service.analyze_mold_group(
        image_b64_list=img_b64_list,
        filenames=filenames,
        temp=temperature,
        humidity=humidity
    )
    # 保存本组评估记录
    archive_path = await llama_service.save_group_json([result])
    return {
        "group_files": filenames,
        "temp": temperature,
        "humidity": humidity,
        "archive": archive_path,
        "report": result
    }