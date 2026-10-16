# services/user_service.py
from services.dao.app_user_dao import get_user_by_username as dao_get_user_by_username, create_user as dao_create_user
from utils.security import get_password_hash, verify_password
from typing import Optional, Dict

def get_user_by_username(username: str):
    return dao_get_user_by_username(username)

def create_user(username: str, password: str, nickname: str = None):
    hashed_pw = get_password_hash(password)
    return dao_create_user(username, hashed_pw, nickname)

def authenticate_user(username: str, password: str) -> Optional[Dict]:
    user = get_user_by_username(username)
    if not user:
        return None
    if not verify_password(password, user["hashed_password"]):
        return None
    return user
