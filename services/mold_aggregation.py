from collections import deque
from typing import Dict, Optional
import time
from services.log_service import logger

# 配置项，灰度阶段直接写在这里，后续再挪config
WINDOW_SIZE = 5
VOTE_THRESHOLD = 3
SESSION_EXPIRE_SEC = 30

# 内存存储：session_id -> {"queue": deque, "last_active": 时间戳}
SESSION_STORE: Dict[str, dict] = {}


def clean_expired_sessions():
    """清理超时会话，每次调用顺带执行"""
    now = time.time()
    expired_keys = []
    for sid, data in SESSION_STORE.items():
        if now - data["last_active"] > SESSION_EXPIRE_SEC:
            expired_keys.append(sid)
    for k in expired_keys:
        del SESSION_STORE[k]
        logger.info(f"[mold_aggregation] session expired, removed: {k}")


def aggregate_frame_result(session_id: str, frame_data: dict) -> dict:
    """
    送入单帧结果，返回聚合后的结果
    frame_data 传入结构：{"riskLevel": str, "riskClass": str, "hit_features": list}
    返回：
    {
        "aggregated": True,
        "riskLevel": str,
        "riskClass": str,
        "hit_features": list,
        "stable": bool
    }
    """
    clean_expired_sessions()
    now_ts = time.time()

    if session_id not in SESSION_STORE:
        SESSION_STORE[session_id] = {
            "queue": deque(maxlen=WINDOW_SIZE),
            "last_active": now_ts
        }
    sess = SESSION_STORE[session_id]
    sess["last_active"] = now_ts
    q = sess["queue"]

    q.append(frame_data)
    # 样本不足窗口大小，直接返回不稳定
    if len(q) < WINDOW_SIZE:
        return {
            "aggregated": True,
            "riskLevel": "无稳定风险",
            "riskClass": "risk-low",
            "hit_features": [],
            "stable": False
        }

    # 统计命中特征频次
    feature_count: Dict[str, int] = {}
    risk_count: Dict[str, int] = {}
    for item in q:
        for ft in item["hit_features"]:
            feature_count[ft] = feature_count.get(ft, 0) + 1
        risk_key = f"{item['riskLevel']}|{item['riskClass']}"
        risk_count[risk_key] = risk_count.get(risk_key, 0) + 1

    # 筛选达到阈值的特征
    stable_features = [k for k, v in feature_count.items() if v >= VOTE_THRESHOLD]
    stable_risk_item = None
    for key, cnt in risk_count.items():
        if cnt >= VOTE_THRESHOLD:
            level, cls = key.split("|")
            stable_risk_item = {"level": level, "cls": cls}
            break

    if stable_risk_item and stable_features:
        return {
            "aggregated": True,
            "riskLevel": stable_risk_item["level"],
            "riskClass": stable_risk_item["cls"],
            "hit_features": stable_features,
            "stable": True
        }
    else:
        return {
            "aggregated": True,
            "riskLevel": "无稳定风险",
            "riskClass": "risk-low",
            "hit_features": [],
            "stable": False
        }
