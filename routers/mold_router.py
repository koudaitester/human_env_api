from fastapi import APIRouter, UploadFile, File, Query
from services.llama_service import llama_service
import base64

router = APIRouter()

@router.post("/visual")
async def mold_visual(file: UploadFile = File(...)):
    img_bytes = await file.read()
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
    # 调用实例方法
    result = await llama_service.analyze_mold_visual(img_b64)
    return result

@router.post("/full")
async def mold_full(
    file: UploadFile = File(...),
    temp: float = Query(..., description="环境温度 ℃"),
    humidity: float = Query(..., description="相对湿度 %")
):
    img_bytes = await file.read()
    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
    result = await llama_service.analyze_mold_full(img_b64, temp, humidity)
    return result
