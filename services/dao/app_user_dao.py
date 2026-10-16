# services/dao/app_user_dao.py
from services.dao.db_pool import get_conn
from typing import Optional, Dict


def get_user_by_username(username: str) -> Optional[Dict]:
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM app_user WHERE username = %s", (username,))
        row = cur.fetchone()
        if row is None:
            return None
        description = cur.description
        if description is None:
            return None
        cols = [desc[0] for desc in description]
        return dict(zip(cols, row))
    finally:
        cur.close()
        conn.close()


def create_user(username: str, hashed_password: str, nickname: Optional[str] = None) -> Dict:
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO app_user (username, hashed_password, nickname)
               VALUES (%s, %s, %s) RETURNING *""",
            (username, hashed_password, nickname)
        )
        row = cur.fetchone()
        conn.commit()
        description = cur.description
        if row is None or description is None:
            raise RuntimeError("User insert did not return a row")
        cols = [desc[0] for desc in description]
        return dict(zip(cols, row))
    finally:
        cur.close()
        conn.close()
