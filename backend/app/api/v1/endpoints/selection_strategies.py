# --- START OF FILE backend/app/api/v1/endpoints/selection_strategies.py ---
from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Any
from app.models.strategy import StrategyConfig, SelectionPoolRequest, SelectionPoolResponse
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
            {"name": "min_momentum_percent", "value": 5, "min_value": -50, "max_value": 100, "step": 1, "unit": "%", "description": "最小动量阈值(%)"}, # 新增参数
            {"name": "roe_threshold_percent", "value": 15, "min_value": 5, "max_value": 30, "step": 1, "unit": "%", "description": "ROE阈值"},
            {"name": "max_pb_value", "value": 2.5, "min_value": 0.1, "max_value": 5.0, "step": 0.1, "unit": "", "description": "最大市净率(PB)"}
        ],
        tags=["价值", "动量", "质量"],
        historical_performance_summary={"annual_return": "18%", "max_drawdown": "-15%"}
    ),
    StrategyConfig(
        id="simple_value_screen",
        name="简单价值筛选",
        description="根据市盈率、市净率和股息率进行基础价值筛选。",
        params=[
            {"name": "max_pe_ttm", "value": 30, "min_value": 1, "max_value": 100, "step": 1, "unit": "", "description": "最大市盈率(TTM)"},
            {"name": "max_pb", "value": 2.0, "min_value": 0.1, "max_value": 10.0, "step": 0.1, "unit": "", "description": "最大市净率"},
            {"name": "min_dividend_yield", "value": 2.0, "min_value": 0.0, "max_value": 10.0, "step": 0.1, "unit": "%", "description": "最小股息率(%)"},
            {"name": "min_total_mv_billions", "value": 50, "min_value": 0, "max_value": 1000, "step": 10, "unit": "亿", "description": "最小总市值(亿元)"}
        ],
        tags=["价值", "基本面"],
        historical_performance_summary={"annual_return": "N/A", "max_drawdown": "N/A"}
    ),
]

@router.get("/strategies", response_model=List[StrategyConfig])
async def get_selection_strategies_endpoint():
    return PRESET_SELECTION_STRATEGIES

@router.post("/generate_pool", response_model=SelectionPoolResponse)
async def generate_selection_pool_endpoint(request: SelectionPoolRequest = Body(...)):
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
        import traceback
        print(f"Error in generate_selection_pool_endpoint: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating selection pool: {str(e)}")
# --- END OF FILE backend/app/api/v1/endpoints/selection_strategies.py ---