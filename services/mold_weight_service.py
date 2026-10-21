"""
霉菌风险加权评估服务
================================
设计原则：
1. 确定性：同一份输入（img_struct + temperature + humidity）永远输出同一份结果
2. 结构化：规则分组 → 特征提取 → 加权 → 定级 → 输出，每层独立可测
3. 同义词归组：LLaVA 措辞漂移时，只要命中组内任一词，就算同一条风险
"""
from typing import Dict, List, Tuple
from services.log_service import logger


# ============================================================
# 一、规则配置区（改规则只动这里，业务逻辑一行不用改）
# ============================================================

# 风险因子规则组：(同义词列表, 权重分, 命中后建议文案)
# 同义词列表里任一词被命中，即视为命中该因子
FEATURE_GROUPS: List[Tuple[List[str], int, str]] = [
    # ---- 高权重：直接可见的霉/水证据 ----
    (["霉斑", "黑斑", "黑色斑点", "黑灰斑块", "片状黑点", "发霉"],
     40, "墙面存在霉斑痕迹，优先做局部除霉处理，同时控制环境湿度"),

    (["积水", "地面积水", "地面积水"],
     35, "地面存在积水，及时擦干，保持地面干燥"),

    (["水珠", "冷凝水", "结露", "水珠流淌"],
     35, "观察到冷凝水珠，加强通风，降低室内湿度"),

    (["水渍", "水痕", "深色印", "深色痕迹", "水迹"],
     30, "墙面/顶面存在水渍痕迹，排查渗水源并持续观察"),

    (["管道凝露", "管道滴水", "水管表面水珠"],
     28, "管道外壁存在凝露，持续滴水会提高局部湿度，检查管道保温"),

    (["地漏积水", "地漏干涸", "地漏异味"],
     25, "地漏状态异常，容易滋生霉菌与异味，及时清理补水"),

    # ---- 中权重：结构/摆放问题 ----
    (["起皮", "鼓包", "墙皮脱落"],
     20, "墙皮起皮鼓包，可能存在渗水，建议检查墙体内部"),

    (["墙纸起翘", "墙纸脱胶", "壁纸翘边"],
     22, "墙纸起翘脱胶，大概率受潮，拆开检查背面是否长霉"),

    (["紧贴墙面", "紧靠墙面", "贴墙摆放", "靠墙"],
     20, "家具/杂物紧贴墙面摆放，建议与墙体预留空隙，利于空气流通"),

    (["关闭", "关窗", "窗户紧闭"],
     15, "窗户处于关闭状态，建议每日定时开窗通风换气"),

    (["密闭", "不通风", "空气不流通"],
     15, "空间相对密闭，建议增加通风频次"),

    # ---- 低权重：蓄湿物品/采光 ----
    (["纸箱", "硬纸箱", "纸箱子"],
     10, "室内堆放纸箱等易吸潮物品，建议远离墙面并定期清理"),

    (["被子", "被褥", "厚床品"],
     10, "床品被褥较厚，定期晾晒减少蓄湿"),

    (["布艺沙发", "布艺家具", "布艺窗帘"],
     10, "布艺家具/窗帘容易吸附潮气，定期通风除潮"),

    (["地毯", "地垫"],
     12, "地毯蓄湿性强，建议定期吸尘晾晒，避免底层长期潮湿"),

    (["昏暗", "光线差", "采光不足", "采光昏暗"],
     10, "区域采光较差，紫外线不足，难以抑制霉菌"),

    (["盆栽", "绿植", "花盆"],
     8, "墙角盆栽浇水易造成局部潮湿，建议移离墙面"),

    (["浮尘", "灰尘", "积灰"],
     5, "表面存在浮尘，定期清洁，避免粉尘成为霉菌载体"),

    (["蛛网", "蜘蛛网"],
     5, "角落有蛛网，长期未清洁，建议打扫"),

    # ---- 负权重：有利特征（减分） ----
    (["排风", "排风扇", "排气扇"],
     -8, "空间配有排风设备，持续排风有助于降低潮湿风险"),

    (["除湿机", "除湿设备"],
     -12, "现场配有除湿设备，合理开启可有效控制湿度抑制霉菌"),
]

# 否定词：关键词前面紧贴这些词，视为否定，不命中
NEGATION_WORDS = ["没有", "无", "未见", "未发现", "不存在", "无明显", "无可见"]

# 温湿度阈值（和 mode_rules.md 对齐）
HUMIDITY_RULES: List[Tuple[float, int, str]] = [
    # (阈值, 权重, 建议)
    (75, 30, "当前相对湿度{rh}%≥75%，极易滋生霉菌，优先除湿"),
    (65, 20, "当前相对湿度{rh}%处于霉菌快速繁殖区间，建议除湿至65%以下"),
    (55, 10, "当前相对湿度{rh}%已达霉菌萌发阈值，注意通风控湿"),
]

# 温度区间加分：18~28℃ 是霉菌最适繁殖温度
TEMP_OPTIMAL_RANGE = (18, 28)
TEMP_OPTIMAL_SCORE = 5
TEMP_OPTIMAL_SUGGEST = "当前温度{t}℃落在霉菌适宜繁殖区间，需配合湿度重点防控"

# 定级阈值
LEVEL_RULES: List[Tuple[int, str, str]] = [
    # (分数下限, riskLevel中文, riskClass css类)
    (60, "高风险", "risk-high"),
    (35, "中风险", "risk-medium"),
    (15, "初级风险", "risk-primary"),
    (0,  "低风险", "risk-low"),
]


# ============================================================
# 二、特征提取（LLaVA 文本 → 结构化命中列表）
# ============================================================

