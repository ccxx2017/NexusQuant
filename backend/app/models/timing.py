# --- START OF FILE backend/app/models/timing.py ---
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from app.models.strategy import StrategyParam # 复用之前的参数模型

class TimingStrategyConfig(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    params: List[StrategyParam] = [] # 例如 RSI周期, RSI阈值
    tags: List[str] = []

class TimingSignalRequest(BaseModel):
    target_tickers: List[str] = Field(..., description="需要进行择时分析的股票代码列表", min_items=1)
    strategy_id: str = Field(..., description="选择的择时策略ID")
    params: Dict[str, Any] = Field(default_factory=dict, description="用户调整后的策略参数")
    # 可选：全局参数，如信号回溯期等
    # signal_lookback_days: Optional[int] = 90 

class TimingSignalItem(BaseModel):
    ts_code: str
    name: Optional[str] = None # 股票名称，可以从stock_basic获取
    signal_type: str # 例如 "BUY_RSI_OVERSOLD", "SELL_RSI_OVERBOUGHT", "OBSERVE_MA_CROSS"
    trigger_date: str # 信号触发日期 YYYY-MM-DD
    trigger_price: Optional[float] = None # 信号触发时的价格（例如当日收盘价）
    signal_strength: Optional[float] = None # 信号强度 (0-1, 或其他度量)
    indicator_values: Optional[Dict[str, Any]] = None # 触发时相关的指标值，如 {"rsi": 25.5}
    notes: Optional[str] = None # 其他备注

class TimingSignalResponse(BaseModel):
    signals: List[TimingSignalItem]
    strategy_used: str
    params_used: Dict[str, Any]
    request_timestamp: str # 请求处理时间
    data_timestamp: Optional[str] = None # 所用行情数据的最新日期
# --- END OF FILE backend/app/models/timing.py ---