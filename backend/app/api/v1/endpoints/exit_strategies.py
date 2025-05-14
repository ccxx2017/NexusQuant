# backend/app/api/v1/endpoints/exit_strategies.py
from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.models.strategy import StrategyConfig # 假设 StrategyConfig 在 strategy.py
from datetime import datetime
import asyncio
import random

# 临时定义模型，后续应移到 app/models/ 中
class HoldingItem(BaseModel):
    ts_code: str
    name: Optional[str] = None
    cost_price: float
    quantity: int
    current_price: float # 当前价格，用于计算信号

class ExitSignalRequest(BaseModel):
    exit_strategy_id: str
    exit_params: Dict[str, Any]
    holdings: List[HoldingItem] # 用户当前的持仓列表

class ExitSignalItem(BaseModel):
    ts_code: str
    name: Optional[str] = None
    signal: Optional[str] = None # 例如 "触发止盈", "达到止损", "ATR追踪卖点"
    details: Optional[Dict[str, Any]] = None # 更详细的信号信息

class ExitSignalResponse(BaseModel):
    signals: List[ExitSignalItem]
    strategy_used: str
    params_used: Dict[str, Any]
    timestamp: str


router = APIRouter()

# 预设的退出策略配置 (实际应从DB或配置文件/服务层加载)
PRESET_EXIT_STRATEGIES = [
    StrategyConfig(
        id="dynamic_sl_tp", # dynamic_stop_profit_loss
        name="动态止盈止损",
        description="设置固定的止盈和止损百分比。",
        params=[
            {"name": "take_profit_percent", "value": 20, "min_value":5, "max_value":100, "unit":'%', "description": "止盈百分比"},
            {"name": "stop_loss_percent", "value": 10, "min_value":1, "max_value":50, "unit":'%', "description": "止损百分比"}
        ],
        tags=["固定比例"],
        # historical_performance_summary 可以不填，因为它通常作用于已有持仓
    ),
    StrategyConfig(
        id="atr_trailing_stop",
        name="ATR追踪止损",
        description="使用ATR指标动态调整止损位。",
        params=[
            {"name": "atr_period", "value": 14, "min_value":5, "max_value":30, "unit":'周期', "description": "ATR计算周期"},
            {"name": "atr_multiplier", "value": 3, "min_value":1, "max_value":5, "unit":'倍数', "description": "ATR倍数"}
        ],
        tags=["动态追踪", "波动率"],
    ),
]

@router.get("/exit/strategies", response_model=List[StrategyConfig])
async def get_exit_strategies():
    """
    获取预设的退出策略列表。
    """
    return PRESET_EXIT_STRATEGIES

@router.post("/exit/check_signals", response_model=ExitSignalResponse)
async def check_exit_signals_for_holdings(request: ExitSignalRequest = Body(...)):
    """
    根据选定的退出策略、参数和用户持仓，检查是否有退出信号。
    核心业务逻辑应在服务层实现。
    """
    # print(f"Received exit signal check request: {request.dict()}")
    # 模拟调用服务层
    # signals_data = await strategy_service.check_exit_signals(
    #     strategy_id=request.exit_strategy_id,
    #     params=request.exit_params,
    #     holdings=request.holdings
    # )

    # --- START: 模拟返回数据 (请替换为真实逻辑) ---
    await asyncio.sleep(0.1) # 模拟IO
    mock_signals_result = []
    for holding in request.holdings:
        signal_text = None
        profit_loss_percent = ((holding.current_price - holding.cost_price) / holding.cost_price) * 100

        if request.exit_strategy_id == "dynamic_sl_tp":
            take_profit = request.exit_params.get("take_profit_percent", 20)
            stop_loss = request.exit_params.get("stop_loss_percent", 10)
            if profit_loss_percent >= take_profit:
                signal_text = f"达到止盈({take_profit}%)"
            elif profit_loss_percent <= -stop_loss:
                signal_text = f"触发止损({stop_loss}%)"
        elif request.exit_strategy_id == "atr_trailing_stop":
            # 模拟ATR逻辑，实际需要历史数据计算ATR
            if profit_loss_percent < -random.uniform(5,15): # 模拟ATR追踪
                 signal_text = "ATR追踪卖点"

        mock_signals_result.append(
            ExitSignalItem(
                ts_code=holding.ts_code,
                name=holding.name or f"股票{holding.ts_code.split('.')[0]}",
                signal=signal_text,
                details={"current_pnl_percent": round(profit_loss_percent,2)} if signal_text else None
            )
        )
    # --- END: 模拟返回数据 ---

    return ExitSignalResponse(
        signals=mock_signals_result,
        strategy_used=request.exit_strategy_id,
        params_used=request.exit_params,
        timestamp=datetime.now().isoformat()
    )