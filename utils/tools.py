import re
import json

def parse_json_safely(raw: str):
    # 剥离markdown代码标记
    raw = re.sub(r"```(json)?", "", raw).strip()
    return json.loads(raw)
