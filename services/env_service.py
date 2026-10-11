class EnvService:
    @staticmethod
    def check_air_purifier_rule(angle: int, is_sleep: bool):
        """
        净化器朝向校验
        is_sleep=True睡眠模式：禁止直吹床位
        angle: 出风口朝向角度
        """
        if is_sleep and 45 <= angle <= 135:
            return {"ok": False, "reason": "睡眠状态禁止直吹床位，会扰动墙面灰尘"}
        return {"ok": True, "reason": "朝向符合规则"}

env_service = EnvService()