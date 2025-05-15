# --- START OF FILE backend/app/services/exit_service.py ---
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from app.db.models import Holding as HoldingDBModel # SQLAlchemy 模型
from app.models.exit import ( # Pydantic 模型
    HoldingItemCreate, 
    HoldingItem as HoldingItemResponse, 
    ExitSignalItem
)
from app.services.tushare_client import ts_client # 用于获取最新价格和股票名称
import pandas as pd
from datetime import datetime, date # 导入 date
import logging

logger = logging.getLogger(__name__)

class ExitService:
    def __init__(self):
        self.ts_client = ts_client
        # 缓存股票基本信息，用于填充股票名称
        self.stock_basic_info: Optional[pd.DataFrame] = None
        self._load_stock_basic_info_if_needed()

    def _load_stock_basic_info_if_needed(self):
        if self.stock_basic_info is None:
            logger.info("ExitService: Loading stock basic info...")
            # 确保获取 'ts_code' 和 'name'
            self.stock_basic_info = self.ts_client.get_stock_basic(fields='ts_code,name,industry')
            if self.stock_basic_info is not None:
                self.stock_basic_info.set_index('ts_code', inplace=True)
                logger.info(f"ExitService: Stock basic info loaded. Total stocks: {len(self.stock_basic_info)}")
            else:
                logger.warning("ExitService: Failed to load stock basic info.")

    def _get_stock_name(self, ts_code: str) -> Optional[str]:
        self._load_stock_basic_info_if_needed() # 确保已加载
        if self.stock_basic_info is not None and ts_code in self.stock_basic_info.index:
            name = self.stock_basic_info.loc[ts_code, 'name']
            return str(name) if pd.notna(name) else None
        return None

    async def _get_current_price_for_ticker(self, ts_code: str) -> Tuple[Optional[float], Optional[str]]:
        """获取单个标的的最新价格和最新交易日期"""
        # 获取最近一个交易日的数据即可
        # Tushare daily_basic 可以获取最新交易日的收盘价
        # 或者用 pro_bar 获取 end_date 为今天的最近一条记录
        today_str = datetime.now().strftime('%Y%m%d')
        
        # 优先尝试 daily_basic 获取最新交易日的数据
        # 注意：daily_basic可能不是实时更新的，如果需要更实时，可以考虑其他接口或get_daily_data取最后一条
        daily_basic_df = self.ts_client.get_daily_basic_for_date(trade_date=None, ts_codes_tuple=(ts_code,)) # 改为元组
        
        if daily_basic_df is not None and not daily_basic_df.empty:
            latest_record = daily_basic_df.iloc[0] # 假设按日期降序（或只有一个最新日期）
            current_price = latest_record.get('close')
            trade_date = latest_record.get('trade_date') # YYYYMMDD格式
            if pd.notna(current_price) and pd.notna(trade_date):
                return float(current_price), str(trade_date)
        
        # 如果 daily_basic 未获取到，尝试用 pro_bar 获取最近一天的数据
        logger.info(f"ExitService: daily_basic failed for {ts_code}, trying pro_bar.")
        daily_df = self.ts_client.get_daily_data(ts_code=ts_code, start_date=(datetime.now() - timedelta(days=7)).strftime('%Y%m%d'), end_date=today_str)
        if daily_df is not None and not daily_df.empty:
            latest_record = daily_df.iloc[-1] # 最后一行是最新数据
            current_price = latest_record.get('close')
            trade_date_dt = daily_df.index[-1] # DatetimeIndex
            if pd.notna(current_price) and pd.notna(trade_date_dt):
                return float(current_price), trade_date_dt.strftime('%Y%m%d')
                
        logger.warning(f"ExitService: Could not fetch current price for {ts_code}")
        return None, None

    def _enrich_holding_item(self, db_holding: HoldingDBModel, current_price: Optional[float]) -> HoldingItemResponse:
        """将数据库模型转换为Pydantic响应模型，并计算盈亏"""
        profit_loss_amount = None
        profit_loss_percent = None
        if current_price is not None and pd.notna(db_holding.cost_price) and pd.notna(db_holding.quantity):
            profit_loss_amount = (current_price - db_holding.cost_price) * db_holding.quantity
            if db_holding.cost_price > 0: # 避免除以零
                profit_loss_percent = ((current_price - db_holding.cost_price) / db_holding.cost_price) * 100
        
        stock_name = self._get_stock_name(db_holding.ts_code)

        return HoldingItemResponse(
            id=db_holding.id,
            ts_code=db_holding.ts_code,
            name=stock_name,
            cost_price=db_holding.cost_price,
            quantity=db_holding.quantity,
            open_date=date.fromisoformat(db_holding.open_date) if isinstance(db_holding.open_date, str) else db_holding.open_date, # 确保是date类型
            notes=db_holding.notes,
            current_price=round(current_price, 2) if current_price is not None else None,
            profit_loss_amount=round(profit_loss_amount, 2) if profit_loss_amount is not None else None,
            profit_loss_percent=round(profit_loss_percent, 2) if profit_loss_percent is not None else None,
        )

    # --- 持仓管理 CRUD ---
    async def create_holding(self, db: Session, holding_data: HoldingItemCreate) -> HoldingItemResponse:
        # 检查股票代码是否存在 (可选，但推荐)
        stock_name = self._get_stock_name(holding_data.ts_code)
        if stock_name is None:
            raise ValueError(f"Stock code {holding_data.ts_code} not found or Tushare basic info not loaded.")

        db_holding = HoldingDBModel(
            ts_code=holding_data.ts_code,
            cost_price=holding_data.cost_price,
            quantity=holding_data.quantity,
            open_date=holding_data.open_date.isoformat(), # 存为字符串
            notes=holding_data.notes
            # user_id 可以从当前登录用户获取，如果实现了用户系统
        )
        db.add(db_holding)
        db.commit()
        db.refresh(db_holding)
        logger.info(f"ExitService: Created holding ID {db_holding.id} for {db_holding.ts_code}")
        
        current_price, _ = await self._get_current_price_for_ticker(db_holding.ts_code)
        return self._enrich_holding_item(db_holding, current_price)

    async def get_all_holdings_with_details(self, db: Session, skip: int = 0, limit: int = 100) -> List[HoldingItemResponse]:
        db_holdings = db.query(HoldingDBModel).offset(skip).limit(limit).all()
        enriched_holdings = []
        for db_holding in db_holdings:
            current_price, _ = await self._get_current_price_for_ticker(db_holding.ts_code)
            enriched_holdings.append(self._enrich_holding_item(db_holding, current_price))
        return enriched_holdings

    async def get_holding_with_details_by_id(self, db: Session, holding_id: int) -> Optional[HoldingItemResponse]:
        db_holding = db.query(HoldingDBModel).filter(HoldingDBModel.id == holding_id).first()
        if db_holding:
            current_price, _ = await self._get_current_price_for_ticker(db_holding.ts_code)
            return self._enrich_holding_item(db_holding, current_price)
        return None
        
    async def update_holding(self, db: Session, holding_id: int, holding_data: HoldingItemCreate) -> Optional[HoldingItemResponse]:
        db_holding = db.query(HoldingDBModel).filter(HoldingDBModel.id == holding_id).first()
        if db_holding:
            # 检查股票代码是否改变，如果改变，也需要确认新代码的有效性
            if db_holding.ts_code != holding_data.ts_code:
                stock_name = self._get_stock_name(holding_data.ts_code)
                if stock_name is None:
                    raise ValueError(f"New stock code {holding_data.ts_code} not found.")
            
            db_holding.ts_code = holding_data.ts_code
            db_holding.cost_price = holding_data.cost_price
            db_holding.quantity = holding_data.quantity
            db_holding.open_date = holding_data.open_date.isoformat()
            db_holding.notes = holding_data.notes
            # db_holding.updated_at = datetime.utcnow() # SQLAlchemy 的 onupdate 会自动处理
            db.commit()
            db.refresh(db_holding)
            logger.info(f"ExitService: Updated holding ID {db_holding.id}")
            current_price, _ = await self._get_current_price_for_ticker(db_holding.ts_code)
            return self._enrich_holding_item(db_holding, current_price)
        return None

    async def delete_holding(self, db: Session, holding_id: int) -> bool:
        db_holding = db.query(HoldingDBModel).filter(HoldingDBModel.id == holding_id).first()
        if db_holding:
            db.delete(db_holding)
            db.commit()
            logger.info(f"ExitService: Deleted holding ID {holding_id}")
            return True
        return False

    # --- 退出信号检查 ---
    async def check_exit_signals_for_holdings(
        self,
        db: Session,
        holding_ids: Optional[List[int]],
        strategy_id: str,
        params: Dict[str, Any]
    ) -> Tuple[List[ExitSignalItem], Optional[str]]:
        logger.info(f"ExitService: Checking exit signals for strategy='{strategy_id}', holding_ids={holding_ids}, params={params}")
        
        signals: List[ExitSignalItem] = []
        latest_data_date_across_all_tickers: Optional[str] = None

        # 确定要检查的持仓
        holdings_to_check: List[HoldingDBModel] = []
        if holding_ids:
            for h_id in holding_ids:
                h = db.query(HoldingDBModel).filter(HoldingDBModel.id == h_id).first()
                if h:
                    holdings_to_check.append(h)
                else:
                    logger.warning(f"Holding ID {h_id} not found in DB, skipping.")
        else: # 如果 holding_ids 为 None 或空，则检查所有持仓
            holdings_to_check = db.query(HoldingDBModel).all()
        
        if not holdings_to_check:
            logger.info("No holdings to check for exit signals.")
            return [], None

        today_str_for_signal = datetime.now().strftime('%Y-%m-%d') # 信号触发日期用标准格式

        for db_holding in holdings_to_check:
            current_price, trade_date_yyyymmdd = await self._get_current_price_for_ticker(db_holding.ts_code)
            
            if current_price is None or trade_date_yyyymmdd is None:
                logger.warning(f"Could not get current price for {db_holding.ts_code}, cannot check exit signal for holding ID {db_holding.id}")
                continue

            # 更新行情数据的最新日期
            # trade_date_yyyymmdd 是 YYYYMMDD 格式，转换为 YYYY-MM-DD
            trade_date_standard = f"{trade_date_yyyymmdd[:4]}-{trade_date_yyyymmdd[4:6]}-{trade_date_yyyymmdd[6:]}"
            if latest_data_date_across_all_tickers is None or trade_date_standard > latest_data_date_across_all_tickers:
                latest_data_date_across_all_tickers = trade_date_standard
            
            stock_name = self._get_stock_name(db_holding.ts_code)

            if strategy_id == "fixed_profit_loss":
                take_profit_percent = params.get("take_profit_percent", 20.0) / 100.0 # 转为小数
                stop_loss_percent = params.get("stop_loss_percent", -10.0) / 100.0   # 转为小数 (通常是负数)

                profit_target_price = db_holding.cost_price * (1 + take_profit_percent)
                loss_target_price = db_holding.cost_price * (1 + stop_loss_percent) # stop_loss_percent是负数

                logger.info(f"  Checking {db_holding.ts_code} (ID:{db_holding.id}): Cost={db_holding.cost_price:.2f}, Current={current_price:.2f}, TP Target={profit_target_price:.2f}, SL Target={loss_target_price:.2f}")

                signal_generated_for_this_holding = False
                # 检查止盈
                if current_price >= profit_target_price:
                    signals.append(ExitSignalItem(
                        holding_id=db_holding.id,
                        ts_code=db_holding.ts_code,
                        name=stock_name,
                        signal_type="TAKE_PROFIT_FIXED",
                        trigger_date=today_str_for_signal, # 用当前检查日期作为信号日期
                        trigger_price=current_price,
                        target_price=round(profit_target_price, 2),
                        notes=f"达到固定止盈目标 ({params.get('take_profit_percent')}%)。成本价: {db_holding.cost_price:.2f}, 目标价: {profit_target_price:.2f}"
                    ))
                    signal_generated_for_this_holding = True
                    logger.info(f"    TAKE_PROFIT signal generated for {db_holding.ts_code}")
                
                # 检查止损 (如果尚未触发止盈)
                # 注意：止损价格应该低于成本价
                if not signal_generated_for_this_holding and current_price <= loss_target_price:
                    signals.append(ExitSignalItem(
                        holding_id=db_holding.id,
                        ts_code=db_holding.ts_code,
                        name=stock_name,
                        signal_type="STOP_LOSS_FIXED",
                        trigger_date=today_str_for_signal,
                        trigger_price=current_price,
                        target_price=round(loss_target_price, 2),
                        notes=f"触发固定止损 ({params.get('stop_loss_percent')}%)。成本价: {db_holding.cost_price:.2f}, 止损价: {loss_target_price:.2f}"
                    ))
                    logger.info(f"    STOP_LOSS signal generated for {db_holding.ts_code}")
            else:
                # 如果有其他策略，可以在这里添加 elif strategy_id == "other_strategy":
                pass # 暂时忽略未知策略，或者也可以抛出错误

        if not signals and not holdings_to_check: # 如果没有持仓可查，返回空
            return [], latest_data_date_across_all_tickers
        elif not signals: # 有持仓但无信号
            logger.info("No exit signals generated for the checked holdings.")
            return [], latest_data_date_across_all_tickers
            
        return signals, latest_data_date_across_all_tickers

# --- END OF FILE backend/app/services/exit_service.py ---