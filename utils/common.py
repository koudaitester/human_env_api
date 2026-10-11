from pydantic import BaseModel

def success_resp(data, msg="ok"):
    return {"code": 0, "msg": msg, "data": data}

def fail_resp(msg="error", code=-1):
    return {"code": code, "msg": msg, "data": None}