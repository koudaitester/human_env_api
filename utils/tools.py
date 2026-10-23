import re
import json
from PIL import Image
import io
import base64

def parse_json_safely(raw: str):
    # 剥离markdown代码标记
    raw = re.sub(r"```(json)?", "", raw).strip()
    return json.loads(raw)

def resize_image_for_llava(img_b64: str, target_size: int = 672) -> str:
    # base64转图片
    img_data = base64.b64decode(img_b64)
    img = Image.open(io.BytesIO(img_data)).convert("RGB")

    # 等比例缩放，长边限制到target_size，保持原图比例，不变形
    w, h = img.size
    if max(w, h) > target_size:
        scale = target_size / max(w, h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # 转回base64
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode("utf-8")
