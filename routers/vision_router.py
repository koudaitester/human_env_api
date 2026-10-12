from fastapi import APIRouter, UploadFile, File, Form
from services import VisionService
import base64

router = APIRouter()
vision_service = VisionService()

@router.post("/analyze_image")
async def analyze_image(file: UploadFile = File(...)):
    # 1.读取上传文件二进制
    file_bytes = await file.read()
    # 2.编码成base64纯字符串（不带data:image前缀）
    image_b64 = base64.b64encode(file_bytes).decode("utf-8")
    # 3.传给service
    result = await vision_service.image_analyze(image_base64=image_b64)
    return result