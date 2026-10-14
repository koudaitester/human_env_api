from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routers import api_router
from fastapi.responses import RedirectResponse
import os
from services.log_service import logger

os.makedirs("./tmp", exist_ok=True)

app = FastAPI(title="Human In API", version="0.1.0")
app.mount("/html_basic/static", StaticFiles(directory="html_basic/static"), name="static")
app.include_router(api_router, prefix="/api/v1")

@app.get("/", tags=["演示面板"])
async def root():
    logger.info("访问根路径")
    # return {"msg": "Human In API service running，访问 /static/index.html 打开演示面板"}
    return RedirectResponse(url="/html_basic/static/mold_analyze.html")

if __name__ == "__main__":
    import uvicorn
    logger.info("启动服务")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)