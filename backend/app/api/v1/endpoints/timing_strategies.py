# backend/app/api/v1/endpoints/timing_strategies.py
from fastapi import APIRouter, HTTPException, Body
from typing import List, Dict, Any, Optional
from pydantic import BaseModel # <--- 移到这里
from app.models.strategy import StrategyConfig
from datetime import datetime
import asyncio
import random

# 临时定义模型，后续应移到 app/models/ 中
class TimingSignalRequest(BaseModel):
    timing_strategy_id: str
    timing_params: Dict[str, Any]
    stock_codes: List[str]

class TimingSignalItem(BaseModel):
    ts_code: str
    name: Optional[str] = None
    current_price: Optional[float] = None
    signal_type: str
    signal_strength: Optional[float] = None
    trigger_time: str
    suggestion: str

class TimingSignalResponse(BaseModel):
    signals: List[TimingSignalItem]
    strategy_used: str
    params_used: Dict[str, Any]
    timestamp: str

router = APIRouter()

PRESET_TIMING_STRATEGIES = [
    StrategyConfig(
        id="rsi_crossover",
        name="RSI超卖反弹",
        # ... (params 和其他内容不变)
        params=[
            {"name": "rsi_period", "value": 14, "min_value":5, "max_value":30, "unit":'周期', "description": "RSI计算周期"},
            {"name": "rsi_buy_threshold", "value": 30, "min_value":10, "max_value":40, "description": "RSI买入阈值"}
        ],
        tags=["技术指标", "反转"],
        historical_performance_summary={"win_rate": "60%", "profit_loss_ratio": "1.8"}
    ),
    StrategyConfig(
        id="bb_breakout",
        name="波动率压缩突破",
        # ... (params 和其他内容不变)
        params=[
            {"name": "bb_period", "value": 20, "min_value":10, "max_value":60, "unit":'周期', "description": "布林带计算周期"},
            {"name": "bb_std_dev", "value": 2, "min_value":1, "max_value":3, "unit":'标准差倍数', "description": "布林带标准差倍数"}
        ],
        tags=["波动率", "突破"],
        historical_performance_summary={"win_rate": "55%", "profit_loss_ratio": "2.1"}
    ),
]

@router.get("/strategies", response_model=List[StrategyConfig]) # <--- 修改这里
async def get_timing_strategies_endpoint(): # 函数名可以更具体一点
    return PRESET_TIMING_STRATEGIES

@router.post("/generate_signals", response_model=TimingSignalResponse)
async def generate_timing_signals_endpoint(request: TimingSignalRequest = Body(...)): # 函数名可以更具体
    await asyncio.sleep(0.1)
    mock_signals = []
    for code in request.stock_codes[:2]:
        mock_signals.append(
            TimingSignalItem(
                ts_code=code,
                name=f"股票{code.split('.')[0]} (模拟)",
                current_price=round(random.uniform(10, 100), 2),
                signal_type="模拟择时信号",
                signal_strength=round(random.uniform(0.5, 0.9), 2),
                trigger_time=datetime.now().isoformat(),
                suggestion="观察" if random.random() > 0.5 else "买入"
            )
        )
    return TimingSignalResponse(
        signals=mock_signals,
        strategy_used=request.timing_strategy_id,
        params_used=request.timing_params,
        timestamp=datetime.now().isoformat()
    )