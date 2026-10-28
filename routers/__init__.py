from fastapi import APIRouter
from .llm_router import router as llm_router
from .rag_router import router as rag_router
from .vision_router import router as vision_router
from .audio_router import router as audio_router
from .env_router import router as env_router
from .mold_router import router as mold_router
from .report_router import router as report_router
from .business_router import router as business_router
from .mold_stream_router import router as mold_stream_router
from .logview_router import router as logview_router

api_router = APIRouter()

api_router.include_router(llm_router, prefix="/llm", tags=["LLM对话"])
api_router.include_router(rag_router, prefix="/rag", tags=["RAG知识库"])
api_router.include_router(vision_router, prefix="/vision", tags=["视觉检测"])
api_router.include_router(audio_router, prefix="/audio", tags=["音频处理"])
api_router.include_router(env_router, prefix="/env", tags=["人居环境评估"])
api_router.include_router(mold_router, prefix="/mold", tags=["霉菌检测"]    )
api_router.include_router(report_router, prefix="/report", tags=["评估报告"])
api_router.include_router(business_router, prefix="/business", tags=["业务接口"])
api_router.include_router(mold_stream_router, prefix="/mold/stream", tags=["滑动窗口"])
api_router.include_router(logview_router, prefix="/logview", tags=["日志查看"])