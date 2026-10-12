from .base_service import BaseService

class VisionService(BaseService):
    @staticmethod
    async def image_analyze(image_path: str, prompt: str):
        """图像/视频帧视觉分析，调用LLaVA"""
        try:
            # LLaVA图像推理预留
            return BaseService.success({"result": ""})
        except Exception as e:
            return BaseService.fail(f"视觉分析异常:{str(e)}")
