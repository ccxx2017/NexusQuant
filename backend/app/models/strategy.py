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
    current_price: Optional[float] = None # 需要实时获取
    # ... 其他选品策略输出的指标 ...
    roe: Optional[float] = None
    pb: Optional[float] = None
    momentum_6m: Optional[float] = None
    composite_score: Optional[int] = None


class SelectionPoolRequest(BaseModel):
    strategy_id: str
    params: Dict[str, Any] # 用户调整后的参数键值对

class SelectionPoolResponse(BaseModel):
    items: List[SelectedPoolItem]
    strategy_used: str
    params_used: Dict[str, Any]
    timestamp: str