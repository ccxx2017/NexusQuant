import os,sys
# 将项目根目录 (backend 目录) 添加到 Python 的模块搜索路径中
# 这样做可以确保 'app' 包能够被正确找到
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# PROJECT_ROOT 现在应该是 D:\AI-practicing\我的开发\创意方案\三位一体盈利增强矩阵02\backend
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 打印当前的 sys.path 以供调试 (正式发布时可以移除)
print("Current sys.path:", sys.path)
print("Attempting to import from app located at:", PROJECT_ROOT)


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api_v1 import api_router as api_v1_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS 中间件配置
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS, # <--- 使用 settings 中的列表
        allow_credentials=True, # 如果您以后需要发送凭证 (如 cookies, authorization headers)
        allow_methods=["*"],    # 允许所有标准的 HTTP 方法
        allow_headers=["*"],    # 允许所有类型的 HTTP 头部
    )

app.include_router(api_v1_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": "Welcome to the Quant Assistant API!"}

# (可选) 在应用启动时初始化Tushare客户端等
# @app.on_event("startup")
# async def startup_event():
#     from app.services.tushare_client import ts_client
#     # ts_client.initialize() or similar
#     pass