from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
import hashlib

# 改成你自己的密钥，生产环境放配置文件！不要硬编码
SECRET_KEY = "your-secret-key-change-me-in-prod"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

# 自定义盐值，可自行修改
SALT = "human_env_salt_2026"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    hash_val = hashlib.sha256((plain_password + SALT).encode("utf-8")).hexdigest()
    return hash_val == hashed_password

def get_password_hash(password: str) -> str:
    return hashlib.sha256((password + SALT).encode("utf-8")).hexdigest()

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