# 无效文本黑名单（LLaVA 偶尔吐出 prompt 碎片，直接过滤）
JUNK_PHRASES = [
    "玻璃洁净度", "采光通风", "墙面材质", "空间类型", "家具摆放",
    "床品情况", "顶面状态", "地面材质", "潮湿痕迹", "整体干净度",
]

def _is_negated(text: str, kw: str) -> bool:
    """检查 kw 前面是否紧跟否定词"""
    idx = text.find(kw.lower())
    if idx <= 0:
        return False
    prefix = text[max(0, idx - 3):idx]
    for neg in NEGATION_WORDS:
        if neg in prefix:
            return True
    return False

def _normalize_text(text: str) -> str:
    """文本归一化：去空白、统一小写，避免大小写/全半角问题"""
    return str(text).strip().lower()


def extract_features(img_struct: dict) -> List[Dict]:
    """
    输入：LLaVA 输出的结构化 dict
    输出：命中的特征列表
        [{"name": "霉斑", "weight": 40, "suggest": "...", "source_field": "wall_info"}, ...]
    """
    if isinstance(img_struct, str):
        import json
        img_struct = json.loads(img_struct)
    if not isinstance(img_struct, dict):
        return []

    logger.info(f"[mold_weight] 输入img_struct: {img_struct}")

    # 把所有字段文本拼成一个大文本，统一匹配（避免字段间割裂）
    all_text = ""
    for field_name, field_value in img_struct.items():
        if not field_value:
            continue
        val = str(field_value).strip()
        if val in ("未见", "无", "未知", "") or len(val) < 3:
            continue
        if any(jp in val for jp in JUNK_PHRASES):
            continue
        all_text += f" {val}"

    all_text = _normalize_text(all_text)
    logger.info(f"[mold_weight] 归一化后匹配文本: {all_text}")

    # 遍历规则组，组内任一关键词命中即记录
    hit_features = []
    for keywords, weight, suggest in FEATURE_GROUPS:
        for kw in keywords:
            if kw.lower() in all_text:
                if _is_negated(all_text, kw):
                    logger.info(f"[mold_weight] 关键词 {kw} 被否定词否定，忽略")
                    continue
                hit_features.append({
                    "name": keywords[0],   # 用组内第一个词作为规范名
                    "matched_keyword": kw,
                    "weight": weight,
                    "suggest": suggest,
                })
                break   # 同组只算一次

    logger.info(f"[mold_weight] 命中特征: {hit_features}")
    return hit_features


# ============================================================
# 三、加权计算（纯函数，输入确定 → 输出确定）
# ============================================================

def _humidity_contribution(humidity: float) -> Tuple[int, str]:
    """湿度加分，返回(分, 建议)"""
    for threshold, score, suggest_template in HUMIDITY_RULES:
        if humidity >= threshold:
            return score, suggest_template.format(rh=humidity)
    return 0, ""


def _temperature_contribution(temperature: float) -> Tuple[int, str]:
    """温度加分：落在霉菌适宜区间才加"""
    low, high = TEMP_OPTIMAL_RANGE
    if low <= temperature <= high:
        return TEMP_OPTIMAL_SCORE, TEMP_OPTIMAL_SUGGEST.format(t=temperature)
    return 0, ""


def _decide_level(total_score: int) -> Tuple[str, str]:
    """根据总分定级，返回(riskLevel中文, riskClass)"""
    for threshold, level, cls in LEVEL_RULES:
        if total_score >= threshold:
            return level, cls
    return "低风险", "risk-low"


# ============================================================
# 四、主入口：算分 + 定级 + 生成建议
# ============================================================

def calc_mold_weight_result(
    img_struct: dict,
    temperature: float | None = None,
    humidity: float | None = None,
) -> dict:
    """
    输入：
      img_struct   : LLaVA 视觉输出的结构化 dict（必须是 dict）
      temperature  : 实时温度 ℃，可空
      humidity     : 实时相对湿度 %，可空
    输出：
      {riskLevel, riskClass, desc, suggest, extraNote}
    """
    # 1. 图像特征命中
    features = extract_features(img_struct)

    total_score = 0
    suggestions = []   # [{weight, text}]

    for f in features:
        total_score += f["weight"]
        suggestions.append({"weight": f["weight"], "text": f["suggest"]})

    # 2. 湿度贡献（有值才算）
    if humidity is not None:
        h_score, h_suggest = _humidity_contribution(humidity)
        total_score += h_score
        if h_score:
            suggestions.append({"weight": h_score, "text": h_suggest})

    # 3. 温度贡献（有值才算）
    if temperature is not None:
        t_score, t_suggest = _temperature_contribution(temperature)
        total_score += t_score
        if t_score:
            suggestions.append({"weight": t_score, "text": t_suggest})

    # 4. 定级
    level, cls = _decide_level(total_score)

    # 5. 建议按权重降序排序
    suggestions.sort(key=lambda x: x["weight"], reverse=True)
    suggest_texts = [s["text"] for s in suggestions if s["text"]][0:3]  # 取前3条建议

    if not suggest_texts:
        suggest_texts = ["保持常规通风，定期监测温湿度即可"]

    logger.info(
        f"[mold_weight] 总分={total_score} 等级={level} 建议数={len(suggest_texts)}"
    )

    return {
        "riskLevel": level,
        "riskClass": cls,
        "desc": f"综合评估结果：{level}（总分{total_score}）",
        "suggest": "； ".join(suggest_texts)+"。",
        "extraNote": "基于图像特征关键词与实时温湿度加权计算，单张图片存在观测局限",
    }
