"""
霉菌风险加权评估服务
================================
设计原则：
1. 确定性：同一份输入（img_struct + temperature + humidity）永远输出同一份结果
2. 结构化：规则分组 → 特征提取 → 加权 → 定级 → 输出，每层独立可测
3. 同义词归组：LLaVA 措辞漂移时，只要命中组内任一词，就算同一条风险
"""
from asyncio import log
from typing import Dict, List, Tuple
from services.log_service import logger
import re


# ============================================================
# 一、规则配置区（改规则只动这里，业务逻辑一行不用改）
# ============================================================

# 风险因子规则组：(同义词列表, 权重分, 命中后建议文案)
# 同义词列表里任一词被命中，即视为命中该因子
# ============================================================
# 一、规则配置区（改规则只动这里，业务逻辑一行不用改）
# ============================================================

from typing import List, Tuple

# 特征关键词
def parse_feature_groups(rule_text: str):
    groups: List[Tuple[List[str], int, str]] = []
    mutex_groups: List[dict] = []
    negation_words: List[str] = []
    humidity_rules: List[str] = []
    lesion_kw_list: List[str] = []
    temp_config = {"low":18.0, "high":28.0, "score":5, "template":""}
    level_rules = []
    soft_downgrade_rules: List[Tuple[str, str, str, int, str]] = []
    soft_append_rules: List[Tuple[str, str, int, str]] = []

    lines = [line.strip() for line in rule_text.splitlines() if line.strip()]
    section = None
    for line in lines:
        if line.startswith("# "):
            section = line[2:].strip()
            continue
        if section == "FEATURE_GROUPS":
            parts = line.split("||")
            if len(parts) != 3:
                continue
            kw_list = [w.strip() for w in parts[0].split(",") if w.strip()]
            score = int(parts[1].strip())
            suggest = parts[2].strip()
            groups.append((kw_list, score, suggest))
        elif section == "MUTEX_GROUPS":
            parts = line.split("||")
            if len(parts) != 2:
                continue
            import ast
            try:
                key_list = ast.literal_eval(parts[0])
                desc = parts[1].strip()
                mutex_groups.append({"keys": key_list, "desc": desc})
            except Exception as e:
                logger.warning(f"解析互斥组失败 line={line}, err={e}")
        elif section == "NEGATION_WORDS":
            negation_words = [w.strip() for w in line.split(",") if w.strip()]
        elif section == "HUMIDITY_RULES":
            parts = line.split("||")
            if len(parts) != 3:
                continue
            try:
                th = float(parts[0].strip())
                sc = int(parts[1].strip())
                tp = parts[2].strip()
                humidity_rules.append((th, sc, tp))
            except Exception as e:
                logger.warning(f"解析湿度规则失败 line={line}, err={e}")
        elif section == "TEMP_CONFIG":
            parts = line.split("||")
            if len(parts) != 3:
                continue
            try:
                range_str = parts[0].strip()
                low, high = [float(x) for x in range_str.split(",")]
                sc = int(parts[1].strip())
                tp = parts[2].strip()
                temp_config["low"] = low
                temp_config["high"] = high
                temp_config["score"] = sc
                temp_config["template"] = tp
            except Exception as e:
                logger.warning(f"解析温度配置失败 line={line}, err={e}")
        elif section == "LEVEL_RULES":
            parts = line.split("||")
            if len(parts) != 3:
                continue
            try:
                th = int(parts[0].strip())
                lv = parts[1].strip()
                cls = parts[2].strip()
                level_rules.append((th, lv, cls))
            except Exception as e:
                logger.warning(f"解析定级规则失败 line={line}, err={e}")
        elif section == "SOFT_DOWNGRADE_RULES":
            parts = line.split("||")
            if len(parts) !=5:
                continue
            try:
                pat_raw = parts[0].strip()
                action = parts[1].strip()
                t_name = parts[2].strip()
                sc = int(parts[3].strip())
                msg = parts[4].strip()
                soft_downgrade_rules.append((pat_raw, action, t_name, sc, msg))
            except Exception as e:
                logger.warning(f"解析降级软规则失败 line={line}, err={e}")
        elif section == "SOFT_APPEND_FEATURE_RULES":
            parts = line.split("||")
            if len(parts) !=4:
                continue
            try:
                pat_raw = parts[0].strip()
                t_name = parts[1].strip()
                sc = int(parts[2].strip())
                msg = parts[3].strip()
                soft_append_rules.append((pat_raw, t_name, sc, msg))
            except Exception as e:
                logger.warning(f"解析追加软规则失败 line={line}, err={e}")
        elif section == "LESION_KEYWORDS":
            lesion_kw_list = [w.strip() for w in line.split(",") if w.strip()]
        elif section == "MAX_PURE_INDUCER":
            MAX_PURE_INDUCER = int(line.strip())
    return groups, mutex_groups, negation_words, humidity_rules, temp_config, level_rules, soft_downgrade_rules, soft_append_rules, lesion_kw_list

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

