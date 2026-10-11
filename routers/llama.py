from fastapi import APIRouter
from pydantic import BaseModel
from services.llama_service import llama_service
from utils.common import success_resp

router = APIRouter(prefix="/llama", tags=["本地Llama大模型"])

class LlamaChatReq(BaseModel):
    prompt: str

@router.post("/chat")
async def llama_chat(req: LlamaChatReq):
    result = await llama_service.chat(req.prompt)
    return success_resp(data={"reply": result})
