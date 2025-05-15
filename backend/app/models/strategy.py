from pydantic import BaseModel,Field
from typing import Any, Optional, Literal, Union,List,Dict

class StrategyParam(BaseModel):
    name: str # 参数的内部标识名，例如 "rsi_period"
    label: str # 参数在UI上显示的名称，例如 "RSI周期"
    value: Any # 参数的当前/默认值
    
    # type 字段用于指导UI渲染和后端处理
    # "number" -> el-slider / el-input-number
    # "boolean" -> el-switch
    # "string" -> el-input
    # "select" -> el-select (需要配合 options 字段)
    type: Literal["number", "boolean", "string", "select"] = "number" 

    # 仅当 type == "number" 时以下字段有意义
    min_value: Optional[Union[float, int]] = None
    max_value: Optional[Union[float, int]] = None
    step: Optional[Union[float, int]] = None
    unit: Optional[str] = None
    
    # 仅当 type == "select" 时以下字段有意义
    options: Optional[List[Dict[str, Any]]] = None # 例如 [{"label": "选项1", "value": "opt1"}, ...]
    
    description: Optional[str] = None

    # 可以添加一个 validator 来确保当 type="number" 时，min/max/step 是数字类型
    # 并且当 type="select" 时，options 存在
    # 但为了保持简单，暂时不加，依赖于策略定义者的正确配置

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