def _is_negated(text: str, kw: str, negation_words: List) -> bool:
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
        for neg in negation_words:
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

def extract_features(img_struct: dict, feature_group: List, negation_words: List, soft_downgrade_raw: List, soft_append_raw: List) -> List[Dict]:
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

    # 优先取moondream带过来的完整原始文本，没有再用字段拼接兜底
    raw_full_text = img_struct.pop("__raw_text__", None)
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
    logger.info("raw_full_text: " + raw_full_text)
    for keywords, weight, suggest in feature_group:
        for kw in keywords:
            if kw.lower() in raw_full_text:
                if _is_negated(raw_full_text, kw, negation_words):
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
    # ========== 软降级：编译正则，替换原来写死的if-re 块 ==========
    # 编译降级规则
    downgrade_compiled = []
    for pat_str, action, t_name, sc, msg in soft_downgrade_raw:
        try:
            downgrade_compiled.append((re.compile(pat_str, re.IGNORECASE), action, t_name, sc, msg))
        except Exception as e:
            logger.warning(f"软降级正则编译失败 {pat_str}: {e}")
    # 编译追加规则
    append_compiled = []
    for pat_str, t_name, sc, msg in soft_append_raw:
        try:
            append_compiled.append((re.compile(pat_str, re.IGNORECASE), t_name, sc, msg))
        except Exception as e:
            logger.warning(f"追加正则编译失败 {pat_str}: {e}")

    if raw_full_text is not None:
        # ===================== 原有逻辑【深色斑块专属消歧义】，原样保留 =====================
        for f in hit_features:
            if f["name"] != "深色斑块":
                continue
            for pat, action, t_name, sc, msg in downgrade_compiled:
                if pat.search(raw_full_text):
                    if action == "keep":
                        logger.info(f"[mold_weight][soft_rule] 识别到描述 {pat.pattern}，保留原有高分")
                        continue
                    elif action == "convert":
                        logger.info(f"[mold_weight][soft_rule] 识别到描述 {pat.pattern}")
                        f["name"] = t_name
                        f["weight"] = sc
                        f["suggest"] = msg
                        logger.info("[mold_weight][soft_rule] mold spot 降级为普通水渍")
                        break

        # 追加 water stain / water mark 特征
        for pat, t_name, sc, msg in append_compiled:
            if pat.search(raw_full_text):
                logger.info(f"[mold_weight][soft_rule] 识别到水渍描述 {pat.pattern}")
                hit_features.append({
                    "name": t_name,
                    "matched_keyword": pat.pattern,
                    "weight": sc,
                    "suggest": msg
                })

        # ========== === 修改新增：通用消歧义分支 start ==========
        # 读取soft_downgrade_raw里的特殊标记，区分「深色斑块规则」和「通用抵消规则」
        # 约定md里通用消歧义 action = "offset"，t_name 是目标特征名，sc是扣减值
        for pat, action, target_feature, delta, tip in downgrade_compiled:
            if action != "offset":
                continue
            if pat.search(raw_full_text):
                logger.info(f"[mold_weight][offset_rule] 命中通用抵消规则：{tip}")
                # 查找目标特征并扣减分数
                for f in hit_features:
                    if f["name"] == target_feature:
                        old_w = f["weight"]
                        f["weight"] += delta
                        logger.info(f"[mold_weight][offset_rule] 特征 {target_feature} 原值 {old_w} → {f['weight']}")
                        if f["weight"] <= 0:
                            hit_features.remove(f)
                            logger.info(f"[mold_weight][offset_rule] {target_feature} 分值归零，移除")
                        break
        # ========== === 修改新增：通用消歧义分支 end ==========

    return hit_features

# ============================================================
# 三、加权计算（纯函数，输入确定 → 输出确定）
# ============================================================

def _humidity_contribution(humidity: float, humidity_rules: List) -> Tuple[int, str]:
    """湿度加分，返回(分, 建议)"""
    for threshold, score, suggest_template in humidity_rules:
        if humidity >= threshold:
            return score, suggest_template.format(rh=humidity)
    return 0, ""

