from services.dao.env_dao import insert_env_record, query_env_history
from typing import List, Dict
from pydantic import BaseModel

class EnvService:
    async def save_env_data(self, temp: float, hum: float, remark: str = ""):
        await insert_env_record(temp, hum, remark)

    async def get_env_history(self, start_time: str | None = None, end_time: str | None = None, limit: int = 100):
        return await query_env_history(start_time, end_time, limit)

    # ========== 新增滑动窗口预警算法 ==========
    async def get_env_risk_analysis(self, start_time=None, end_time=None, limit=100):
        data_list = await self.get_env_history(start_time, end_time, limit)
        risk_result = {
            "has_risk": False,
            "risk_periods": [],
            "raw_data": data_list
        }
        window = []  # 滑动窗口，最多保存最近3条记录

        for item in data_list:
            hum = item["hum"]
            window.append(item)
            # 窗口保持最大长度=3
            if len(window) > 3:
                window.pop(0)

            # 判断窗口内全部3条湿度 >=65
            if len(window) == 3:
                all_high_hum = all(rec["hum"] >= 65 for rec in window)
                if all_high_hum:
                    risk_result["has_risk"] = True
                    start_risk = window[0]["time"]
                    end_risk = window[2]["time"]
                    risk_result["risk_periods"].append({
                        "start": start_risk,
                        "end": end_risk,
                        "msg": "连续3次采集湿度超标，存在霉菌滋生风险"
                    })
        return risk_result

env_service = EnvService()