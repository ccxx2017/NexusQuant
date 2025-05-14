# backend/app/api/v1/endpoints/backtesting_lab.py
from fastapi import APIRouter, HTTPException, Body, BackgroundTasks
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, date
import asyncio
import random
import pandas as pd

# --- Pydantic Models (理想情况下应在 app/models/backtest.py 中定义) ---
class StrategySetting(BaseModel):
    id: str
    params: Dict[str, Any] = {}

class BacktestConfig(BaseModel):
    start_date: date
    end_date: date
    initial_cash: float = Field(default=1000000, gt=0)
    commission_bps: float = Field(default=2.5, ge=0) # 万分之
    benchmark_ticker: Optional[str] = None

class BacktestRequest(BaseModel):
    selection_strategy: StrategySetting
    timing_strategy: StrategySetting
    exit_strategy: StrategySetting
    backtest_config: BacktestConfig
    target_tickers: Optional[List[str]] = None # 可选，如果指定，则只在这些标的中回测

class PerformanceSummary(BaseModel):
    total_return: float
    annual_return: float
    max_drawdown: float
    sharpe_ratio: float
    sortino_ratio: Optional[float] = None
    alpha: Optional[float] = None
    beta: Optional[float] = None
    win_rate: Optional[float] = None
    profit_loss_ratio: Optional[float] = None

class EquityCurveDataPoint(BaseModel):
    date: str # YYYY-MM-DD
    value: float

class TradesSummary(BaseModel):
    total_trades: Optional[int] = None
    # ... more trade stats ...

class BacktestResult(BaseModel):
    performance_summary: PerformanceSummary
    equity_curve: Dict[str, List[EquityCurveDataPoint]] # keys: "strategy", "benchmark"
    trades_summary: Optional[TradesSummary] = None
    config_used: Dict[str, Any] # 本次回测使用的配置
    timestamp: str
    status: str = "completed" # "running", "completed", "failed"
    message: Optional[str] = None


router = APIRouter()

# 模拟一个长时间运行的回测任务
async def run_simulated_backtest_task(result_id: str, request_payload: Dict):
    print(f"Background task for backtest {result_id} started.")
    await asyncio.sleep(random.uniform(5, 10)) # 模拟回测耗时
    
    # --- START: 模拟生成回测结果 ---
    start_val = request_payload["backtest_config"]["initial_cash"]
    dates = pd.date_range(start=request_payload["backtest_config"]["start_date"], 
                          end=request_payload["backtest_config"]["end_date"], 
                          freq='B') # Business days
    
    strategy_equity = [start_val]
    benchmark_equity = [start_val]
    for _ in range(1, len(dates)):
        strategy_equity.append(strategy_equity[-1] * (1 + random.uniform(-0.015, 0.02)))
        benchmark_equity.append(benchmark_equity[-1] * (1 + random.uniform(-0.01, 0.015)))

    simulated_result = BacktestResult(
        performance_summary=PerformanceSummary(
            total_return=(strategy_equity[-1] / start_val) - 1,
            annual_return=random.uniform(0.05, 0.25),
            max_drawdown=-random.uniform(0.05, 0.30),
            sharpe_ratio=random.uniform(0.5, 2.0),
            win_rate=random.uniform(0.4, 0.7),
            profit_loss_ratio=random.uniform(1.0, 3.0)
        ),
        equity_curve={
            "strategy": [{"date": dt.strftime('%Y-%m-%d'), "value": val} for dt, val in zip(dates, strategy_equity)],
            "benchmark": [{"date": dt.strftime('%Y-%m-%d'), "value": val} for dt, val in zip(dates, benchmark_equity)]
        },
        trades_summary=TradesSummary(total_trades=random.randint(50, 200)),
        config_used=request_payload,
        timestamp=datetime.now().isoformat(),
        status="completed"
    )
    # --- END: 模拟生成回测结果 ---

    # 实际项目中，这里应该将结果保存到数据库或缓存，以便前端后续查询
    # 例如: results_store[result_id] = simulated_result.dict()
    print(f"Background task for backtest {result_id} finished. Result (simulated): {simulated_result.performance_summary.total_return}")
    # For now, we are not storing results for polling, just simulating the delay.
    # The actual result will be returned directly if not using background tasks for real.

