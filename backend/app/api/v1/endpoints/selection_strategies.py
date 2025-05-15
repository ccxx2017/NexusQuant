# --- START OF FILE backend/app/api/v1/endpoints/selection_strategies.py ---
from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Any
from app.models.strategy import StrategyConfig, SelectionPoolRequest, SelectionPoolResponse
from app.models.strategy import StrategyConfig, StrategyParam
from app.services.strategy_service import StrategyService
from datetime import datetime

router = APIRouter()
strategy_service = StrategyService()

PRESET_SELECTION_STRATEGIES = [
    StrategyConfig(
        id="simple_value",
        name="简单价值筛选",
        description="根据市盈率(PE-TTM)和市净率(PB)进行初步价值筛选。",
        params=[
            StrategyParam(name="max_pe_ttm", label="最大PE(TTM)", value=20, type="number", min_value=1, max_value=100, step=1, unit="倍"),
            StrategyParam(name="min_pb_value", label="最小PB", value=0.5, type="number", min_value=0.1, max_value=5, step=0.1, unit="倍"),
            StrategyParam(name="min_dividend_yield_ratio", label="最小股息率", value=2.0, type="number", min_value=0, max_value=15, step=0.1, unit="%"),
            StrategyParam(name="min_market_cap_billion", label="最小市值(亿元)", value=50, type="number", min_value=0, max_value=10000, step=10, unit="亿"),
            StrategyParam(name="exclude_st", label="排除ST股", value=True, type="boolean"),
        ],
        tags=["价值", "基本面", "PE", "PB"]
    ),
    StrategyConfig(
        id="value_momentum",
        name="动量质量双引擎",
        description="结合价值因子(PB)、质量因子(ROE)和动量因子进行综合筛选。",
        params=[
            StrategyParam(name="momentum_window_months", label="动量回溯窗口", value=6, type="number", min_value=1, max_value=24, step=1, unit="个月"),
            StrategyParam(name="min_momentum_percent", label="最小动量阈值", value=5.0, type="number", min_value=-50, max_value=200, step=1, unit="%"),
            StrategyParam(name="roe_threshold_percent", label="ROE阈值", value=10.0, type="number", min_value=0, max_value=50, step=1, unit="%"),
            StrategyParam(name="max_pb_value", label="最大PB", value=2.5, type="number", min_value=0.1, max_value=10, step=0.1, unit="倍"),
        ],
        tags=["价值", "动量", "质量", "ROE", "PB"]
    )
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