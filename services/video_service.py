import time
import uuid

# 内存任务存储，重启丢失
task_store = {}

class VideoService:
    @staticmethod
    def create_task(prompt: str):
        task_id = str(uuid.uuid4())
        task_store[task_id] = {
            "status": "running",
            "prompt": prompt,
            "video_path": None
        }
        # mock 3秒后完成
        time.sleep(3)
        task_store[task_id]["status"] = "done"
        task_store[task_id]["video_path"] = "/tmp/sample.mp4"
        return task_id

    @staticmethod
    def get_task(task_id: str):
        return task_store.get(task_id, None)

video_service = VideoService()