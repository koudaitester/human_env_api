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
import re


# ============================================================
# 一、规则配置区（改规则只动这里，业务逻辑一行不用改）
# ============================================================

# 风险因子规则组：(同义词列表, 权重分, 命中后建议文案)
# 同义词列表里任一词被命中，即视为命中该因子
FEATURE_GROUPS: List[Tuple[List[str], int, str]] = [
    # ========== 病灶类（强权重，核心定级依据） ==========
    (["深色斑块"],
     81, "墙面识别到深色斑块样痕迹，有可能是霉斑、污渍，此模型只做辅助评估；建议近距离实地观察，触摸辨别，同步控制环境湿度"),

    # (["点状深色小点"],
    #  80, "墙面存在点状深色小点/霉菌斑块，有可能是微小霉点、污渍，此模型只做辅助评估；建议近距离确认，及时清洁并控制湿度"),

    (["积水", "地面积水"],
     30, "地面存在积水，及时擦干，保持地面干燥"),

    (["起皮", "鼓包", "墙皮脱落"],
     25, "墙皮起皮鼓包，大概率受潮，建议检查墙体内部渗水"),

    (["水痕印记"],
     20, "墙面存在水痕印记，排查渗水源并持续观察"),

    (["水珠", "冷凝水", "结露"],
     12, "观察到冷凝水珠，加强通风，降低室内湿度"),

    # ========== 诱因类（弱权重，只做加分，无病灶时封顶20） ==========
    (["紧贴墙面", "紧靠墙面", "贴墙摆放", "靠墙"],
     6, "家具/杂物紧贴墙面摆放，建议预留空隙，减少受潮发霉风险"),

    (["纸箱", "硬纸箱", "纸箱子"],
     6, "室内堆放易吸潮纸箱，建议远离墙面并定期清理"),

    (["被子", "被褥", "厚床品"],
     5, "厚床品容易蓄积潮气，建议定期晾晒"),

    (["布艺沙发", "布艺家具", "布艺窗帘"],
     5, "布艺织物容易吸附潮气，定期通风晾晒"),

    (["地毯", "地垫"],
     7, "地毯容易蓄积潮气，定期吸尘干燥"),

    (["昏暗", "光线差", "采光不足", "采光昏暗"],
     5, "区域采光昏暗，紫外线不足，不利于抑制霉菌"),

    (["盆栽", "绿植", "花盆"],
     4, "盆栽浇水容易增加局部湿度，尽量远离墙体"),

    (["浮尘", "灰尘", "积灰"],
     3, "表面积灰，灰尘容易附着潮气，定期清洁"),

    (["蛛网", "蜘蛛网"],
     3, "角落存在蛛网，建议清洁，保持环境干燥"),

    (["关闭", "关窗", "窗户紧闭"],
     5, "窗户处于关闭状态，建议每日定时开窗通风换气"),

    (["密闭", "不通风", "空气不流通"],
     5, "空间相对密闭，建议增加通风频次"),

    # ========== 有利减分项 ==========
    (["排风", "排风扇", "排气扇"],
     -8, "空间配有排风设备，合理开启可以降低潮湿风险"),

    (["除湿机", "除湿设备"],
     -12, "现场配有除湿设备，合理使用能够抑制霉菌滋生"),
]

# 否定词：关键词前面紧贴这些词，视为否定，不命中
NEGATION_WORDS = ["没有", "无", "未见", "未发现", "不存在", "无明显", "无可见", "没有可见"]

# 互斥分组配置
MUTEX_GROUPS = [
    {"keys": ["点状深色小点", "深色斑块"], "desc": "深色痕迹同源互斥"},
    {"keys": ["水痕印记", "水渍印记"], "desc": "水痕同源互斥"},
]

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
    (81, "高风险", "risk-high"),
    (41, "中风险", "risk-medium"),
    (21, "初级风险", "risk-primary"),
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

