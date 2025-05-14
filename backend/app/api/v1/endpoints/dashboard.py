# backend/app/api/v1/endpoints/dashboard.py
from fastapi import APIRouter
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime
import random

# --- Pydantic Models (理想情况下应在 app/models/dashboard.py 中定义) ---
class DashboardSummary(BaseModel):
    total_assets: float
    daily_pnl: float
    daily_pnl_percent: float
    holding_count: int
    market_risk: str # e.g., "低风险", "中等风险", "高风险"
    pending_signals: int

class CoreSignalCounts(BaseModel):
    buy_signals: int
    watch_signals: int
    sell_signals: int

class LatestOpportunityItem(BaseModel):
    type: str # "buy" or "watch"
    name: str
    ts_code: str
    reason: str
    price: float

class MarketTrendDataPoint(BaseModel):
    date: str # YYYY-MM-DD
    index_value: float
    vix_value: Optional[float] = None # VIX或其他情绪指标

class DashboardData(BaseModel):
    summary: DashboardSummary
    core_signals: CoreSignalCounts
    latest_opportunities: List[LatestOpportunityItem]
    market_trend: List[MarketTrendDataPoint]
    # holdings_performance: List[Any] # 也可以在这里返回简化的持仓表现


router = APIRouter()

@router.get("/dashboard/data", response_model=DashboardData)
async def get_dashboard_data():
    """
    获取主仪表盘所需的聚合数据。
    目前返回模拟数据。
    """
    # --- START: 模拟数据生成 ---
    summary = DashboardSummary(
        total_assets=round(random.uniform(100000, 500000), 2),
        daily_pnl=round(random.uniform(-5000, 5000), 2),
        daily_pnl_percent=round(random.uniform(-0.02, 0.02), 4), # 存储为小数，前端乘以100再显示百分比
        holding_count=random.randint(0, 15),
        market_risk=random.choice(["低风险", "中等风险", "高风险"]),
        pending_signals=random.randint(0, 10)
    )

    core_signals = CoreSignalCounts(
        buy_signals=random.randint(0, 5),
        watch_signals=random.randint(0, 8),
        sell_signals=random.randint(0, 3)
    )

    latest_opportunities = [
        LatestOpportunityItem(type='buy', name='模拟股票A', ts_code='60000A.SH', reason='模拟买入理由1', price=round(random.uniform(10,50),2)),
        LatestOpportunityItem(type='watch', name='模拟股票B', ts_code='00000B.SZ', reason='模拟观察理由1', price=round(random.uniform(5,20),2)),
        LatestOpportunityItem(type='buy', name='模拟ETF C', ts_code='15990C.SZ', reason='模拟买入理由2', price=round(random.uniform(1,5),3)),
    ]

    # 模拟市场趋势数据 (例如最近30个交易日)
    market_trend = []
    current_date = datetime.now()
    index_start_value = 3000
    vix_start_value = 20
    for i in range(30):
        day = current_date - timedelta(days=i)
        index_start_value = index_start_value * (1 + random.uniform(-0.015, 0.015))
        vix_start_value = vix_start_value * (1 + random.uniform(-0.03, 0.03))
        market_trend.append(MarketTrendDataPoint(
            date=day.strftime('%Y-%m-%d'),
            index_value=round(index_start_value, 2),
            vix_value=round(vix_start_value, 2) if random.random() > 0.1 else None # 模拟VIX有时可能缺失
        ))
    market_trend.reverse() # 日期从旧到新

    # --- END: 模拟数据生成 ---

    return DashboardData(
        summary=summary,
        core_signals=core_signals,
        latest_opportunities=latest_opportunities,
        market_trend=market_trend
    )

# 确保导入 timedelta
from datetime import timedelta