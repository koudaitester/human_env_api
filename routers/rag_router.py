from fastapi import APIRouter, Body
from pydantic import BaseModel
from services import RagService
from services.log_service import logger

router = APIRouter()

class RagSearchReq(BaseModel):
    query: str
    top_k: int = 3

@router.post("/search")
async def rag_search(req: RagSearchReq = Body()):
    logger.info(f"知识库检索接口调用，query: {req.query}, top_k: {req.top_k}")
    return await RagService.search_knowledge(req.query, req.top_k)
