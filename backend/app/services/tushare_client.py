import tushare as ts
from functools import lru_cache
from app.core.config import settings
from typing import Optional

class TushareClient:
    def __init__(self, token: Optional[str] = None):
        self.token = token or settings.TUSHARE_TOKEN
        if not self.token:
            raise ValueError("Tushare token is not set.")
        ts.set_token(self.token)
        self.pro = ts.pro_api()
        print("Tushare Pro API initialized.")

    @lru_cache(maxsize=128) # 简单的缓存示例
    def get_stock_basic(self, list_status: str = 'L', fields: str = 'ts_code,symbol,name,area,industry,list_date'):
        try:
            return self.pro.stock_basic(list_status=list_status, fields=fields)
        except Exception as e:
            print(f"Error fetching stock_basic from Tushare: {e}")
            return None

    # ... 其他Tushare接口的封装方法 ...
    # 例如: get_daily, get_fina_indicator, etc.

    def get_daily_data(self, ts_code: str, start_date: str, end_date: str):
        try:
            # 注意：Tushare pro_bar 接口可能更常用
            df = ts.pro_bar(ts_code=ts_code, adj='qfq', start_date=start_date, end_date=end_date)
            # df = self.pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
            return df
        except Exception as e:
            print(f"Error fetching daily data for {ts_code}: {e}")
            return None


ts_client = TushareClient()

# 示例用法 (可以在其他服务或API端点中调用)
# if __name__ == "__main__":
#     client = TushareClient()
#     stock_list = client.get_stock_basic()
#     if stock_list is not None:
#         print(stock_list.head())