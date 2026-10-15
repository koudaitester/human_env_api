import psycopg2
import psycopg2.pool
import yaml
from typing import Optional

with open("config/db_config.yaml", "r", encoding="utf-8") as f:
    DB_CONFIG = yaml.safe_load(f)

CONNECTION_POOL: Optional[psycopg2.pool.SimpleConnectionPool] = None

def init_pool():
    global CONNECTION_POOL
    if CONNECTION_POOL is None:
        CONNECTION_POOL = psycopg2.pool.SimpleConnectionPool(
            minconn=2,
            maxconn=10,
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            dbname=DB_CONFIG["database"]
        )

def get_conn():
    if CONNECTION_POOL is None:
        init_pool()
    return CONNECTION_POOL.getconn()

def release_conn(conn):
    if CONNECTION_POOL and conn:
        CONNECTION_POOL.putconn(conn)

def close_all_pool():
    if CONNECTION_POOL:
        CONNECTION_POOL.closeall()