# 模拟存储回测结果的地方 (实际应使用DB或Redis)
results_store: Dict[str, Dict] = {}


@router.post("/backtesting-lab/run_backtest", response_model=BacktestResult, status_code=200) # Changed to 200 for direct return
async def run_backtest_endpoint(request: BacktestRequest = Body(...), background_tasks: BackgroundTasks = None):
    """
    接收策略组合和配置，运行回测。
    对于长时间回测，应该使用后台任务并提供查询状态的接口。
    当前版本将直接模拟并返回结果。
    """
    print(f"Received backtest request: {request.dict(exclude_none=True)}")

    # --- 模拟调用 BacktestingService ---
    # from app.services.backtesting_service import backtesting_service_instance # 假设有此实例
    # try:
    #     # 对于真实回测，这可能是个耗时操作
    #     # result_data = await backtesting_service_instance.run_backtest(request)
    #     # return result_data
    # except Exception as e:
    #     print(f"Backtest failed: {e}")
    #     # raise HTTPException(status_code=500, detail=f"Backtest execution failed: {str(e)}")
    # ---

    # --- START: 直接运行模拟回测并返回结果 (不使用后台任务的简化版) ---
    request_payload = request.dict(exclude_none=True) # 用于模拟任务
    await asyncio.sleep(random.uniform(1, 3)) # 模拟回测耗时
    
    start_val = request_payload["backtest_config"]["initial_cash"]
    # 需要 pandas 来生成日期范围
    try:
        import pandas as pd
    except ImportError:
        raise HTTPException(status_code=500, detail="Pandas library not installed, needed for date range generation in simulation.")

    dates = pd.date_range(start=request_payload["backtest_config"]["start_date"], 
                          end=request_payload["backtest_config"]["end_date"], 
                          freq='B')
    
    strategy_equity = [start_val]
    benchmark_equity = [start_val]
    for _ in range(1, len(dates)):
        strategy_equity.append(strategy_equity[-1] * (1 + random.uniform(-0.015, 0.02)))
        benchmark_equity.append(benchmark_equity[-1] * (1 + random.uniform(-0.01, 0.015)))

    simulated_result = BacktestResult(
        performance_summary=PerformanceSummary(
            total_return=(strategy_equity[-1] / start_val) - 1,
            annual_return=random.uniform(0.05, 0.25),
            max_drawdown=-random.uniform(0.05, 0.30),
            sharpe_ratio=random.uniform(0.5, 2.0),
            win_rate=random.uniform(0.4, 0.7),
            profit_loss_ratio=random.uniform(1.0, 3.0)
        ),
        equity_curve={
            "strategy": [{"date": dt.strftime('%Y-%m-%d'), "value": round(val,2)} for dt, val in zip(dates, strategy_equity)],
            "benchmark": [{"date": dt.strftime('%Y-%m-%d'), "value": round(val,2)} for dt, val in zip(dates, benchmark_equity)] if request.backtest_config.benchmark_ticker else []
        },
        trades_summary=TradesSummary(total_trades=random.randint(50, 200)),
        config_used=request_payload,
        timestamp=datetime.now().isoformat(),
        status="completed"
    )
    return simulated_result
    # --- END: 直接运行模拟回测并返回结果 ---


    # --- 使用后台任务的逻辑 (如果回测非常耗时) ---
    # import uuid
    # result_id = str(uuid.uuid4())
    # results_store[result_id] = {"status": "running", "message": "Backtest started..."}
    # # background_tasks.add_task(run_simulated_backtest_task, result_id, request.dict(exclude_none=True))
    # # return {"result_id": result_id, "status": "running", "message": "Backtest submitted, check status later."}
    # ---

# (可选) 如果使用后台任务，需要一个查询状态的接口
# @router.get("/backtesting-lab/result/{result_id}")
# async def get_backtest_result(result_id: str):
#     result = results_store.get(result_id)
#     if not result:
#         raise HTTPException(status_code=404, detail="Backtest result not found or not yet completed.")
#     return result