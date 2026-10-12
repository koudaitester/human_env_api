from fastapi import APIRouter, Body
from pydantic import BaseModel
from services import VisionService

router = APIRouter()

class VisionAnalyzeReq(BaseModel):
    image_path: str
    prompt: str

@router.post("/analyze")
async def vision_analyze(req: VisionAnalyzeReq = Body()):
    return await VisionService.image_analyze(req.image_path, req.prompt)
