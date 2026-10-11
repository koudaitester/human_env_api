from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routers import health, env, video
import os

app = FastAPI(title="${PROJECT_NAME} API")

# 挂载静态页面目录
app.mount("/static", StaticFiles(directory="html_basic"), name="static")

# 注册路由
app.include_router(health.router)
app.include_router(env.router)
app.include_router(video.router)

@app.get("/")
async def root():
    return {"msg":"Project scaffold ready", "project":"${PROJECT_NAME}", "static_page": "/static/index.html"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)