from fastapi import APIRouter
from pydantic import BaseModel
from services.video_service import video_service
from utils.common import success_resp, fail_resp
import threading

router = APIRouter(prefix="/video", tags=["AI视频生成"])

class VideoCreateReq(BaseModel):
    prompt: str

@router.post("/create")
async def create_video_task(req: VideoCreateReq):
    task_id = video_service.create_task(req.prompt)
    return success_resp(data={"task_id": task_id})

@router.get("/task/{task_id}")
async def get_video_task(task_id: str):
    task = video_service.get_task(task_id)
    if not task:
        return fail_resp(msg="任务不存在")
    return success_resp(data=task)