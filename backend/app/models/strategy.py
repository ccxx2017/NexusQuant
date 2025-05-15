from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class StrategyParam(BaseModel):
    name: str
    value: Any
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    step: Optional[Any] = None
    unit: Optional[str] = None
    description: Optional[str] = None

class StrategyConfig(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    params: List[StrategyParam] = []
    tags: List[str] = []
    # 预期的历史表现摘要，初期可以是静态的
    historical_performance_summary: Optional[Dict[str, str]] = None


class SelectedPoolItem(BaseModel):
    ts_code: str
    name: str
    current_price: Optional[float] = None
    roe: Optional[float] = None
    pb: Optional[float] = None # 市净率
    pe_ttm: Optional[float] = None # 市盈率 TTM
    dividend_yield_ratio: Optional[float] = None # 股息率 (例如 0.02 表示 2%)
    total_mv: Optional[float] = None # 总市值（亿元）
    momentum_6m: Optional[float] = None
    composite_score: Optional[int] = None
    # 可以添加更多策略可能需要的字段


class SelectionPoolRequest(BaseModel):
    strategy_id: str
    params: Dict[str, Any] # 用户调整后的参数键值对

class SelectionPoolResponse(BaseModel):
    items: List[SelectedPoolItem]
    strategy_used: str
    params_used: Dict[str, Any]
    timestamp: str