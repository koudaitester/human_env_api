from .db_pool import get_conn, release_conn

async def insert_env_record(temp: float, hum: float, remark: str = ""):
    conn = get_conn()
    cur = conn.cursor()
    sql = """
        INSERT INTO env_record(temperature, humidity, remark)
        VALUES (%s, %s, %s)
    """
    cur.execute(sql, (temp, hum, remark))
    conn.commit()
    cur.close()
    release_conn(conn)

async def query_env_history(start_time: str | None = None, end_time: str | None = None, limit: int = 100):
    conn = get_conn()
    cur = conn.cursor()
    if start_time and end_time:
        sql = """
            SELECT created_at, temperature, humidity
            FROM env_record
            WHERE created_at BETWEEN %s AND %s
            ORDER BY created_at ASC LIMIT %s
        """
        params = [start_time, end_time, limit]
    else:
        sql = """
            SELECT created_at, temperature, humidity
            FROM env_record
            ORDER BY created_at ASC LIMIT %s
        """
        params = [limit]

    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    release_conn(conn)

    res = []
    for row in rows:
        res.append({
            "time": row[0].isoformat(),
            "temp": float(row[1]),
            "hum": float(row[2])
        })
    return res
