from fastapi import APIRouter
from utils.common import success_resp

router = APIRouter(prefix="/health", tags=["健康检查"])

@router.get("/")
async def health_check():
    return success_resp(data={"status": "running"})