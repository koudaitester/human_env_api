from fastapi import FastAPI
from routers import api_router

app = FastAPI(title="Human In API", version="0.1.0")
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"msg": "Human In API service running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
