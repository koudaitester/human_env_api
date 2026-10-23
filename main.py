from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routers import api_router
from fastapi.responses import RedirectResponse
import os
from services.log_service import logger
from services.dao.db_pool import init_pool, close_all_pool
import atexit
from routers.user_router import router as user_router

os.makedirs("./tmp", exist_ok=True)

app = FastAPI(title="Human In API", version="0.1.0")
app.mount("/html_basic/static", StaticFiles(directory="html_basic/static"), name="static")
app.include_router(api_router, prefix="/api/v1")

# 应用启动初始化连接池
init_pool()
# 退出时释放
atexit.register(close_all_pool)

app.include_router(user_router, prefix="/user")

@app.get("/", tags=["演示面板"])
async def root():
    logger.info("访问根路径")
    # return {"msg": "Human In API service running，访问 /static/index.html 打开演示面板"}
    return RedirectResponse(url="/html_basic/static/login.html")

if __name__ == "__main__":
    import uvicorn
    logger.info("启动服务")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
