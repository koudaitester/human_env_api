import asyncpg
from typing import Optional, List, Dict, Any
import json
from services.log_service import logger

# 数据库连接配置
DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 5432,
    "user": "postgres",
    "password": "123456",
    "database": "human_env_db"
}

async def get_conn():
    conn = await asyncpg.connect(**DB_CONFIG)
    return conn


# 新增：获取报告列表，按创建时间倒序
async def get_report_list() -> List[Dict[str, Any]]:
    conn = await get_conn()
    rows = await conn.fetch("""
        SELECT report_id, type, create_time, temp, hum, thumbnail, risk_level
        FROM report ORDER BY create_time DESC
    """)
    await conn.close()
    return [dict(r) for r in rows]


# 新增：单条报告详情查询
async def get_report_detail(report_id: int) -> Optional[Dict[str, Any]]:
    conn = await get_conn()
    row = await conn.fetchrow("SELECT * FROM report WHERE report_id = $1", report_id)
    await conn.close()
    if row:
        return dict(row)
    return None

async def save_report(
    type_str: str,
    temp: Optional[float],
    hum: Optional[float],
    thumbnail: Optional[str],
    result_json: dict,
    risk_level: str
) -> int:
    conn = await get_conn()
    logger.info(f"连接数据库成功: {conn}")
    # 核心修复：字典转json字符串
    json_str = json.dumps(result_json, ensure_ascii=False)
    sql = """
        INSERT INTO report(type, temp, hum, thumbnail, result_json, risk_level)
        VALUES($1,$2,$3,$4,$5,$6) RETURNING report_id
    """
    new_id = await conn.fetchval(sql, type_str, temp, hum, thumbnail, json_str, risk_level)
    logger.info(f"报告保存成功，report_id: {new_id}")
    await conn.close()
    return new_id