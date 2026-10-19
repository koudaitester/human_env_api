# routers/report_router.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from services.report_service import get_report_list, get_report_detail, get_conn
import json

router = APIRouter()

class ReportItem(BaseModel):
    report_id: int
    type: str
    create_time: datetime
    temp: Optional[float]
    hum: Optional[float]
    thumbnail: Optional[str]
    risk_level: str

class ReportDetail(ReportItem):
    result_json: dict

@router.get("/list", response_model=list[ReportItem])
async def get_report_list():
    conn = await get_conn()
    rows = await conn.fetch("""
        SELECT report_id, type, create_time, temp, hum, thumbnail, risk_level, result_json
        FROM report ORDER BY create_time DESC
    """)
    await conn.close()
    out = []
    for r in rows:
        d = dict(r)
        d["result_json"] = json.loads(d["result_json"])
        out.append(d)
    return out

@router.get("/{report_id}", response_model=ReportDetail)
async def get_report_detail(report_id:int):
    conn = await get_conn()
    row = await conn.fetchrow("SELECT * FROM report WHERE report_id = $1", report_id)
    await conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="记录不存在")
    data = dict(row)
    data["result_json"] = json.loads(data["result_json"])
    return data
