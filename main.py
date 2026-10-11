from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from routers import health, env, video
import os
from routers import llama

app = FastAPI(title="${PROJECT_NAME} API")

# 挂载静态页面目录
app.mount("/static", StaticFiles(directory="html_basic"), name="static")

# 注册路由
app.include_router(health.router)
app.include_router(env.router)
app.include_router(video.router)
app.include_router(llama.router)

app.mount("/html_basic", StaticFiles(directory="html_basic"), name="static")

@app.get("/")
async def root():
    return {"msg":"Project scaffold ready", "project":"${PROJECT_NAME}", "static_page": "/html_basic/index.html"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)