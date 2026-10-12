from fastapi import APIRouter, Body
from pydantic import BaseModel
from services import RagService

router = APIRouter()

class RagSearchReq(BaseModel):
    query: str
    top_k: int = 3

@router.post("/search")
async def rag_search(req: RagSearchReq = Body()):
    return await RagService.search_knowledge(req.query, req.top_k)
