import backtrader as bt
import pandas as pd
from datetime import datetime
from app.services.tushare_client import ts_client # 假设已实现
from app.strategies.base_strategy import MyCombinedStrategy # 需要定义这个策略类
from app.models.backtest import BacktestRequest, BacktestResult, EquityCurveDataPoint, PerformanceSummary # Pydantic模型

class BacktestingService:
    async def run_backtest(self, request: BacktestRequest) -> BacktestResult:
        cerebro = bt.Cerebro()

        # 1. 数据准备 (简化示例，实际需要更健壮的数据处理)
        # 假设 request.target_tickers 是一个列表
        all_tickers_to_fetch = request.target_tickers[:]
        if request.backtest_config.benchmark_ticker:
            all_tickers_to_fetch.append(request.backtest_config.benchmark_ticker)

        for ticker in all_tickers_to_fetch:
            # 从Tushare获取数据并转换为Backtrader格式
            df = await self._get_historical_data_for_ticker(
                ticker,
                request.backtest_config.start_date,
                request.backtest_config.end_date
            )
            if df is not None and not df.empty:
                # Backtrader 需要 datetime index 和 ohlcv 列
                df.index = pd.to_datetime(df.index)
                df = df[['open', 'high', 'low', 'close', 'vol']] # Tushare返回的列名可能不同
                df.columns = ['open', 'high', 'low', 'close', 'volume'] # 重命名为Backtrader期望的
                data_feed = bt.feeds.PandasData(dataname=df, name=ticker)
                cerebro.adddata(data_feed)
            else:
                print(f"Warning: No data found for ticker {ticker}")


        # 2. 策略组装与添加
        # MyCombinedStrategy 内部会使用 request.selection_strategy, request.timing_strategy, request.exit_strategy
        # 及其 params 来决定交易逻辑
        cerebro.addstrategy(
            MyCombinedStrategy,
            selection_params=request.selection_strategy.params,
            timing_params=request.timing_strategy.params,
            exit_params=request.exit_strategy.params
            # ... 其他需要传递给策略的参数 ...
        )

        # 3. 资金与手续费
        cerebro.broker.setcash(request.backtest_config.initial_cash)
        cerebro.broker.setcommission(commission=request.backtest_config.commission_bps / 10000.0)

        # 4. 分析器
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', timeframe=bt.TimeFrame.Years)
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trade_analyzer')
        cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='annual_return')
        # 为了获取每日净值，可以在策略的 next() 或 stop() 中记录，或使用 TimeReturn analyzer

        # 5. 运行回测
        print("Running backtest...")
        results = cerebro.run()
        strat = results[0] # 获取第一个策略实例的结果

        # 6. 结果提取
        analyzers = strat.analyzers
        sharpe_ratio = analyzers.sharpe.get_analysis().get('sharperatio', None)
        max_drawdown = analyzers.drawdown.get_analysis().get('max', {}).get('drawdown', None)
        # ... 提取其他分析器结果 ...

        # 提取净值曲线 (这里需要更复杂的处理，例如从TimeReturn分析器或自定义记录中获取)
        # 以下为伪代码，实际需要根据你的实现调整
        equity_curve_strategy = [] # List[EquityCurveDataPoint]
        # for date, value in cerebro.broker.get_value_over_time(): # 这不是Backtrader的标准API，需要自己实现
        #    equity_curve_strategy.append(EquityCurveDataPoint(date=date.isoformat(), value=value))

        # 提取基准曲线 (如果添加了基准数据和分析)
        equity_curve_benchmark = []

        performance = PerformanceSummary(
            total_return=(cerebro.broker.getvalue() / request.backtest_config.initial_cash) - 1,
            annual_return=None, # 从 AnnualReturn 分析器获取
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            # ... 其他指标 ...
        )

        return BacktestResult(
            performance_summary=performance,
            equity_curve={"strategy": equity_curve_strategy, "benchmark": equity_curve_benchmark},
            config_used=request.dict() # 返回本次回测的配置
        )

    async def _get_historical_data_for_ticker(self, ticker: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        # 实际中可能需要将Tushare的异步调用封装得更好
        # 这里简化为直接调用 (Tushare本身是同步的，FastAPI的async是为了IO密集型操作不阻塞主线程)
        df = ts_client.get_daily_data(ts_code=ticker, start_date=start_date.replace("-", ""), end_date=end_date.replace("-", ""))
        if df is not None and not df.empty:
            df = df.set_index('trade_date').sort_index() # 确保日期是索引且升序
            # 可能需要数据清洗和列名转换
            return df
        return None