from fastapi import APIRouter, Body
from pydantic import BaseModel
from services import AudioService

router = APIRouter()

class AudioExtractReq(BaseModel):
    video_path: str
    output_mp3: str

@router.post("/extract")
async def audio_extract(req: AudioExtractReq = Body()):
    return await AudioService.extract_audio(req.video_path, req.output_mp3)
