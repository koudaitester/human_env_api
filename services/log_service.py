import logging
import os
from datetime import datetime

# 日志根目录
LOG_DIR = "log"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR, exist_ok=True)

# 日志文件名按日期
log_filename = os.path.join(LOG_DIR, f"{datetime.now().strftime('%Y%m%d')}.log")

# 日志格式
log_format = logging.Formatter(
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# 创建logger实例
logger = logging.getLogger("env_project")
logger.setLevel(logging.INFO)
logger.propagate = False

# 文件handler
file_handler = logging.FileHandler(log_filename, encoding="utf-8")
file_handler.setFormatter(log_format)

# 控制台handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_format)

# 挂载
logger.addHandler(file_handler)
logger.addHandler(console_handler)
