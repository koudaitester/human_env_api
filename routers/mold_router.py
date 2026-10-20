from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from services.llama_service import llama_service
import base64
from services.log_service import logger
import re
from services.report_service import save_report
import json
from typing import Annotated
from utils.deps import get_current_user
from utils.validator import validate_range
from services.mold_weight_service import calc_mold_weight_result

router = APIRouter()

# 全局常量
MAX_FILE_SIZE = 10 * 1024 * 1024  # 单文件最大10MB
ALLOWED_MIME = {"image/jpeg", "image/png"}


@router.post("/visual")
async def mold_visual(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
    ):
    # 文件校验
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="图片不能超过10MB")
    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(status_code=400, detail="仅支持 jpg / png 图片")

    img_bytes = await file.read()
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
    logger.info("霉菌检测视觉分析接口调用")
    # 调用实例方法
    result = await llama_service.analyze_mold_visual(img_b64)
    raw = re.sub(r'```(json)?', '', result["data"]).strip()
    # result["data"] = raw
    logger.info(f"霉菌检测视觉分析结果: {result}")
    #调用calc_mold_weight判断环境风险、建议
    img_struct = raw
    weight_result = calc_mold_weight_result(img_struct)
    logger.info(f"霉菌检测视觉分析加权结果: {weight_result}")
    result["data"] = weight_result
    return result

@router.post("/full")
async def mold_full(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    temperature: Annotated[float | None, Query(description="环境温度 ℃")] = None,
    humidity: Annotated[float | None, Query(description="相对湿度 %")] = None
):
    logger.info(f"霉菌检测全参数分析接口调用，温度: {temperature}, 湿度: {humidity}")
    # 文件校验
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="图片不能超过10MB")
    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(status_code=400, detail="仅支持 jpg / png 图片")

    # 非必传：有值才校验范围，为空直接跳过
    if temperature is not None:
        temperature = validate_range(temperature, -20, 60)
    if humidity is not None:
        humidity = validate_range(humidity, 0, 100)

    img_bytes = await file.read()
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
    user_id = current_user["id"]
    result = await llama_service.analyze_mold_full(img_b64, temperature, humidity)
    raw = re.sub(r'```(json)?', '', result["data"]).strip()
    logger.info(f"霉菌检测全参数分析原始结果: {raw}")
    try:
        data_dict = json.loads(raw)
    except json.JSONDecodeError:
        data_dict = {}
    risk_level = data_dict.get("riskLevel", "未知风险等级")
    result["data"] = data_dict
    logger.info(f"霉菌检测全参数分析结果: {result}")
    try:
        await save_report(
            type_str="image",
            temp=temperature,
            hum=humidity,
            thumbnail=None,
            result_json=result,
            risk_level=risk_level,
            user_id=user_id
        )
    except Exception as e:
        logger.exception("保存报告入库异常", exc_info=e)

    result["data"] = raw
    return result

# 多图综合评估接口：一组图片，同房间，返回一份汇总结果
@router.post("/analyze_group")
async def analyze_group_images(
    images: Annotated[list[UploadFile], File(description="多张同房间图片，最多5张")],
    temperature: Annotated[float | None, Query(description="环境温度 ℃")] = None,
    humidity: Annotated[float | None, Query(description="相对湿度 %")] = None
):
    MAX_IMG_COUNT = 5
    if len(images) > MAX_IMG_COUNT:
        raise HTTPException(status_code=400, detail=f"单次最多上传{MAX_IMG_COUNT}张同房间照片")
    if len(images) < 1:
        raise HTTPException(status_code=400, detail="至少上传一张图片")

    # 批量校验每张图片
    for upload_file in images:
        if upload_file.size and upload_file.size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"文件 {upload_file.filename} 超过10MB上限")
        if upload_file.content_type not in ALLOWED_MIME:
            raise HTTPException(status_code=400, detail=f"文件 {upload_file.filename} 仅支持 jpg/png")

    # 可选校验：如果传了温湿度，则校验范围
    if temperature is not None:
        temperature = validate_range(temperature, -20, 60)
    if humidity is not None:
        humidity = validate_range(humidity, 0, 100)

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
        temperature=temperature,
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
