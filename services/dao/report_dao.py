from .db_pool import get_conn, release_conn
import json

async def insert_report_record(raw_input: dict, llm_result: dict, risk_level: str):
    conn = get_conn()
    cur = conn.cursor()
    sql = """
        INSERT INTO report_records(raw_input, llm_result, risk_level)
        VALUES (%s, %s, %s)
    """
    cur.execute(sql, (json.dumps(raw_input), json.dumps(llm_result), risk_level))
    conn.commit()
    cur.close()
    release_conn(conn)

async def list_report_records(page: int = 1, page_size: int = 10):
    conn = get_conn()
    cur = conn.cursor()
    offset = (page - 1) * page_size
    sql = """
        SELECT id, created_at, raw_input, llm_result, risk_level
        FROM report_records
        ORDER BY created_at DESC
        LIMIT %s OFFSET %s
    """
    cur.execute(sql, (page_size, offset))
    rows = cur.fetchall()
    cur.close()
    release_conn(conn)

    result = []
    for row in rows:
        result.append({
            "id": row[0],
            "time": row[1].isoformat(),
            "raw_input": row[2],
            "llm_result": row[3],
            "risk_level": row[4]
        })
    return result
