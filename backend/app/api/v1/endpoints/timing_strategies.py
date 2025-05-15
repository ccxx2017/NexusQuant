# --- START OF FILE backend/app/api/v1/endpoints/timing_strategies.py ---
from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Any
from app.models.timing import TimingStrategyConfig, TimingSignalRequest, TimingSignalResponse # 从新模型导入
# 假设我们也会创建一个 TimingService
from app.services.timing_service import TimingService 
from datetime import datetime
from app.models.strategy import StrategyParam

router = APIRouter()
timing_service = TimingService() # 实例化服务

# 预设的择时策略
PRESET_TIMING_STRATEGIES = [
    TimingStrategyConfig(
        id="rsi_oversold_rebound",
        name="RSI超卖反弹",
        description="当相对强弱指数(RSI)进入超卖区后出现反弹迹象时产生信号。",
        params=[
            StrategyParam(name="rsi_period", label="RSI周期", value=14, type="number", min_value=5, max_value=30, step=1, unit="周期", description="RSI计算周期"),
            StrategyParam(name="rsi_oversold_threshold", label="RSI超卖阈值", value=30, type="number", min_value=10, max_value=50, step=1, unit="", description="RSI低于此值视为超卖"),
            # 之前的 rsi_rebound_confirmation_days 可以考虑后续再加入，或者简化逻辑
        ],
        tags=["技术指标", "反转", "RSI"]
    ),
    TimingStrategyConfig(
        id="ma_cross", # 之前可能是 ma_golden_cross，统一为 ma_cross，具体金叉死叉由信号类型区分
        name="均线交叉",
        description="当短期均线上穿或下穿长期均线时产生信号。",
        params=[
            StrategyParam(name="short_ma_period", label="短期均线周期", value=5, type="number", min_value=3, max_value=60, step=1, unit="日", description="短期移动平均线计算周期"),
            StrategyParam(name="long_ma_period", label="长期均线周期", value=20, type="number", min_value=10, max_value=200, step=1, unit="日", description="长期移动平均线计算周期"),
            StrategyParam(name="enable_volume_filter", label="启用成交量确认", value=False, type="boolean", description="是否要求信号日成交量放大"),
            StrategyParam(name="volume_avg_days", label="成交量平均N日", value=10, type="number", min_value=3, max_value=30, step=1, unit="日", description="计算N日平均成交量"),
            StrategyParam(name="volume_multiple", label="成交量放大倍数", value=1.5, type="number", min_value=1.0, max_value=5.0, step=0.1, unit="倍", description="当日成交量需大于N日均量的此倍数"),
        ],
        tags=["技术指标", "趋势", "均线"]
    ),
]

@router.get("/strategies", response_model=List[TimingStrategyConfig])
async def get_timing_strategies_endpoint():
    """获取所有预设的择时策略配置"""
    return PRESET_TIMING_STRATEGIES

@router.post("/generate_signals", response_model=TimingSignalResponse)
async def generate_timing_signals_endpoint(request: TimingSignalRequest = Body(...)):
    """根据选择的策略和标的列表，生成择时信号"""
    try:
        current_time = datetime.now()
        signal_items, data_last_date = await timing_service.generate_signals_for_targets(
            target_tickers=request.target_tickers,
            strategy_id=request.strategy_id,
            params=request.params
        )
        return TimingSignalResponse(
            signals=signal_items,
            strategy_used=request.strategy_id,
            params_used=request.params,
            request_timestamp=current_time.isoformat(),
            data_timestamp=data_last_date
        )
    except ValueError as e:
        # 例如策略ID不存在
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        import traceback
        print(f"Error in generate_timing_signals_endpoint: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating timing signals: {str(e)}")

# --- END OF FILE backend/app/api/v1/endpoints/timing_strategies.py ---