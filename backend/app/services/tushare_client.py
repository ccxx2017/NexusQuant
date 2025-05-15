# --- START OF FILE backend/app/services/tushare_client.py ---
import tushare as ts
from functools import lru_cache
from app.core.config import settings
from typing import Optional, List, Tuple # <--- 导入 Tuple
import pandas as pd
from datetime import datetime, timedelta 

class TushareClient:
    def __init__(self, token: Optional[str] = None):
        self.token = token or settings.TUSHARE_TOKEN
        if not self.token:
            print("Warning: Tushare token is not set. Some functionalities might be limited.")
            self.pro = None
        else:
            ts.set_token(self.token)
            self.pro = ts.pro_api()
            print("Tushare Pro API initialized.")

    @lru_cache(maxsize=128)
    def get_stock_basic(self, list_status: str = 'L', fields: str = 'ts_code,symbol,name,area,industry,list_date,is_hs') -> Optional[pd.DataFrame]:
        if not self.pro: return None
        try:
            df = self.pro.stock_basic(list_status=list_status, fields=fields)
            return df
        except Exception as e:
            print(f"Error fetching stock_basic from Tushare: {e}")
            return None

    @lru_cache(maxsize=10)
    def get_daily_basic_for_date(self, trade_date: Optional[str] = None, ts_codes_tuple: Optional[Tuple[str, ...]] = None) -> Optional[pd.DataFrame]: # <--- 参数名改为 ts_codes_tuple，类型改为 Tuple
        """
        获取指定交易日的每日基本指标数据。
        trade_date: YYYYMMDD 格式，如果为 None，则获取最新交易日数据。
        ts_codes_tuple: 股票代码元组，如果为 None，则获取全市场。
        """
        if not self.pro: return None
        
        # 将元组转换回列表以进行Tushare API调用
        ts_codes_list: Optional[List[str]] = list(ts_codes_tuple) if ts_codes_tuple else None

        try:
            fields = 'ts_code,trade_date,close,turnover_rate,turnover_rate_f,volume_ratio,pe,pe_ttm,pb,ps,ps_ttm,dv_ratio,dv_ttm,total_share,float_share,free_share,total_mv,circ_mv'
            
            # 使用转换后的 ts_codes_list
            if ts_codes_list and isinstance(ts_codes_list, list):
                all_data = []
                batch_size = 100
                for i in range(0, len(ts_codes_list), batch_size):
                    batch_codes = ts_codes_list[i:i + batch_size]
                    df_batch = self.pro.daily_basic(ts_code=','.join(batch_codes), trade_date=trade_date, fields=fields)
                    if df_batch is not None and not df_batch.empty:
                        all_data.append(df_batch)
                if not all_data:
                    return None
                return pd.concat(all_data, ignore_index=True)
            else: # 获取全市场
                # 注意：即使 ts_codes_list 为 None，Tushare API 的 ts_code 参数也期望是字符串
                # 如果是 None，ts.pro.daily_basic 的 ts_code 参数会使用默认值（全市场）
                # 如果我们想明确传递空字符串给 Tushare 以获取全市场，可以这样做：
                # ts_code_param = ','.join(ts_codes_list) if ts_codes_list else ''
                # 或者让 Tushare 客户端库处理 None
                return self.pro.daily_basic(ts_code=','.join(ts_codes_list) if ts_codes_list else None, trade_date=trade_date, fields=fields)

        except Exception as e:
            print(f"Error fetching daily_basic from Tushare for date {trade_date}: {e}")
            return None

    def get_daily_data(self, ts_code: str, start_date: str, end_date: str,adj: str = 'qfq') -> Optional[pd.DataFrame]:
        if not self.pro: return None
        try:
            df = ts.pro_bar(ts_code=ts_code, adj=adj, start_date=start_date, end_date=end_date)
            if df is not None and not df.empty:
                if 'trade_date' in df.columns:
                    df['trade_date'] = pd.to_datetime(df['trade_date']) # 转换为 datetime 对象
                    df = df.set_index('trade_date').sort_index()
                return df
            return None
        except Exception as e:
            print(f"Error fetching daily data for {ts_code} from {start_date} to {end_date}: {e}")
            return None

    @lru_cache(maxsize=50) # 缓存财务数据
    def get_financial_indicator(self, ts_code: str, period: Optional[str] = None, fields: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        获取单只股票的财务指标数据。
        ts_code: 股票代码
        period: 报告期，例如 '20231231' (年报), '20230930' (三季报)。如果为 None，获取最新。
                Tushare 的 fina_indicator 似乎不直接支持 period=None 来获取最新，
                通常是获取指定代码的所有报告期数据，然后筛选。
                为简化，这里我们先获取所有报告期数据，然后在 service 层筛选最新一期。
                或者，指定一个较近的 start_date。
        fields: 需要的字段，例如 'ts_code,ann_date,end_date,roe_yearly,q_roe,roe_waa'
        """
        if not self.pro: return None
        try:
            # 为了获取最新的ROE，我们可能需要获取最近几期的财报
            # 这里简化为获取该股票所有可用的财务指标，然后在 service 层处理
            # 如果只想获取最新的，可能需要先查最新公告日期，再用 end_date 过滤
            # 更好的方式是获取 `fina_indicator` 并按 `end_date` 排序取最新
            
            # Tushare 的 fina_indicator 接口通常返回某个股票的所有历史财报数据
            # 我们可以获取所有，然后在 service 层取最新的一期
            # 接口默认按 end_date 降序返回，第一条通常是较新的 (但不一定是最新公告的)
            # 需要的字段：roe_yearly（年化ROE）, roe_waa（加权平均ROE）, q_roe（单季度ROE）等
            # 这里的 fields 可以根据需要调整
            default_fields = 'ts_code,ann_date,end_date,roe,roe_yearly,roe_waa,q_roe,pb' # 同时获取pb
            df = self.pro.fina_indicator(ts_code=ts_code, fields=fields or default_fields)
            if df is not None and not df.empty:
                df = df.sort_values(by='end_date', ascending=False) # 按报告期倒序
            return df
        except Exception as e:
            print(f"Error fetching financial_indicator for {ts_code}: {e}")
            return None
ts_client = TushareClient()
# --- END OF FILE backend/app/services/tushare_client.py ---