from .base_service import BaseService
from config.llama_config import LLAMA_MODEL_NAME, OLLAMA_HOST
import ollama

class LlmService(BaseService):
    @staticmethod
    async def chat_completion(prompt: str, system_prompt: str = None):
        """大模型对话生成"""
        try:
            resp = ollama.chat(
                model=LLAMA_MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt or ""},
                    {"role": "user", "content": prompt}
                ]
            )
            return BaseService.success(resp["message"]["content"])
        except Exception as e:
            return BaseService.fail(f"LLM调用失败:{str(e)}")
