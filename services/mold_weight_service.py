import re
from typing import Dict, List, Tuple
from services.log_service import logger

# ========== 权重规则表 ==========
# 关键词 → (权重分, 命中后追加的建议文案)
FEATURE_RULES: List[Tuple[str, int, str]] = [
    ("霉斑",       40, "墙面存在霉斑痕迹，优先做局部除霉处理，同时控制环境湿度"),
    ("积水",       35, "地面存在积水，及时擦干，保持地面干燥"),
    ("水珠",       35, "观察到冷凝水珠，加强通风，降低室内湿度"),
    ("水渍",       30, "墙面/顶面存在水渍痕迹，排查渗水源并持续观察"),
    ("深色痕迹",   15, "墙面有可疑深色痕迹，建议近距离确认是否为水渍或霉斑"),
    ("起皮",       20, "墙皮起皮鼓包，可能存在渗水，建议检查墙体内部"),
    ("紧贴墙面",   20, "家具/杂物紧贴墙面摆放，建议与墙体预留空隙，利于空气流通"),
    ("纸箱",       10, "室内堆放纸箱等易吸潮物品，建议远离墙面并定期清理"),
    ("盆栽",       8,  "墙角盆栽浇水易造成局部潮湿，建议移离墙面"),
    ("被子",       10, "床品被褥较厚，定期晾晒减少蓄湿"),
    ("关闭",       15, "窗户处于关闭状态，建议每日定时开窗通风换气"),
    ("昏暗",       10, "区域采光较差，紫外线不足，难以抑制霉菌"),
    ("密闭",       15, "空间相对密闭，建议增加通风频次"),
    ("浮尘",       5,  "表面存在浮尘，定期清洁，避免粉尘成为霉菌载体"),
    ("蛛网",       5,  "角落有蛛网，长期未清洁，建议打扫"),
]

# 温湿度阈值加分（和 mode_rules.md 对齐）
def _humidity_score(humidity: float) -> Tuple[int, str]:
    if humidity >= 75:
        return 30, f"当前相对湿度{humidity}%≥75%，极易滋生霉菌，优先除湿"
    elif humidity >= 65:
        return 20, f"当前相对湿度{humidity}%处于霉菌快速繁殖区间，建议除湿至65%以下"
    elif humidity >= 55:
        return 10, f"当前相对湿度{humidity}%已达霉菌萌发阈值，注意通风控湿"
    else:
        return 0, ""

def _temp_score(t: float) -> Tuple[int, str]:
    # 18~28℃ 是霉菌最适区间
    if 18 <= t <= 28:
        return 5, f"当前温度{t}℃落在霉菌适宜繁殖区间，需配合湿度重点防控"
    return 0, ""


# ========== 特征提取：从 LLaVA 的 12 个字段里抽关键词 ==========
def extract_features(img_struct: dict) -> List[Dict]:
    if isinstance(img_struct, str):
        import json
        img_struct = json.loads(img_struct)
    if not isinstance(img_struct, dict):
        return []

    logger.info(f"提取图像结构化特征，输入字段: {img_struct}")

    hit_features = []
    for field_name, field_value in img_struct.items():
        if not field_value or field_value in ("未见", "无", "未知", ""):
            continue
        text = str(field_value).strip()
        # 过滤：太短、明显是字段提示碎片直接跳过
        if len(text) < 5:
            continue
        # 黑名单：这些是我们prompt里的字段描述词，命中直接跳过
        junk_words = ["玻璃洁净度", "采光通风", "墙面材质", "空间类型", "家具摆放", "床品情况"]
        if any(jw in text for jw in junk_words):
            continue

        for keyword, weight, suggest in FEATURE_RULES:
            if keyword in text:
                hit_features.append({
                    "keyword": keyword,
                    "weight": weight,
                    "suggest": suggest,
                    "source_field": field_name,
                })
    seen = set()
    uniq = []
    for f in hit_features:
        if f["keyword"] not in seen:
            seen.add(f["keyword"])
            uniq.append(f)
    return uniq

# ========== 主函数：算分 + 定级 + 生成建议 ==========
def calc_mold_weight_result(img_struct: dict, temperature: float|None=None, humidity: float|None=None) -> dict:
    """
    输入：
      img_struct   : LLaVA 视觉输出的结构化 dict
      temperature  : 实时温度 ℃
      humidity     : 实时相对湿度 %
    输出：
      {riskLevel, riskClass, desc, suggest, extraNote}
    """
    features = extract_features(img_struct)

    total_score = 0
    risk_factors = []
    suggestions = []

    # 1. 图像特征贡献
    for f in features:
        total_score += f["weight"]
        risk_factors.append({
            "name": f["keyword"],
            "desc": f"从图像字段[{f['source_field']}]中识别到",
            "weight": f["weight"],
        })
        suggestions.append({"weight": f["weight"], "text": f["suggest"]})

    # 2. 湿度贡献
    if humidity is not None:
        h_score, h_suggest = _humidity_score(humidity)
        total_score += h_score
        if h_score:
            risk_factors.append({"name": "环境湿度", "desc": f"RH={humidity}%", "weight": h_score})
            suggestions.append({"weight": h_score, "text": h_suggest})

    # 3. 温度贡献
    if temperature is not None:
        t_score, t_suggest = _temp_score(temperature)
        total_score += t_score
        if t_score:
            risk_factors.append({"name": "环境温度", "desc": f"T={temperature}℃", "weight": t_score})
            suggestions.append({"weight": t_score, "text": t_suggest})

    # 4. 定级
    if total_score >= 60:
        level, cls = "高风险", "risk-high"
    elif total_score >= 35:
        level, cls = "中风险", "risk-medium"
    elif total_score >= 15:
        level, cls = "中风险", "risk-primary"
    else:
        level, cls = "低风险", "risk-low"

    # 5. 建议按权重降序，取前4条
    suggestions.sort(key=lambda x: x["weight"], reverse=True)
    suggest_texts = [s["text"] for s in suggestions[:4]]
    if not suggest_texts:
        suggest_texts = ["保持常规通风，定期监测温湿度即可"]

    return {
        "riskLevel": level,
        "riskClass": cls,
        # "totalScore": total_score,
        "desc": f"综合评估结果：{level}",
        "suggest": suggest_texts[0] if suggest_texts else "保持常规通风，定期监测温湿度即可",
        "extraNote": "基于图像特征关键词与实时温湿度加权计算，单张图片存在观测局限",
    }
