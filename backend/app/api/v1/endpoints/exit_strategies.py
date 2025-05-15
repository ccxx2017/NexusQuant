# --- START OF FILE backend/app/api/v1/endpoints/exit_strategies.py ---
from fastapi import APIRouter, HTTPException, Body, Depends
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.db.database import get_db # 用于数据库会话依赖注入
from app.models.exit import ( # 从我们新创建的模型文件导入
    ExitStrategyConfig, 
    HoldingItemCreate, 
    HoldingItem as HoldingItemResponse, # Pydantic模型用于响应
    ExitSignalRequest, 
    ExitSignalResponse
)
# 假设我们也会创建一个 ExitService
from app.services.exit_service import ExitService
from datetime import datetime
from app.models.strategy import StrategyParam 

router = APIRouter()
exit_service = ExitService() # 实例化服务

# 预设的退出策略 (与选品、择时类似)
# 预设的退出策略
PRESET_EXIT_STRATEGIES = [
    ExitStrategyConfig(
        id="fixed_profit_loss",
        name="固定比例止盈止损",
        description="当持仓达到预设的止盈百分比或止损百分比时触发退出信号。",
        params=[
            StrategyParam(name="take_profit_percent", label="止盈百分比", value=20.0, type="number", min_value=1.0, max_value=200.0, step=1.0, unit="%", description="从成本价计算的止盈目标百分比"),
            StrategyParam(name="stop_loss_percent", label="止损百分比", value=-10.0, type="number", min_value=-100.0, max_value=-1.0, step=1.0, unit="%", description="从成本价计算的止损目标百分比 (负数)"),
        ],
        tags=["风险管理", "止盈", "止损"]
    ),
    # 未来可以添加更多退出策略，例如：
    # ExitStrategyConfig(id="trailing_stop_loss", name="移动止损", ...),
]

@router.get("/strategies", response_model=List[ExitStrategyConfig])
async def get_exit_strategies_endpoint():
    """获取所有预设的退出策略配置"""
    return PRESET_EXIT_STRATEGIES

# --- 持仓管理 CRUD 操作 ---
@router.post("/holdings", response_model=HoldingItemResponse, status_code=201)
async def create_holding_endpoint(
    holding_data: HoldingItemCreate, 
    db: Session = Depends(get_db)
):
    """添加一个新的持仓记录"""
    try:
        created_holding = await exit_service.create_holding(db=db, holding_data=holding_data)
        return created_holding
    except ValueError as e: # 例如股票代码不存在
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating holding: {str(e)}")

@router.get("/holdings", response_model=List[HoldingItemResponse])
async def get_all_holdings_endpoint(
    db: Session = Depends(get_db),
    skip: int = 0, # 分页参数
    limit: int = 100 # 分页参数
):
    """获取所有持仓记录 (带最新价格和盈亏信息)"""
    holdings_with_details = await exit_service.get_all_holdings_with_details(db=db, skip=skip, limit=limit)
    return holdings_with_details
    
@router.get("/holdings/{holding_id}", response_model=HoldingItemResponse)
async def get_holding_by_id_endpoint(
    holding_id: int, 
    db: Session = Depends(get_db)
):
    """根据ID获取单个持仓记录 (带最新价格和盈亏信息)"""
    holding = await exit_service.get_holding_with_details_by_id(db=db, holding_id=holding_id)
    if holding is None:
        raise HTTPException(status_code=404, detail="Holding not found")
    return holding

@router.put("/holdings/{holding_id}", response_model=HoldingItemResponse)
async def update_holding_endpoint(
    holding_id: int, 
    holding_data: HoldingItemCreate, # 使用Create模型作为更新，也可以定义专门的Update模型
    db: Session = Depends(get_db)
):
    """更新指定的持仓记录"""
    updated_holding = await exit_service.update_holding(db=db, holding_id=holding_id, holding_data=holding_data)
    if updated_holding is None:
        raise HTTPException(status_code=404, detail="Holding not found")
    return updated_holding

@router.delete("/holdings/{holding_id}", status_code=204) # 204 No Content
async def delete_holding_endpoint(
    holding_id: int, 
    db: Session = Depends(get_db)
):
    """删除指定的持仓记录"""
    success = await exit_service.delete_holding(db=db, holding_id=holding_id)
    if not success:
        raise HTTPException(status_code=404, detail="Holding not found or could not be deleted")
    return # FastAPI 会自动处理 204 的空响应体

# --- 退出信号生成 ---
@router.post("/check_signals", response_model=ExitSignalResponse)
async def check_exit_signals_endpoint(
    request: ExitSignalRequest = Body(...),
    db: Session = Depends(get_db) # 如果需要从数据库读取持仓
):
    """根据选择的退出策略和持仓，检查退出信号"""
    try:
        current_time = datetime.now()
        # ExitService 将负责从数据库获取持仓（如果 request.holding_ids 为 None 或空）
        # 或者只处理 request.holding_ids 中指定的持仓
        signal_items, data_last_date = await exit_service.check_exit_signals_for_holdings(
            db=db,
            holding_ids=request.holding_ids,
            strategy_id=request.strategy_id,
            params=request.params
        )
        return ExitSignalResponse(
            signals=signal_items,
            strategy_used=request.strategy_id,
            params_used=request.params,
            request_timestamp=current_time.isoformat(),
            data_timestamp=data_last_date
        )
    except ValueError as e: # 例如策略ID不存在或持仓不存在
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        import traceback
        print(f"Error in check_exit_signals_endpoint: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error checking exit signals: {str(e)}")

# --- END OF FILE backend/app/api/v1/endpoints/exit_strategies.py ---