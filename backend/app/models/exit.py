# --- START OF FILE backend/app/models/exit.py ---
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from datetime import date, datetime # 导入 date 和 datetime
from app.models.strategy import StrategyParam # 复用之前的参数模型

class HoldingItemBase(BaseModel):
    ts_code: str = Field(..., description="股票代码 (例如 000001.SZ)")
    cost_price: float = Field(..., gt=0, description="持仓成本价")
    quantity: int = Field(..., gt=0, description="持仓数量 (股)")
    open_date: date = Field(..., description="开仓日期 (YYYY-MM-DD)")
    # 可选：备注
    notes: Optional[str] = None

class HoldingItemCreate(HoldingItemBase):
    pass

class HoldingItem(HoldingItemBase):
    id: int # 数据库自增ID或由其他方式生成的唯一ID
    name: Optional[str] = None # 股票名称，由后端填充
    current_price: Optional[float] = None # 最新价格，由后端填充
    profit_loss_amount: Optional[float] = None # 盈亏金额，由后端计算
    profit_loss_percent: Optional[float] = None # 盈亏百分比，由后端计算
    # 可选：上次检查退出信号的时间
    # last_checked_at: Optional[datetime] = None 

    class Config:
        orm_mode = True # 如果未来使用ORM，需要这个

class ExitStrategyConfig(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    params: List[StrategyParam] = [] # 例如 止盈百分比, 止损百分比
    tags: List[str] = []

class ExitSignalRequest(BaseModel):
    # 可以选择检查所有持仓，或指定部分持仓ID
    # 如果后端不存储持仓，则每次请求都需要传递持仓列表
    # 我们先假设后端会存储持仓，并提供一个获取所有持仓的接口
    # 那么检查信号时，可以不传具体持仓，由后端服务处理所有（或用户标记的）活跃持仓
    # 或者，允许用户明确指定要检查的持仓ID
    holding_ids: Optional[List[int]] = Field(None, description="要检查退出信号的持仓ID列表 (如果为None或空，则检查所有活跃持仓)")
    strategy_id: str = Field(..., description="选择的退出策略ID")
    params: Dict[str, Any] = Field(default_factory=dict, description="用户调整后的退出策略参数")

class ExitSignalItem(BaseModel):
    holding_id: int # 关联的持仓ID
    ts_code: str
    name: Optional[str] = None
    signal_type: str # 例如 "TAKE_PROFIT_FIXED", "STOP_LOSS_FIXED", "TRAILING_STOP_LOSS"
    trigger_date: str # 信号触发日期 YYYY-MM-DD (通常是当前检查日期)
    trigger_price: float # 信号触发时的价格（通常是当前最新价）
    target_price: Optional[float] = None # 止盈/止损目标价
    notes: Optional[str] = None # 备注，例如 "达到20%止盈目标"

class ExitSignalResponse(BaseModel):
    signals: List[ExitSignalItem]
    strategy_used: str
    params_used: Dict[str, Any]
    request_timestamp: str
    data_timestamp: Optional[str] = None # 行情数据的最新日期
# --- END OF FILE backend/app/models/exit.py ---