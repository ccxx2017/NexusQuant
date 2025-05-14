# backend/app/api/v1/endpoints/selection_strategies.py
from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Any
from app.models.strategy import StrategyConfig, SelectionPoolRequest, SelectionPoolResponse # 从models导入
from app.services.strategy_service import StrategyService
from datetime import datetime

router = APIRouter()
strategy_service = StrategyService()

PRESET_SELECTION_STRATEGIES = [
    StrategyConfig(
        id="value_momentum",
        name="动量质量双引擎",
        description="结合价值与动量因子，筛选具备增长潜力的标的。",
        params=[
            {"name": "momentum_window_months", "value": 6, "min_value": 3, "max_value": 24, "step": 1, "unit": "个月", "description": "动量回溯窗口"},
            {"name": "roe_threshold_percent", "value": 15, "min_value": 5, "max_value": 30, "step": 1, "unit": "%", "description": "ROE阈值"},
            {"name": "pb_discount_percent", "value": 20, "min_value": 0, "max_value": 50, "step": 5, "unit": "%", "description": "PB相对行业折价率"}
        ],
        tags=["价值", "动量", "质量"],
        historical_performance_summary={"annual_return": "18%", "max_drawdown": "-15%"}
    ),
]

@router.get("/strategies", response_model=List[StrategyConfig]) # <--- 修改这里
async def get_selection_strategies_endpoint(): # 函数名可以更具体一点避免冲突
    return PRESET_SELECTION_STRATEGIES

@router.post("/generate_pool", response_model=SelectionPoolResponse)
async def generate_selection_pool_endpoint(request: SelectionPoolRequest = Body(...)): # 函数名可以更具体
    try:
        pool_items_data = await strategy_service.generate_pool_for_selection(
            strategy_id=request.strategy_id,
            params=request.params
        )
        return SelectionPoolResponse(
            items=pool_items_data,
            strategy_used=request.strategy_id,
            params_used=request.params,
            timestamp=datetime.now().isoformat()
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating selection pool: {str(e)}")