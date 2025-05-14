# backend/app/api/v1/api_v1.py
from fastapi import APIRouter
from app.api.v1.endpoints import selection_strategies, timing_strategies, exit_strategies, backtesting_lab, dashboard # 确保这些文件存在且有 router 对象

api_router = APIRouter()
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(selection_strategies.router, prefix="/selection", tags=["selection-strategies"])
api_router.include_router(timing_strategies.router, prefix="/timing", tags=["timing-strategies"])
api_router.include_router(exit_strategies.router, prefix="/exit", tags=["exit-strategies"])
api_router.include_router(backtesting_lab.router, prefix="/backtesting-lab", tags=["backtesting-lab"])

# 你也可以直接在这里定义一些简单的路由作为测试
@api_router.get("/test-v1")
async def test_v1_endpoint():
    return {"message": "API v1 is working!"}