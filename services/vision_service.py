from .base_service import BaseService

class VisionService(BaseService):
    @staticmethod
    async def image_analyze(image_path: str, prompt: str):
        # Mock返回，演示截图用，后续替换成LLaVA真实调用
        mock_data = {
            "summary": "室内人居环境，墙面完好，窗户半开。",
            "risk": ["开窗会引入室外污染物，PM2.5存在升高风险"],
            "suggest": "污染天关闭窗户，开启空气净化设备。"
        }
        return BaseService.success(mock_data)

vision_service = VisionService()