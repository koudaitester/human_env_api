from fastapi import APIRouter, Body
from pydantic import BaseModel
from services import EnvService

router = APIRouter()

class EnvEvaluateReq(BaseModel):
    params: dict
    knowledge_list: list | None = None

@router.post("/evaluate")
async def env_evaluate(req: EnvEvaluateReq = Body()):
    knowledge = req.knowledge_list or []
    return await EnvService.evaluate_env(req.params, knowledge)
