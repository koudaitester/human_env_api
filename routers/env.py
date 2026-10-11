from fastapi import APIRouter
from pydantic import BaseModel
from services.env_service import env_service
from utils.common import success_resp, fail_resp

router = APIRouter(prefix="/env", tags=["人居环境"])

class PurifierCheckReq(BaseModel):
    angle: int
    is_sleep: bool

@router.post("/purifier/check")
async def purifier_check(req: PurifierCheckReq):
    res = env_service.check_air_purifier_rule(req.angle, req.is_sleep)
    if res["ok"]:
        return success_resp(data=res)
    return fail_resp(msg=res["reason"])