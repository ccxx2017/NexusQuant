# --- START OF FILE backend/app/services/strategy_service.py ---
from typing import List, Dict, Any, Optional, Tuple
from app.services.tushare_client import ts_client
from app.models.strategy import SelectedPoolItem
import pandas as pd
import asyncio
from datetime import datetime, timedelta

class StrategyService:
    def __init__(self):
        self.ts_client = ts_client

    async def _calculate_momentum(self, ts_code: str, window_months: int) -> Optional[float]:
        # ... (此函数保持不变，与上一轮提供的一致) ...
        end_date_dt = datetime.now()
        start_date_dt_approx = end_date_dt - timedelta(days=int(window_months * 30.44 + 45))
        end_date_str = end_date_dt.strftime('%Y%m%d')
        start_date_str_for_api = start_date_dt_approx.strftime('%Y%m%d')
        daily_df = self.ts_client.get_daily_data(ts_code=ts_code, start_date=start_date_str_for_api, end_date=end_date_str, adj='qfq')
        if daily_df is None or daily_df.empty:
            print(f"      Debug ({ts_code}): No daily data found for momentum calculation in range {start_date_str_for_api}-{end_date_str}.")
            return None
        if len(daily_df) < 2:
             print(f"      Debug ({ts_code}): Not enough data points ({len(daily_df)}) for momentum calculation.")
             return None
        target_trading_days_back = int(window_months * 21) 
        if len(daily_df) <= target_trading_days_back:
            start_price_row = daily_df.iloc[0]
            start_price_date = start_price_row.name
            start_price = start_price_row['close']
            # print(f"      Debug ({ts_code}): Data points ({len(daily_df)}) less than target lookback ({target_trading_days_back}). Using earliest price.") # 日志已存在类似信息
        else:
            start_price_row = daily_df.iloc[-(target_trading_days_back + 1)]
            start_price_date = start_price_row.name
            start_price = start_price_row['close']
        end_price_row = daily_df.iloc[-1]
        end_price_date = end_price_row.name
        end_price = end_price_row['close']
        print(f"      Debug ({ts_code}): Momentum calc: StartPrice ({start_price_date.strftime('%Y-%m-%d')}): {start_price:.2f}, EndPrice ({end_price_date.strftime('%Y-%m-%d')}): {end_price:.2f}")
        if pd.isna(start_price) or pd.isna(end_price) or start_price == 0:
            print(f"      Debug ({ts_code}): Invalid start/end price for momentum (start: {start_price}, end: {end_price}).")
            return None
        momentum = (end_price - start_price) / start_price
        print(f"      Debug ({ts_code}): Calculated momentum: {momentum:.4f}")
        return momentum

    async def _get_latest_roe_and_pb(self, ts_code: str) -> Tuple[Optional[float], Optional[float]]:
        # ... (此函数保持不变，与上一轮提供的一致) ...
        fina_df = self.ts_client.get_financial_indicator(ts_code=ts_code, fields='ts_code,end_date,roe,roe_yearly,roe_waa,pb')
        if fina_df is None or fina_df.empty:
            # print(f"    Debug ({ts_code}): No financial data found.") # 日志移到调用处
            return None, None
        latest_fina = fina_df.iloc[0]
        roe_value = latest_fina.get('roe_yearly') 
        if pd.isna(roe_value): roe_value = latest_fina.get('roe_waa')
        if pd.isna(roe_value): roe_value = latest_fina.get('roe')
        pb_value = latest_fina.get('pb')
        processed_roe = pd.to_numeric(roe_value, errors='coerce') / 100.0 if pd.notna(roe_value) else None
        processed_pb = pd.to_numeric(pb_value, errors='coerce') if pd.notna(pb_value) else None
        return processed_roe, processed_pb

    def _calculate_composite_score(self, roe: Optional[float], pb: Optional[float], momentum: Optional[float], 
                                   min_momentum_ratio: float, max_pb_value_param: float) -> int:
        """
        计算动量质量策略的综合得分。
        roe, pb, momentum 应该是已经处理过的小数值。
        min_momentum_ratio 是用户设定的最小动量阈值（小数）。
        max_pb_value_param 是用户设定的最大PB值。
        """
        score = 0
        
        # ROE Score (max 40)
        if roe is not None and not pd.isna(roe):
            if roe >= 0.20: score += 40
            elif roe >= 0.15: score += 30
            elif roe >= 0.10: score += 20
        
        # PB Score (max 30, lower is better)
        if pb is not None and not pd.isna(pb) and pb > 0: # PB必须大于0
            if pb <= 1.0: score += 30
            elif pb <= 1.5: score += 20
            elif pb <= 2.0: score += 10
            elif pb <= max_pb_value_param: score += 5 # 确保通过筛选的至少有分
            
        # Momentum Score (max 30, higher is better, based on 6m momentum)
        if momentum is not None and not pd.isna(momentum):
            if momentum >= 0.20: score += 30
            elif momentum >= 0.10: score += 20
            elif momentum >= min_momentum_ratio: score += 10 # 确保通过筛选的至少有分
            
        return score

    async def generate_pool_for_selection(self, strategy_id: str, params: Dict[str, Any]) -> List[SelectedPoolItem]:
        print(f"StrategyService: Generating pool for strategy_id='{strategy_id}' with params={params}")

        if strategy_id == "value_momentum":
            print("StrategyService: Executing value_momentum strategy.")
            momentum_window_months = params.get("momentum_window_months", 6)
            min_momentum_percent = params.get("min_momentum_percent", 5.0)
            roe_threshold_percent = params.get("roe_threshold_percent", 15.0)
            max_pb_value = params.get("max_pb_value", 2.5)

            min_momentum_ratio = min_momentum_percent / 100.0
            roe_threshold_ratio = roe_threshold_percent / 100.0

            stock_list_df = self.ts_client.get_stock_basic(list_status='L', fields='ts_code,name,industry')
            if stock_list_df is None or stock_list_df.empty:
                print("StrategyService: Failed to fetch stock basic list for value_momentum.")
                return []

            sample_stocks_df = stock_list_df.head(50) # 样本数量
            print(f"StrategyService (value_momentum): Processing a sample of {len(sample_stocks_df)} stocks...")
            
            sample_ts_codes_list = sample_stocks_df['ts_code'].tolist()
            sample_ts_codes_tuple = tuple(sample_ts_codes_list) if sample_ts_codes_list else None
            daily_basic_df = self.ts_client.get_daily_basic_for_date(ts_codes_tuple=sample_ts_codes_tuple)
            
            if daily_basic_df is not None and not daily_basic_df.empty:
                if 'trade_date' in daily_basic_df.columns:
                    daily_basic_df = daily_basic_df.sort_values('trade_date').groupby('ts_code').tail(1)
                stocks_with_pb_df = pd.merge(sample_stocks_df[['ts_code', 'name']],
                                             daily_basic_df[['ts_code', 'pb']],
                                             on='ts_code',
                                             how='left')
                stocks_with_pb_df['pb'] = pd.to_numeric(stocks_with_pb_df['pb'], errors='coerce')
            else: # 如果 daily_basic 返回空，则所有PB为NA
                print(f"Warning: daily_basic returned no data for PB calculation for sample stocks. All PBs will be NA.")
                stocks_with_pb_df = sample_stocks_df[['ts_code', 'name']].copy()
                stocks_with_pb_df['pb'] = pd.NA 

            results: List[SelectedPoolItem] = []

            for _, stock_row in stocks_with_pb_df.iterrows():
                ts_code = stock_row['ts_code']
                name = stock_row['name']
                pb_from_daily_basic = stock_row['pb'] 
                
                print(f"  Processing {ts_code} - {name} (PB_daily: {pb_from_daily_basic})...")

                roe, pb_from_fina = await self._get_latest_roe_and_pb(ts_code)
                
                final_pb = pb_from_daily_basic
                if pd.isna(final_pb) and pd.notna(pb_from_fina):
                    final_pb = pb_from_fina
                    print(f"    {ts_code}: Using PB_fina: {final_pb}")
                
                print(f"    {ts_code}: Final_PB={final_pb}, ROE={roe}")

                if pd.isna(final_pb) or not (final_pb > 0 and final_pb <= max_pb_value):
                    print(f"    Skipping {ts_code}: PB not met (PB: {final_pb} vs max: {max_pb_value}).")
                    continue
                print(f"    {ts_code}: PB met.")

                if roe is None or pd.isna(roe) or not (roe >= roe_threshold_ratio):
                    print(f"    Skipping {ts_code}: ROE not met (ROE: {roe} vs threshold: {roe_threshold_ratio}).")
                    continue
                print(f"    {ts_code}: ROE met.")

                momentum = await self._calculate_momentum(ts_code, momentum_window_months)

                if momentum is None or pd.isna(momentum) or not (momentum >= min_momentum_ratio):
                    print(f"    Skipping {ts_code}: Momentum not met (Momentum: {momentum} vs threshold: {min_momentum_ratio}).")
                    continue
                print(f"    {ts_code}: Momentum met.")
                
                # 计算综合得分
                composite_score = self._calculate_composite_score(roe, final_pb, momentum, 
                                                                min_momentum_ratio, max_pb_value)
                print(f"    {ts_code}: Composite Score = {composite_score}")

                results.append(SelectedPoolItem(
                    ts_code=ts_code,
                    name=name,
                    roe=round(roe, 4) if pd.notna(roe) else None,
                    pb=round(final_pb, 4) if pd.notna(final_pb) else None,
                    momentum_6m=round(momentum, 4) if momentum_window_months == 6 and pd.notna(momentum) else None,
                    composite_score=composite_score # 添加综合得分
                ))
                # if len(results) >= 5: # 可以暂时去掉这个限制，看看能选出多少
                #     break
            
            # 按综合得分降序排列
            results.sort(key=lambda item: item.composite_score if item.composite_score is not None else -1, reverse=True)
            
            # 取前N名，例如前10名
            final_results = results[:10]

            print(f"StrategyService (value_momentum): Found {len(final_results)} stocks after scoring and ranking.")
            return final_results

        elif strategy_id == "simple_value_screen":
            # ... (simple_value_screen 逻辑保持不变，与上一轮提供的一致) ...
            # (省略)
            print("StrategyService: Executing simple_value_screen strategy.")
            max_pe_ttm = params.get("max_pe_ttm", 30.0)
            max_pb_value_sv = params.get("max_pb", 2.0)
            min_dividend_yield_percent = params.get("min_dividend_yield", 2.0)
            min_total_mv_billions = params.get("min_total_mv_billions", 50.0)
            min_dividend_yield_ratio = min_dividend_yield_percent / 100.0
            min_total_mv = min_total_mv_billions * 10000
            stock_list_df_sv = self.ts_client.get_stock_basic(list_status='L', fields='ts_code,name,industry,list_date')
            if stock_list_df_sv is None or stock_list_df_sv.empty:
                print("StrategyService: Failed to fetch stock basic list for simple_value_screen.")
                return []
            sample_ts_codes_list_sv = stock_list_df_sv['ts_code'].tolist()[:200]
            print(f"StrategyService (simple_value_screen): Fetching daily basic for a sample of {len(sample_ts_codes_list_sv)} stocks...")
            sample_ts_codes_tuple_sv = tuple(sample_ts_codes_list_sv) if sample_ts_codes_list_sv else None
            daily_basic_df_sv = self.ts_client.get_daily_basic_for_date(ts_codes_tuple=sample_ts_codes_tuple_sv)
            if daily_basic_df_sv is None or daily_basic_df_sv.empty:
                print("StrategyService: Failed to fetch daily basic data for simple_value_screen.")
                return []
            if 'trade_date' in daily_basic_df_sv.columns:
                 daily_basic_df_sv = daily_basic_df_sv.sort_values('trade_date').groupby('ts_code').tail(1)
            merged_df = pd.merge(stock_list_df_sv[['ts_code', 'name', 'industry']], 
                                 daily_basic_df_sv[['ts_code', 'pe_ttm', 'pb', 'dv_ratio', 'total_mv']], 
                                 on='ts_code', how='inner')
            if merged_df.empty:
                print("StrategyService: No data after merging stock_list and daily_basic for simple_value_screen.")
                return []
            merged_df['pe_ttm'] = pd.to_numeric(merged_df['pe_ttm'], errors='coerce')
            merged_df['pb'] = pd.to_numeric(merged_df['pb'], errors='coerce')
            merged_df['dv_ratio_actual'] = pd.to_numeric(merged_df['dv_ratio'], errors='coerce') / 100.0
            merged_df['total_mv_actual'] = pd.to_numeric(merged_df['total_mv'], errors='coerce')
            print(f"StrategyService (simple_value_screen): Applying filters - max_pe_ttm={max_pe_ttm}, max_pb={max_pb_value_sv}, min_dividend_yield_ratio={min_dividend_yield_ratio}, min_total_mv={min_total_mv} (万元)")
            filtered_df = merged_df[
                (merged_df['pe_ttm'] > 0) & (merged_df['pe_ttm'] <= max_pe_ttm) &
                (merged_df['pb'] > 0) & (merged_df['pb'] <= max_pb_value_sv) &
                (merged_df['dv_ratio_actual'] >= min_dividend_yield_ratio) &
                (merged_df['total_mv_actual'] >= min_total_mv)
            ]
            print(f"StrategyService (simple_value_screen): Found {len(filtered_df)} stocks after filtering.")
            results_sv = []
            for _, row in filtered_df.iterrows():
                results_sv.append(SelectedPoolItem(
                    ts_code=row['ts_code'], name=row['name'], pe_ttm=row['pe_ttm'], pb=row['pb'],
                    dividend_yield_ratio=row['dv_ratio_actual'], total_mv=row['total_mv_actual'] / 10000,
                ))
            return results_sv

        else:
            raise ValueError(f"Unknown selection strategy_id: {strategy_id}")
# --- END OF FILE backend/app/services/strategy_service.py ---