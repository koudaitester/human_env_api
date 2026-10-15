from services.dao.env_dao import insert_env_record, query_env_history

class EnvService:
    async def save_env_data(self, temp: float, hum: float, remark: str = ""):
        await insert_env_record(temp, hum, remark)

    async def get_env_history(self, start_time: str | None = None, end_time: str | None = None, limit: int = 100):
        return await query_env_history(start_time, end_time, limit)

env_service = EnvService()