def resolve_mutex_features(hit_features: list[dict], mutex_groups: list[dict]) -> list[dict]:
    """
    同源特征互斥去重算法
    :param hit_features: 原始命中特征列表
    :param mutex_groups: 互斥组配置，格式：[{"keys": ["A","B"], "desc": "说明"}]
    :return: 去重之后的特征列表，同组只保留权重最高一条
    """
    result = hit_features.copy()
    for group in mutex_groups:
        group_keys = group["keys"]
        # 筛选当前命中里属于这个互斥组的项
        group_items = [item for item in result if item["name"] in group_keys]
        if len(group_items) <= 1:
            continue
        # 按权重倒序，保留最高分那条
        group_items.sort(key=lambda x: x["weight"], reverse=True)
        keep_item = group_items[0]
        # 删除本组其他条目
        result = [x for x in result if x not in group_items or x == keep_item]
        logger.info(f"[mold_weight][mutex] {group['desc']}, 保留特征: {keep_item['name']} weight={keep_item['weight']}")
    return result

def _is_negated(text: str, kw: str) -> bool:
    kw_lower = kw.lower()
    sentences = re.split(r"[，。；]", text)
    # 预清洗分句：去空白
    sentences = [s.strip() for s in sentences if s.strip()]
    
    for i, sent in enumerate(sentences):
        sent_lower = sent.lower()
        if kw_lower not in sent_lower:
            continue

        m = re.search(r"(无|没有)\s*([^。；!?]+)", sent_lower)
        if m:
            parts = [p.strip() for p in re.split(r"[，、]", m.group(2)) if p.strip()]
            if kw_lower in parts:
                return True

        # 规则1：当前分句内就同时有否定词
        for neg in NEGATION_WORDS:
            if neg in sent_lower:
                # 是否问句里实体白名单保留
                if "是否" in sent_lower:
                    continue
                return True
        # 规则2：当前分句是「是否XX」，后面紧邻的下一个分句是纯「未见/无」
        if "是否" in sent_lower and i + 1 < len(sentences):
            next_sent = sentences[i+1].lower()
            if next_sent in ("未见", "无"):
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
        if val in ("未见", "无", "未知", ""):
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

#弱因子封顶分数接口
def calc_inducer_cap_score(hit_features: List[dict]) -> tuple[int, int, int]:
    """
    区分病灶 / 诱因 / 有利减分，实现【无病灶时诱因封顶20】规则
    :param hit_features: 经过互斥去重后的命中特征列表
    :return: (lesion_score, inducer_score, benefit_score)
    """
    LESION_KEYWORDS = {"深色斑块", "点状深色小点", "积水", "起皮", "水痕印记", "水珠"}
    MAX_PURE_INDUCER = 20

    lesion_score = 0
    inducer_raw = 0
    benefit_score = 0

    for f in hit_features:
        kw = f["matched_keyword"]
        w = f["weight"]
        if kw in LESION_KEYWORDS:
            lesion_score += w
        elif w > 0:
            inducer_raw += w
        else:
            benefit_score += w

    if lesion_score > 0:
        # 存在病灶，诱因不封顶
        inducer_score = inducer_raw
    else:
        # 只有诱因，封顶
        inducer_score = min(inducer_raw, MAX_PURE_INDUCER)

    return lesion_score, inducer_score, benefit_score

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
    # 互斥组去重
    features = resolve_mutex_features(features, MUTEX_GROUPS)

    # 调用抽出来的分数计算
    lesion_score, inducer_score, benefit_score = calc_inducer_cap_score(features)

    img_total = lesion_score + inducer_score + benefit_score
    img_total = max(0, img_total)

    total_score = img_total
    suggestions = [{"weight": f["weight"], "text": f["suggest"]} for f in features]

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

    # 4. 定级&score上线100
    level, cls = _decide_level(total_score)
    total_score = min(total_score, 100)

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