def _temperature_contribution(temperature: float, temp_config: List) -> Tuple[int, str]:
    """温度加分：落在霉菌适宜区间才加"""
    low, high = (temp_config["low"], temp_config["high"])
    if low <= temperature <= high:
        return temp_config["score"], temp_config["template"].format(t=temperature)
    return 0, ""

def _decide_level(total_score: int, level_rules: List) -> Tuple[str, str]:
    """根据总分定级，返回(riskLevel中文, riskClass)"""
    for threshold, level, cls in level_rules:
        if total_score >= threshold:
            return level, cls
    return "低风险", "risk-low"

#弱因子封顶分数接口
def calc_inducer_cap_score(hit_features: List[dict], lesion_keywords: List) -> tuple[int, int, int]:
    """
    区分病灶 / 诱因 / 有利减分，实现【无病灶时诱因封顶20】规则
    :param hit_features: 经过互斥去重后的命中特征列表
    :return: (lesion_score, inducer_score, benefit_score)
    """
    MAX_PURE_INDUCER = 20

    lesion_score = 0
    inducer_raw = 0
    benefit_score = 0

    for f in hit_features:
        kw = f["matched_keyword"]
        w = f["weight"]
        if kw in lesion_keywords:
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
    rule_text: str = ""
) -> dict:
    """
    输入：
      img_struct   : LLaVA 视觉输出的结构化 dict（必须是 dict）
      temperature  : 实时温度 ℃，可空
      humidity     : 实时相对湿度 %，可空
    输出：
      {riskLevel, riskClass, desc, suggest, extraNote}
    """

    FEATURE_GROUPS = []
    MUTEX_GROUPS = []
    NEGATION_WORDS  = []
    HUMIDITY_RULES = []
    LEVEL_RULES = []
    SOFT_DOWNGRADE_RAW = []
    SOFT_APPEND_RAW = []
    LESION_KEYWORDS = []

    if rule_text.strip():
        logger.info("命中features知识库策略")
        FEATURE_GROUPS, MUTEX_GROUPS, NEGATION_WORDS, HUMIDITY_RULES, TEMP_CONFIG, LEVEL_RULES, SOFT_DOWNGRADE_RAW, SOFT_APPEND_RAW, LESION_KEYWORDS = parse_feature_groups(rule_text)
    else:
        logger.info("未命中features知识库策略")

    logger.info(f"img_struct: {img_struct}" )

    # 忽略场景
    ignore_scene_pat = re.compile(r"this image is not a wall/ceiling/floor scene.", re.IGNORECASE)
    raw_text = img_struct["__raw_text__"]
    logger.info(f"raw_text: {raw_text}")
    if ignore_scene_pat.search(raw_text):
        # 直接返回：无效场景，不跑特征匹配、不打分
        return {
            "riskLevel": "invalid",
            "riskClass": "invalid",
            "desc": "图片非墙面/顶面/地面场景，不做霉菌评估",
            "suggest": "",
            "extraNote": "请重新拍照，上传正确的场景图片"
        }

    # 1. 图像特征命中
    features = extract_features(img_struct, FEATURE_GROUPS, NEGATION_WORDS, SOFT_DOWNGRADE_RAW, SOFT_APPEND_RAW)
    # 互斥组去重
    features = resolve_mutex_features(features, MUTEX_GROUPS)

    # 调用抽出来的分数计算
    lesion_score, inducer_score, benefit_score = calc_inducer_cap_score(features, LESION_KEYWORDS)

    img_total = lesion_score + inducer_score + benefit_score
    img_total = max(0, img_total)

    total_score = img_total
    suggestions = [{"weight": f["weight"], "text": f["suggest"]} for f in features]

    # 2. 湿度贡献（有值才算）
    if humidity is not None:
        logger.info("湿度贡献命中") # type: ignore
        h_score, h_suggest = _humidity_contribution(humidity, HUMIDITY_RULES)
        total_score += h_score
        if h_score:
            suggestions.append({"weight": h_score, "text": h_suggest})

    # 3. 温度贡献（有值才算）
    logger.info("温度: " + str(temperature))
    if temperature is not None:
        logger.info("温度贡献命中")
        t_score, t_suggest = _temperature_contribution(temperature, TEMP_CONFIG)
        total_score += t_score
        if t_score:
            suggestions.append({"weight": t_score, "text": t_suggest})

    # 4. 定级&score上线100
    level, cls = _decide_level(total_score, LEVEL_RULES)
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
