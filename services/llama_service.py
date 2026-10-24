from asyncio import log
import datetime

import httpx
import json
from ollama import chat
from utils.rag_helper import get_rag_knowledge
from services.log_service import logger
import os
from services.dao.db_pool import get_conn, release_conn
import re
from services.prompt_service import get_prompt
from utils.tools import resize_image_for_llava

# 霉菌知识库标识
MOLD_KNOWLEDGE_ID = "mold_rules.md"

DISCLAIMER = """
【免责声明】本评估仅为AI参考判断，不能替代专业检测机构。
若怀疑存在严重霉菌污染，请联系专业机构上门检测。
"""

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
        # rule_text = await get_rag_knowledge(MOLD_KNOWLEDGE_ID)
        prompt = get_prompt("mold_vision_extract_llava")
        #压缩base64图片
        # img_b64 = resize_image_for_llava(img_b64, 1000)

        # logger.info("prompt: " + prompt)
        resp = chat(
            model="llava",
            messages=[{
                "role": "user",
                "content": prompt,
                "images": [img_b64]
            }],
            options={
            "temperature": 0.0,
            "top_p": 0.1,
            "seed": 42,
            "max_tokens": 384,
            "keepalive": "10m"
            }
        )
        logger.info("llava resp: " + str(resp))
        return {"code": 200, "data": resp["message"]["content"]}

    async def analyze_mold_full(self, img_b64: str, temperature: float|None = None, humidity: float|None = None):
        # Service：接收b64、温湿度，拉规则，拼接prompt，调用模型
        # rule_text = await get_rag_knowledge(MOLD_KNOWLEDGE_ID)
        # if temperature is None or humidity is None:
        #     raise ValueError("温湿度参数不能为空")

        prompt = get_prompt("mold_vision_extract_llava")
        logger.info("prompt: " + prompt)

        resp = chat(
            model="llava",
            messages=[{
                "role": "user",
                "content": prompt,
                "images": [img_b64]
            }],
            options={
            "temperature": 0.1,
            "top_p": 0.1,
            "seed": 42,
            "max_tokens": 512,
            "keepalive": "10m",
            }
        )
        return {"code": 200, "data": resp["message"]["content"]}

    async def analyze_mold_group(self, image_b64_list: list[str], filenames: list[str], temperature: float|None, humidity: float|None):
        rule_text = get_rag_knowledge("mold_rules.md")
        prompt = f"""
    {rule_text}
    本次巡检一共 {len(image_b64_list)} 张照片，文件名列表：{filenames}
    全部照片属于**同一个人居房间/空间**。
    环境参数：温度 {temperature}℃，相对湿度 {humidity}%。

    任务：综合全部照片画面，对这整个空间做霉菌风险综合评估。
    禁止对每张图片单独输出评估，只输出一份整体评估JSON。
    JSON字段要求：
    1. group_risk_level：整体风险等级（低风险 / 中风险 / 高风险）
    2. risk_summary：综合描述，描述在哪些照片观察到可疑痕迹
    3. suspect_positions：可疑位置清单
    4. suggestion：针对这个房间的整套处置建议
    """
        logger.info("prompt: " + prompt)
        resp = chat(
            model="llava",
            messages=[{
                "role": "user",
                "content": prompt,
                "images": image_b64_list
            }]
        )
        
        logger.info("llava group resp: " + str(resp))
        raw = resp["message"]["content"]

        # 匹配 ```json ... ```
        pattern = r"```(?:json)?\n?(.*?)\n?```"
        match = re.search(pattern, raw, re.DOTALL)
        if match:
            raw = match.group(1).strip()
        
        logger.info("llava group raw: " + raw)

        # 2. 移除json里的控制字符（\x00-\x1f 除了 \n \r \t）
        raw = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', raw)

        if isinstance(raw, dict):
            data = raw
        else:
            data = json.loads(raw)

        data["disclaimer"] = DISCLAIMER
        data["file_list"] = filenames
        data["temperature"] = temperature
        data["humidity"] = humidity
        return data

    async def save_group_json(self, result_list: list[dict]):
        report = result_list[0]
        filenames = report.get("file_list", [])
        temperature = report.get("temperature")
        humidity = report.get("humidity")

        conn = get_conn()
        try:
            cur = conn.cursor()
            insert_sql = """
            INSERT INTO mold_group_record (
                file_names, temperature, humidity, group_risk_level,
                risk_summary, suspect_positions, suggestion, disclaimer, full_result_json
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id;
            """
            cur.execute(insert_sql, (
                ",".join(filenames),
                temperature,
                humidity,
                report.get("group_risk_level"),
                report.get("risk_summary"),
                report.get("suspect_positions"),
                report.get("suggestion"),
                report.get("disclaimer"),
                json.dumps(report, ensure_ascii=False)
            ))
            row = cur.fetchone()
            record_id = row[0]
            conn.commit()
            return f"record_id:{record_id}"
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            release_conn(conn)

llama_service = LlamaService()