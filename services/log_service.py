import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

LOG_DIR = "log"
os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger("env_project")
logger.setLevel(logging.INFO)
logger.propagate = False

log_format = logging.Formatter(
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# 轮转：单个文件最大5MB，最多保留5个备份
file_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, f"{datetime.now().strftime('%Y%m%d')}.log"),
    maxBytes=5*1024*1024,
    backupCount=5,
    encoding="utf-8"
)
file_handler.setFormatter(log_format)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_format)

logger.addHandler(file_handler)
logger.addHandler(console_handler)