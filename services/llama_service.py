import httpx
import json
from ollama import chat
from utils.rag_helper import get_rag_knowledge

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
                print("ollama raw resp:", resp.text)
                data = resp.json()
                if "response" not in data:
                    raise KeyError("missing response")
                return json.loads(data["response"])
        except Exception as e:
            print("大模型调用异常：", e)
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
        prompt = f"""
你是人居环境霉菌评估专家。
参考下面知识库规则：
{rule_text}
输入信息：
图像观察结果：根据图片内容识别
任务：综合上面全部信息，评估霉菌风险。
输出固定结构：
【霉菌视觉判定】
【环境参数评估】
【综合风险等级】
【风险说明】
【处置建议】
约束：
1. 严格遵循知识库温湿度阈值；
2. 区分灰尘、污渍、霉斑，不夸大；
3. 缺少温湿度数据，明确说明：缺少温湿度，评估仅基于图像，存在局限性；
4. 结尾带上免责提示：本结果仅AI辅助筛查，不能替代专业环境检测。
"""
        resp = chat(
            model="llava",
            messages=[{
                "role": "user",
                "content": prompt,
                "images": [img_b64]
            }]
        )
        return {"code": 200, "data": resp["message"]["content"]}

    async def analyze_mold_full(self, img_b64: str, temp: float, humidity: float):
        # Service：接收b64、温湿度，拉规则，拼接prompt，调用模型
        rule_text = await get_rag_knowledge(MOLD_KNOWLEDGE_ID)
        prompt = f"""
你是人居环境霉菌评估专家。
参考下面知识库规则：
{rule_text}
输入信息：
图像观察结果：根据图片内容识别
环境温度：{temp} ℃
相对湿度：{humidity} %
任务：综合上面全部信息，评估霉菌风险。
输出固定结构：
【霉菌视觉判定】
【环境参数评估】
【综合风险等级】
【风险说明】
【处置建议】
约束：
1. 严格遵循知识库温湿度阈值；
2. 区分灰尘、污渍、霉斑，不夸大；
3. 结尾带上免责提示：本结果仅AI辅助筛查，不能替代专业环境检测。
"""
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
