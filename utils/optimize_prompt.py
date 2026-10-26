import json
from typing import List, Dict

# ===================== 配置区，直接改这里 =====================
MODEL_ENDPOINT = "http://127.0.0.1:8000/v1/chat/completions"  # MoonDream / LLaVA 本地接口
TARGET_ACC = 0.98        # 目标JSON合规+定级吻合率
MAX_ITER = 15            # 最大迭代轮次，防止死循环
TEST_CASES: List[Dict] = [
    # 测试样本：image_path + 人工标准输出（golden）
    {
        "image": "./test_img/mold1.jpg",
        "golden": {
            "riskLevel": "medium",
            "riskClass": "霉菌中度风险",
            "desc": "墙面局部发现霉斑，湿度偏高",
            "suggest": "加强排风，使用次氯酸擦拭",
            "extraNote": "后续持续监测湿度"
        }
    },
    {
        "image": "./test_img/mold2.jpg",
        "golden": {
            "riskLevel": "low",
            "riskClass": "低风险",
            "desc": "无明显霉斑，环境湿度正常",
            "suggest": "常规通风，定期监测温湿度",
            "extraNote": ""
        }
    }
]
INIT_SYSTEM_PROMPT = """
你是人居环境评估器，分析图片霉菌情况，严格输出JSON。
字段：riskLevel, riskClass, desc, suggest, extraNote
禁止额外文字、禁止markdown。
"""
# =============================================================

import requests

def call_vision(prompt: str, img_path: str) -> dict:
    """调用视觉模型，返回原始json对象"""
    # 这里简化，你替换成你项目里真实的LLaVA/MoonDream调用逻辑
    payload = {
        "system": prompt,
        "image": img_path
    }
    resp = requests.post(MODEL_ENDPOINT, json=payload, timeout=30)
    raw = resp.json()["content"]
    try:
        return json.loads(raw)
    except Exception:
        return {"__invalid": True}

def score_one(pred: dict, golden: dict) -> float:
    """打分函数：吻合度， 0~1"""
    if pred.get("__invalid"):
        return 0.0
    hit = 0
    total = len(golden.keys())
    for k, v in golden.items():
        if pred.get(k) == v:
            hit += 1
    return hit / total

def evaluate(prompt: str) -> float:
    """跑全部测试集，返回平均吻合率"""
    scores = []
    for case in TEST_CASES:
        pred = call_vision(prompt, case["image"])
        s = score_one(pred, case["golden"])
        scores.append(s)
    return sum(scores) / len(scores)

def optimize_prompt():
    best_prompt = INIT_SYSTEM_PROMPT
    best_score = evaluate(best_prompt)
    print(f"初始Prompt得分: {best_score:.3f}")

    current_prompt = best_prompt
    for it in range(1, MAX_ITER + 1):
        print(f"\n===== 迭代 {it}/{MAX_ITER} =====")
        # 让LLM生成新版prompt，这一步就是Agent的思考环节
        improve_req = f"""
当前system prompt：
{current_prompt}
当前吻合率 {best_score:.3f}，目标 {TARGET_ACC}。
任务：优化这个prompt，保证模型严格输出正确JSON，字段和格式不出错，霉菌定级准确。
只输出新版system prompt文本，不要别的解释。
"""
        llm_resp = requests.post(MODEL_ENDPOINT, json={"prompt": improve_req})
        new_prompt = llm_resp.json()["content"].strip()
        new_score = evaluate(new_prompt)
        print(f"新版本得分: {new_score:.3f}")

        if new_score > best_score:
            best_score = new_score
            best_prompt = new_prompt
            current_prompt = new_prompt
            print("✅ 更新最优Prompt")
            if best_score >= TARGET_ACC:
                print("🎯 达成目标！")
                break
        else:
            print("❌ 新版本效果变差，保留旧最优版本")

    print("\n==================== 最终最优Prompt ====================")
    print(f"得分：{best_score:.3f}")
    print(best_prompt)
    return best_prompt

if __name__ == "__main__":
    final_prompt = optimize_prompt()