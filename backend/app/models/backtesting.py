# --- START OF FILE backend/app/models/backtesting.py ---
from pydantic import BaseModel, Field, model_validator # <--- 导入 model_validator
from typing import List, Dict, Any, Optional
from datetime import date

# 复用之前的参数定义
from app.models.strategy import StrategyParam

# 定义回测请求中各个策略模块的配置
class BacktestSelectionConfig(BaseModel):
    target_tickers: List[str] = Field(..., min_items=1, description="回测标的股票代码列表")

class BacktestTimingConfig(BaseModel):
    strategy_id: str = Field(..., description="择时策略ID")
    params: Dict[str, Any] = Field(default_factory=dict, description="择时策略参数")

class BacktestExitConfig(BaseModel):
    strategy_id: str = Field(..., description="退出策略ID")
    params: Dict[str, Any] = Field(default_factory=dict, description="退出策略参数")

class BacktestRunRequest(BaseModel):
    name: Optional[str] = Field(None, description="回测任务名称 (用户可选填)")
    start_date: date = Field(..., description="回测开始日期 (YYYY-MM-DD)")
    end_date: date = Field(..., description="回测结束日期 (YYYY-MM-DD)")
    initial_cash: float = Field(100000.0, gt=0, description="初始资金")
    commission_percent: float = Field(0.0005, ge=0, lt=0.1, description="手续费率 (例如 0.0005 表示万分之五)")
    
    selection_config: BacktestSelectionConfig = Field(..., description="选品配置 (初期为直接指定标的)")
    timing_config: Optional[BacktestTimingConfig] = None # Field(None, description="择时策略配置 (可选)") # 保持 None
    exit_config: Optional[BacktestExitConfig] = None # Field(None, description="退出策略配置 (可选)") # 保持 None
    
    @model_validator(mode='after') # <--- 使用新的 model_validator
    def check_dates(cls, values):
        start_date, end_date = values.start_date, values.end_date # <--- 直接从 self 中获取属性
        if start_date and end_date and end_date <= start_date: # <--- 确保两者都存在
            raise ValueError('回测结束日期必须晚于开始日期')
        return values # <--- 返回整个模型实例

# 回测结果中的绩效指标
class BacktestPerformanceMetrics(BaseModel):
    total_return_percent: Optional[float] = None
    annual_return_percent: Optional[float] = None
    max_drawdown_percent: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    win_rate_percent: Optional[float] = None # 胜率
    profit_factor: Optional[float] = None # 盈亏比或盈利因子
    total_trades: Optional[int] = None

# 回测结果中的净值曲线数据点
class EquityDataPoint(BaseModel):
    date: str # YYYY-MM-DD
    value: float # 当日净值

class BacktestRunResponse(BaseModel):
    run_id: str # 后端生成的回测运行ID
    request_params: BacktestRunRequest # 本次回测的请求参数，方便追溯
    status: str = Field("completed", description="回测状态 (例如: pending, running, completed, failed)")
    message: Optional[str] = None # 成功或失败的消息
    performance: Optional[BacktestPerformanceMetrics] = None
    equity_curve: Optional[List[EquityDataPoint]] = None
# --- END OF FILE backend/app/models/backtesting.py ---