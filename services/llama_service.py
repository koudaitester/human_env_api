from ollama import Client
from config.llama_config import LLAMA_MODEL_NAME, OLLAMA_HOST, MAX_TOKENS, TEMPERATURE

class LlamaService:
    def __init__(self):
        self.client = Client(host=OLLAMA_HOST)

    async def chat(self, prompt: str):
        resp = self.client.chat(
            model=LLAMA_MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature": TEMPERATURE,
                "num_predict": MAX_TOKENS
            }
        )
        return resp["message"]["content"]

llama_service = LlamaService()
