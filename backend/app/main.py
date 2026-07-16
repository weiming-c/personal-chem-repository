import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db
from app.utils.response import error


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化数据库"""
    await init_db()
    # 确保上传目录存在
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS 跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件——上传的图片
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content=error(code=500, message=f"服务器内部错误: {str(exc)}"),
    )


@app.get("/api/health")
async def health_check():
    return {"code": 0, "message": "ok", "data": {"version": settings.APP_VERSION}}


# 注册路由
from app.routers.questions import router as question_router, router_ocr, router_upload
from app.routers.search import router as search_router
from app.routers.tags import router as tags_router
from app.routers.wrong_questions import router as wrong_questions_router

app.include_router(question_router)
app.include_router(router_ocr)
app.include_router(router_upload)
app.include_router(search_router)
app.include_router(tags_router)
app.include_router(wrong_questions_router)
# 后续步骤逐步添加:
# app.include_router(tags.router)
# app.include_router(search.router)
# app.include_router(wrong_questions.router)
# app.include_router(papers.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
