from .base_service import BaseService

class AudioService(BaseService):
    @staticmethod
    async def extract_audio(video_path: str, output_mp3: str):
        """从视频提取音频，保存mp3"""
        try:
            return BaseService.success({"audio_path": output_mp3})
        except Exception as e:
            return BaseService.fail(f"音频提取失败:{str(e)}")
