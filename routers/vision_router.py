from fastapi import APIRouter, UploadFile, File, Form
from services import VisionService

router = APIRouter()

@router.post("/analyze_image")
async def analyze_image(
    prompt: str = Form(default="请识别图片内人居环境，找出风险点"),
    file: UploadFile = File(...)
):
    # 保存上传图片到临时目录
    tmp_path = f"./tmp/{file.filename}"
    with open(tmp_path, "wb") as f:
        f.write(await file.read())
    res = await VisionService.image_analyze(tmp_path, prompt)
    return res