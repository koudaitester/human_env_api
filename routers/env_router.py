from fastapi import APIRouter, Body
from pydantic import BaseModel
from services import EnvService

router = APIRouter()

class EnvEvaluateReq(BaseModel):
    pm25: float
    temperature: float
    humidity: float
    knowledge_list: list | None = None

@router.post("/evaluate")
async def env_evaluate(req: EnvEvaluateReq):
    knowledge = req.knowledge_list or []
    return await EnvService.evaluate_env(
        params={
            "pm25": req.pm25,
            "temperature": req.temperature,
            "humidity": req.humidity
        },
        knowledge_list=knowledge
    )
