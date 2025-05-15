# --- START OF FILE backend/app/services/timing_service.py ---
from typing import List, Dict, Any, Optional, Tuple
from app.services.tushare_client import ts_client
from app.models.timing import TimingSignalItem # 从新模型导入
import pandas as pd
import talib # 导入 TA-Lib
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class TimingService:
    def __init__(self):
        self.ts_client = ts_client
        self.stock_basic_info: Optional[pd.DataFrame] = None
        self._load_stock_basic_info()

    def _load_stock_basic_info(self):
        """加载并缓存股票基本信息，用于获取股票名称等"""
        if self.stock_basic_info is None:
            self.stock_basic_info = self.ts_client.get_stock_basic(fields='ts_code,name')
            if self.stock_basic_info is not None:
                self.stock_basic_info.set_index('ts_code', inplace=True)
                print("TimingService: Stock basic info loaded and cached.")

    def _get_stock_name(self, ts_code: str) -> Optional[str]:
        if self.stock_basic_info is not None and ts_code in self.stock_basic_info.index:
            return self.stock_basic_info.loc[ts_code, 'name']
        return None

    def _get_stock_name_and_industry(self, ts_code: str) -> Tuple[Optional[str], Optional[str]]:
        """
        根据股票代码获取股票名称和行业。
        """
        if self.stock_basic_info is not None and not self.stock_basic_info.empty and ts_code in self.stock_basic_info.index:
            try:
                stock_data = self.stock_basic_info.loc[ts_code]
                name = stock_data.get('name')
                industry = stock_data.get('industry')
                return str(name) if pd.notna(name) else None, str(industry) if pd.notna(industry) else None
            except KeyError: # 以防万一 loc 失败或字段不存在
                logger.warning(f"Could not find name/industry for {ts_code} in cached basic info.")
                return None, None
        logger.warning(f"Stock basic info not loaded or {ts_code} not found in cache.")
        return None, None
    
    async def generate_signals_for_targets(
                self,
                target_tickers: List[str],
                strategy_id: str,
                params: Dict[str, Any]
            ) -> Tuple[List[TimingSignalItem], Optional[str]]:
        logger.info(f"TimingService: Generating signals for strategy='{strategy_id}', targets={target_tickers}, params={params}")

        signals: List[TimingSignalItem] = []
        latest_data_date_across_all_tickers: Optional[str] = None

        if strategy_id == "rsi_oversold_rebound":
            rsi_period = int(params.get("rsi_period", 14))
            rsi_oversold_threshold = float(params.get("rsi_oversold_threshold", 30.0))

            end_date_dt = datetime.now()
            start_date_dt = end_date_dt - timedelta(days=rsi_period + 90) # Ensure enough data for prev_rsi
            end_date_str = end_date_dt.strftime('%Y%m%d')
            start_date_str = start_date_dt.strftime('%Y%m%d')

            for ts_code in target_tickers:
                logger.debug(f"  Processing ticker: {ts_code} for RSI strategy (period: {rsi_period}, threshold: {rsi_oversold_threshold}). Dates: {start_date_str}-{end_date_str}")
                
                daily_df = self.ts_client.get_daily_data(ts_code=ts_code, start_date=start_date_str, end_date=end_date_str, adj='qfq')

                # Need at least rsi_period + 1 days to have a current RSI and a previous RSI
                if daily_df is None or daily_df.empty or len(daily_df) < rsi_period + 1:
                    logger.warning(f"    Skipping {ts_code}: Not enough data for RSI and prev_RSI (need {rsi_period + 1}, got {len(daily_df) if daily_df is not None else 0}).")
                    continue
                
                current_ticker_latest_date_str = daily_df.index[-1].strftime('%Y-%m-%d')
                if latest_data_date_across_all_tickers is None or current_ticker_latest_date_str > latest_data_date_across_all_tickers:
                    latest_data_date_across_all_tickers = current_ticker_latest_date_str

                close_prices = daily_df['close'].to_numpy()
                rsi_values = talib.RSI(close_prices, timeperiod=rsi_period)
                
                # Ensure we have at least two RSI values to compare (current and previous)
                # talib.RSI produces (rsi_period-1) NaNs at the beginning.
                # So, rsi_values[-1] is current_rsi, rsi_values[-2] is prev_rsi.
                # We need at least rsi_period valid close prices for the first RSI, 
                # and rsi_period+1 for the second (which becomes prev_rsi for current_rsi).
                
                if len(rsi_values) < 2 or pd.isna(rsi_values[-1]) or pd.isna(rsi_values[-2]):
                    # This check might be redundant if len(daily_df) < rsi_period + 1 handles it,
                    # but good for robustness.
                    logger.warning(f"    Skipping {ts_code}: Not enough valid RSI values to compare current and previous.")
                    continue

                current_rsi = rsi_values[-1]
                prev_rsi = rsi_values[-2] # RSI of the day before the current_rsi day
                
                trigger_date_dt_obj = daily_df.index[-1] # Date for current_rsi
                trigger_price_val = daily_df['close'].iloc[-1]

                logger.info(f"    {ts_code}: Date: {trigger_date_dt_obj.strftime('%Y-%m-%d')}, Current RSI({rsi_period}): {current_rsi:.2f}, Prev RSI: {prev_rsi:.2f}, Price: {trigger_price_val:.2f}")

                stock_name, stock_industry = self._get_stock_name_and_industry(ts_code)
                signal_generated_for_this_stock = False

                # 1. Check for "RSI_OVERSOLD_TURN_UP" (拐头型反弹)
                if current_rsi < rsi_oversold_threshold and current_rsi > prev_rsi:
                    signal_strength = round((current_rsi - prev_rsi) / (rsi_oversold_threshold - prev_rsi + 1e-6), 2) # Normalize strength, avoid div by zero
                    signal_strength = min(max(signal_strength, 0.1), 0.9) # Cap strength between 0.1 and 0.9 for this type
                    signal_note = f"RSI({rsi_period})在超卖区从{prev_rsi:.2f}拐头向上至{current_rsi:.2f} (阈值:{rsi_oversold_threshold}). 行业：{stock_industry or 'N/A'}"
                    
                    signals.append(TimingSignalItem(
                        ts_code=ts_code,
                        name=stock_name,
                        signal_type="RSI_OVERSOLD_TURN_UP", # 新的信号类型
                        trigger_date=trigger_date_dt_obj.strftime('%Y-%m-%d'),
                        trigger_price=round(float(trigger_price_val), 2) if pd.notna(trigger_price_val) else None,
                        signal_strength=signal_strength,
                        indicator_values={"rsi": round(current_rsi, 2), "prev_rsi": round(prev_rsi, 2), "threshold": rsi_oversold_threshold},
                        notes=signal_note
                    ))
                    signal_generated_for_this_stock = True
                    logger.info(f"      Signal: RSI_OVERSOLD_TURN_UP for {ts_code}")

                # 2. If no "TURN_UP" signal, check for "RSI_IN_OVERSOLD_ZONE" (仍在超卖区 - 观察)
                #    This can be an 'else if' or an independent check. 
                #    If independent, a stock might have both (though less likely with TURN_UP being more specific).
                #    Let's make it an 'else if' for now to avoid duplicate signals for the same core condition.
                elif not signal_generated_for_this_stock and current_rsi < rsi_oversold_threshold:
                    signal_strength = round(1 - (current_rsi / rsi_oversold_threshold), 2) 
                    signal_note = f"RSI({rsi_period})为{current_rsi:.2f}，处于超卖区 (阈值:{rsi_oversold_threshold}). 行业：{stock_industry or 'N/A'}"
                    
                    signals.append(TimingSignalItem(
                        ts_code=ts_code,
                        name=stock_name,
                        signal_type="RSI_IN_OVERSOLD_ZONE", # 新的或修改后的信号类型
                        trigger_date=trigger_date_dt_obj.strftime('%Y-%m-%d'),
                        trigger_price=round(float(trigger_price_val), 2) if pd.notna(trigger_price_val) else None,
                        signal_strength=signal_strength,
                        indicator_values={"rsi": round(current_rsi, 2), "threshold": rsi_oversold_threshold},
                        notes=signal_note
                    ))
                    logger.info(f"      Signal: RSI_IN_OVERSOLD_ZONE for {ts_code}")
            
            return signals, latest_data_date_across_all_tickers
        elif strategy_id == "ma_golden_cross": # 注意：您策略ID用的是 "ma_golden_cross"，而前端之前用的是 "ma_cross"，需统一。假设后端用 "ma_golden_cross"
            short_ma_period = int(params.get("short_ma_period", 5))
            long_ma_period = int(params.get("long_ma_period", 20))
            
            # 新增：获取成交量过滤参数 (来自您之前的请求，但在此处确认已包含)
            enable_volume_filter = params.get("enable_volume_filter", False) 
            volume_avg_days = int(params.get("volume_avg_days", 5))
            volume_multiple = float(params.get("volume_multiple", 1.5))

            if short_ma_period >= long_ma_period: # 修正：应为 >=，因为短周期不能等于或大于长周期
                logger.error(f"  MA Golden Cross: Short MA period ({short_ma_period}) must be less than Long MA period ({long_ma_period}).")
                return [], latest_data_date_across_all_tickers 

            required_data_len = long_ma_period + 1 
            end_date_dt = datetime.now()
            start_date_dt = end_date_dt - timedelta(days=required_data_len + 60) 
            end_date_str = end_date_dt.strftime('%Y%m%d')
            start_date_str = start_date_dt.strftime('%Y%m%d')

            for ts_code in target_tickers:
                logger.debug(f"  Processing ticker: {ts_code} for MA Golden Cross (short: {short_ma_period}, long: {long_ma_period}, vol_filter: {enable_volume_filter}). Dates: {start_date_str}-{end_date_str}")

                daily_df = self.ts_client.get_daily_data(ts_code=ts_code, start_date=start_date_str, end_date=end_date_str, adj='qfq')

                if daily_df is None or daily_df.empty or len(daily_df) < required_data_len:
                    logger.warning(f"    Skipping {ts_code}: Not enough data for MA calculation (need {required_data_len}, got {len(daily_df) if daily_df is not None else 0}).")
                    continue
                
                current_ticker_latest_date_str = daily_df.index[-1].strftime('%Y-%m-%d')
                if latest_data_date_across_all_tickers is None or current_ticker_latest_date_str > latest_data_date_across_all_tickers:
                    latest_data_date_across_all_tickers = current_ticker_latest_date_str

                close_prices = daily_df['close'].to_numpy()
                volumes = daily_df['vol'].to_numpy() # 获取成交量数据

                short_ma_values = talib.SMA(close_prices, timeperiod=short_ma_period)
                long_ma_values = talib.SMA(close_prices, timeperiod=long_ma_period)

                if len(short_ma_values) < 2 or len(long_ma_values) < 2 or \
                   pd.isna(short_ma_values[-1]) or pd.isna(short_ma_values[-2]) or \
                   pd.isna(long_ma_values[-1]) or pd.isna(long_ma_values[-2]):
                    logger.warning(f"    Skipping {ts_code}: Not enough valid MA values for comparison.")
                    continue

                current_short_ma = short_ma_values[-1]
                prev_short_ma = short_ma_values[-2]
                current_long_ma = long_ma_values[-1]
                prev_long_ma = long_ma_values[-2]

                trigger_date_dt_obj = daily_df.index[-1]
                trigger_price_val = daily_df['close'].iloc[-1]
                current_volume = volumes[-1]
                
                logger.info(f"    {ts_code}: Date: {trigger_date_dt_obj.strftime('%Y-%m-%d')}, Price: {trigger_price_val:.2f}")
                logger.info(f"      SMA({short_ma_period}): Current={current_short_ma:.2f}, Prev={prev_short_ma:.2f}")
                logger.info(f"      SMA({long_ma_period}): Current={current_long_ma:.2f}, Prev={prev_long_ma:.2f}")


                stock_name, stock_industry = self._get_stock_name_and_industry(ts_code)
                signal_generated_for_this_stock = False

                # 判断金叉条件
                if prev_short_ma < prev_long_ma and current_short_ma >= current_long_ma:
                    logger.info(f"    {ts_code}: Potential Golden Cross on {trigger_date_dt_obj.strftime('%Y-%m-%d')}.")
                    
                    volume_check_passed = True 
                    volume_filter_notes = ""

                    if enable_volume_filter:
                        logger.debug(f"      Volume filter enabled. AvgDays: {volume_avg_days}, Multiple: {volume_multiple}, CurrentVol: {current_volume}")
                        # 需要至少 volume_avg_days + 1 天的数据来计算不包含当日的N日均量
                        if len(volumes) < volume_avg_days + 1: 
                            logger.warning(f"      Not enough volume data to calculate {volume_avg_days}-day average volume (need {volume_avg_days+1}, got {len(volumes)}).")
                            # volume_check_passed = False # 如果严格要求，可以设为False
                            volume_filter_notes = f" (量能数据不足)"
                        else:
                            # 计算过去N日的平均成交量 (不包括当日，所以用 volumes[:-1])
                            avg_volume_n_days_values = talib.SMA(volumes[:-1], timeperiod=volume_avg_days)
                            if pd.isna(avg_volume_n_days_values[-1]): #检查计算出的均量是否有效
                                logger.warning(f"      Could not calculate {volume_avg_days}-day average volume (SMA result is NaN).")
                                # volume_check_passed = False
                                volume_filter_notes = f" (均量计算NaN)"
                            else:
                                avg_volume_n_days = avg_volume_n_days_values[-1]
                                volume_threshold = avg_volume_n_days * volume_multiple
                                logger.debug(f"      Avg Vol ({volume_avg_days}d): {avg_volume_n_days:.0f}, Required Vol: > {volume_threshold:.0f}")
                                if current_volume > volume_threshold:
                                    logger.info(f"      Volume check PASSED. Current Vol: {current_volume:.0f} > Threshold: {volume_threshold:.0f}")
                                    volume_filter_notes = f" (量能确认)"
                                else:
                                    logger.info(f"      Volume check FAILED. Current Vol: {current_volume:.0f} <= Threshold: {volume_threshold:.0f}")
                                    volume_check_passed = False
                                    volume_filter_notes = f" (量能未达标)"
                    
                    if volume_check_passed:
                        signals.append(TimingSignalItem(
                            ts_code=ts_code,
                            name=stock_name,
                            signal_type="MA_GOLDEN_CROSS",
                            trigger_date=trigger_date_dt_obj.strftime('%Y-%m-%d'),
                            trigger_price=round(float(trigger_price_val), 2) if pd.notna(trigger_price_val) else None,
                            signal_strength=0.7, 
                            indicator_values={
                                f"short_ma({short_ma_period})": round(current_short_ma, 2),
                                f"long_ma({long_ma_period})": round(current_long_ma, 2),
                                "volume": int(current_volume) if pd.notna(current_volume) else None,
                                "filter_active": enable_volume_filter, # 传递成交量过滤是否激活的状态
                            },
                            notes=f"SMA({short_ma_period})上穿SMA({long_ma_period}).{volume_filter_notes} 行业：{stock_industry or 'N/A'}"
                        ))
                        signal_generated_for_this_stock = True
                        logger.info(f"      Signal: MA_GOLDEN_CROSS for {ts_code}{' with volume confirmation' if enable_volume_filter and volume_check_passed else ''}")
                    elif enable_volume_filter: # 如果启用了过滤但未通过
                         logger.info(f"    {ts_code}: Golden Cross signal filtered out due to volume condition.")
                
                # 判断死叉条件
                elif not signal_generated_for_this_stock and prev_short_ma > prev_long_ma and current_short_ma <= current_long_ma:
                    # 死叉通常不关注成交量放大，但可以按需添加
                    logger.info(f"    {ts_code}: Death Cross on {trigger_date_dt_obj.strftime('%Y-%m-%d')}.")
                    signals.append(TimingSignalItem(
                        ts_code=ts_code,
                        name=stock_name,
                        signal_type="MA_DEATH_CROSS",
                        trigger_date=trigger_date_dt_obj.strftime('%Y-%m-%d'),
                        trigger_price=round(float(trigger_price_val), 2) if pd.notna(trigger_price_val) else None,
                        signal_strength=0.3, # 死叉信号强度可以低一些
                        indicator_values={
                            f"short_ma({short_ma_period})": round(current_short_ma, 2),
                            f"long_ma({long_ma_period})": round(current_long_ma, 2),
                        },
                        notes=f"SMA({short_ma_period})下穿SMA({long_ma_period}). 行业：{stock_industry or 'N/A'}"
                    ))
                    logger.info(f"      Signal: MA_DEATH_CROSS for {ts_code}")

            return signals, latest_data_date_across_all_tickers
        else:
            logger.error(f"Unknown timing strategy_id: {strategy_id}")
            raise ValueError(f"Unknown timing strategy_id: {strategy_id}")

# --- END OF Relevant part of backend/app/services/timing_service.py ---