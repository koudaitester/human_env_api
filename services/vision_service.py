from .base_service import BaseService
from services.llama_service import LlamaService

class VisionService(BaseService):
    def __init__(self):
        self.llama = LlamaService()

    # 只保留 image_base64 一个入参，prompt写在内部
    async def image_analyze(self, image_base64: str):
#         prompt = """
# 你是人居微环境检测专家。分析图片，输出JSON，只返回JSON，不要多余文字。
# 字段：risk_level(high/medium/low), summary, suggestions(数组)
# 知识库规则：
# 1. PM2.5>20 呼吸道敏感人群会感到不适；
# 2. 能见度差代表空气污染；
# 3. 识别积水、霉菌、杂物堆积等室内隐患。
# """
        prompt = """
你是人居环境霉菌检测专家。
任务：分析这张室内环境图片，识别是否存在霉菌。
要求：
1. 先判断：图片内**是否可见霉菌**。
2. 定位：标记可疑区域（墙面/墙角/吊顶/窗框/浴室缝隙/家具背面/地板接缝）。
3. 描述特征：颜色（黑、绿、白、灰斑）、斑点形态、潮湿痕迹、水渍、起皮、返潮。
4. 风险分级：低风险 / 中风险 / 高风险。
5. 给出简短原因和对应的简易处置建议。

限制：
- 只基于图片可见内容判断，不要过度脑补。
- 区分：灰尘、污渍、霉斑三者，不要把灰尘误判成霉菌。
- 输出结构固定：
【霉菌判定】
【可疑位置】
【视觉特征】
【风险等级】
【建议】
"""
        llm_result = await self.llama.call_llama(prompt, image_base64)
        return llm_result