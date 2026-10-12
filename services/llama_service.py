import httpx
import json

class LlamaService:
    def __init__(self, model_name="llava"):
        self.model_name = model_name
        self.ollama_url = "http://127.0.0.1:11434/api/generate"

    async def call_llama(self, prompt: str, image_b64: str|None = None):
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "images": [image_b64],
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
