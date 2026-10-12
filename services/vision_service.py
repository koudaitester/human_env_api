from .base_service import BaseService
from services.llama_service import LlamaService

class VisionService(BaseService):
    def __init__(self):
        self.llama = LlamaService()

    # 只保留 image_base64 一个入参，prompt写在内部
    async def image_analyze(self, image_base64: str):
        prompt = """
你是人居微环境检测专家。分析图片，输出JSON，只返回JSON，不要多余文字。
字段：risk_level(high/medium/low), summary, suggestions(数组)
知识库规则：
1. PM2.5>20 呼吸道敏感人群会感到不适；
2. 能见度差代表空气污染；
3. 识别积水、霉菌、杂物堆积等室内隐患。
"""
        llm_result = await self.llama.call_llama(prompt, image_base64)
        return llm_result