from fastapi import APIRouter, UploadFile, File
from services.mold_stream_service import mold_stream_service
import base64

router = APIRouter()

@router.post("/frame")
async def feed_frame(file: UploadFile = File(...)):
    content = await file.read()
    b64 = base64.b64encode(content).decode("utf-8")
    single_result = await mold_stream_service.feed_frame(b64)
    return {"single_frame_result": single_result}

@router.get("/vote")
async def get_vote():
    return {"latest": mold_stream_service.get_latest_vote()}

@router.post("/clear")
async def clear_window():
    mold_stream_service.clear_window()
    return {"msg": "window cleared"}
