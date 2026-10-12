from fastapi import APIRouter, Body
from pydantic import BaseModel
from services import LlmService

router = APIRouter()

class ChatReq(BaseModel):
    prompt: str
    system_prompt: str | None = None

@router.post("/chat")
async def llm_chat(req: ChatReq = Body()):
    return await LlmService.chat_completion(req.prompt, req.system_prompt)
