from .base_service import BaseService

class EnvService(BaseService):
    @staticmethod
    async def evaluate_env(params: dict, knowledge_list: list):
        pm25 = params["pm25"]
        if pm25 <= 20:
            risk_level = "低风险"
            tip = "空气质量良好，维持当前环境参数即可。"
        elif pm25 <= 35:
            risk_level = "轻度风险"
            tip = "PM2.5略高，建议保持净化器低速运行。"
        else:
            risk_level = "较高风险"
            tip = "污染物偏高，减少开窗，加大净化器风量。"
        return BaseService.success({
            "params": params,
            "risk_level": risk_level,
            "suggestion": tip
        })