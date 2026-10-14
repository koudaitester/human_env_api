import httpx
import json
from ollama import chat
from utils.rag_helper import get_rag_knowledge
from services.log_service import logger

# 霉菌知识库标识
MOLD_KNOWLEDGE_ID = "mold_rules.md"

class LlamaService:
    def __init__(self, model_name="llava"):
        self.model_name = model_name
        self.ollama_url = "http://127.0.0.1:11434/api/generate"

    async def call_llama(self, prompt: str, image_b64: str|None = None):
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "images": [image_b64] if image_b64 else [],
            "stream": False,
            "format": "json"
        }
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(self.ollama_url, json=payload)
                logger.info("ollama raw resp: " + resp.text)
                data = resp.json()
                if "response" not in data:
                    raise KeyError("missing response")
                return json.loads(data["response"])
        except Exception as e:
            logger.error("大模型调用异常：", e)
            # 降级mock
            return {
                "risk_level": "medium",
                "summary": "模型调用失败，使用兜底评估",
                "suggestions": ["检查ollama服务是否正常运行，模型是否拉取成功"]
            }

    # ========== 移入类内 ==========
    async def analyze_mold_visual(self, img_b64: str):
        # Service：只拉知识库 + 拼接prompt + 调用大模型
        rule_text = await get_rag_knowledge(MOLD_KNOWLEDGE_ID)
#         prompt = f"""
# 你是人居环境霉菌评估专家。
# 输入信息：
# 参考下面知识库规则：
# {rule_text}
# 分析图片，只输出纯JSON文本。
# 硬性规则：
# 1. 仅输出纯JSON字符串，绝对不能添加任何markdown标记，禁止```、禁止代码块
# 2. 禁止输出任何解释、前言、说明文字、注释，只返回JSON
# 3. 必须包含4个key：riskLevel、riskClass、desc、suggest
# 4. riskClass只能从下面4个里面选：risk-low / risk-warn / risk-mid / risk-high
# 输出示例（只参考结构，不要原样输出示例）：
# {"riskLevel":"低风险","riskClass":"risk-low","desc":"描述内容","suggest":"建议内容"}
# 你的输出必须可以直接用JSON.parse解析，不能包含任何额外字符。

# 约束：
# 1. 严格遵循知识库温湿度阈值；
# 2. 区分灰尘、污渍、霉斑，不夸大；
# 3. 缺少温湿度数据，明确说明：缺少温湿度，评估仅基于图像，存在局限性；
# 4. 结尾带上免责提示：本结果仅AI辅助筛查，不能替代专业环境检测。
# """
        prompt = """
    任务：人居环境霉菌图像评估。
硬性规则：
1. 仅输出纯JSON字符串，绝对不能添加任何markdown标记，禁止```、禁止代码块
2. 禁止输出任何解释、前言、说明文字、注释，只返回JSON
3. 全部内容**必须使用中文书写**，desc、suggest、riskLevel字段不允许出现英文
4. 必须包含4个key：riskLevel、riskClass、desc、suggest
5. riskClass只能从下面4个里面选：risk-low / risk-warn / risk-mid / risk-high

输出示例（只参考结构，不要原样输出示例）：
{"riskLevel":"低风险","riskClass":"risk-low","desc":"描述内容","suggest":"建议内容"}

你的输出必须可以直接用JSON.parse解析，不能包含任何额外字符。
    """
        logger.info("prompt: " + prompt)
        resp = chat(
            model="llava",
            messages=[{
                "role": "user",
                "content": prompt,
                "images": [img_b64]
            }]
        )
        logger.info("llava resp: " + str(resp))
        return {"code": 200, "data": resp["message"]["content"]}

    async def analyze_mold_full(self, img_b64: str, temp: float, humidity: float):
        # Service：接收b64、温湿度，拉规则，拼接prompt，调用模型
        rule_text = await get_rag_knowledge(MOLD_KNOWLEDGE_ID)
        prompt = f"""
任务：人居环境霉菌综合风险评估。
硬性规则：
1. 仅输出纯JSON字符串，绝对不能添加任何markdown标记，禁止```、禁止代码块
2. 禁止输出任何解释、前言、说明文字、注释，只返回JSON
3. 全部内容必须使用中文书写，desc、suggest、riskLevel字段不允许出现英文
4. 必须包含4个key：riskLevel、riskClass、desc、suggest
5. riskClass只能从下面4个里面选：risk-low / risk-warn / risk-mid / risk-high

评估依据：
【知识库规则】
{rule_text}
【环境参数】
温度：{temp} ℃
相对湿度：{humidity} %

输出示例（只参考结构，不要原样输出示例）：
{{"riskLevel":"低风险","riskClass":"risk-low","desc":"描述内容","suggest":"建议内容"}}

你的输出必须可以直接用JSON.parse解析，不能包含任何额外字符。
"""
        logger.info("prompt: " + prompt)
        resp = chat(
            model="llava",
            messages=[{
                "role": "user",
                "content": prompt,
                "images": [img_b64]
            }]
        )
        return {"code": 200, "data": resp["message"]["content"]}

llama_service = LlamaService()
