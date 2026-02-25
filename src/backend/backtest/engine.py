"""
回测引擎 - 封装 Backtrader Cerebro
"""
import backtrader as bt
from datetime import datetime
from .data_feed import PostgresData
from .analyzers.performance import PerformanceAnalyzer, DrawDownAnalyzer


class BacktestEngine:
    """
    回测引擎封装类
    
    提供简化的 API 来执行回测：
    1. 配置参数 (资金、手续费、滑点)
    2. 添加股票数据
    3. 添加策略
    4. 运行回测
    5. 获取结果
    """
    
    def __init__(
        self,
        initial_cash: float = 1000000,
        commission: float = 0.0003,
        slippage: float = 0.002,
        stake: int = 1000
    ):
        """
        初始化回测引擎
        
        Args:
            initial_cash: 初始资金 (默认 100 万)
            commission: 手续费率 (默认万分之三)
            slippage: 滑点比例 (默认 0.2%)
            stake: 每次交易股数 (默认 1000 股)
        """
        self.cerebro = bt.Cerebro()
        self.cerebro.broker.setcash(initial_cash)
        self.cerebro.broker.setcommission(commission=commission)
        # Backtrader 滑点配置
        self.cerebro.broker.set_slippage_perc(slippage)
        
        self.stake = stake
        self.ts_code = None
        self.start_date = None
        self.end_date = None
        
        # 添加分析器
        self.cerebro.addanalyzer(PerformanceAnalyzer, _name='performance')
        self.cerebro.addanalyzer(DrawDownAnalyzer, _name='drawdown')
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', riskfreerate=0.02)
        self.cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        
    def add_data(self, ts_code: str, start_date: str, end_date: str):
        """
        添加股票数据
        
        Args:
            ts_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
        """
        data = PostgresData.from_db(ts_code, start_date, end_date)
        self.cerebro.adddata(data)
        self.ts_code = ts_code
        self.start_date = start_date
        self.end_date = end_date
        
    def add_strategy(self, strategy_cls, **params):
        """
        添加策略
        
        Args:
            strategy_cls: 策略类 (继承自 bt.Strategy)
            **params: 策略参数
        """
        self.cerebro.addstrategy(strategy_cls, **params)
        
    def run(self) -> dict:
        """
        执行回测并返回结果
        
        Returns:
            包含回测结果的字典
        """
        initial_cash = self.cerebro.broker.startingcash
        
        # 运行回测
        results = self.cerebro.run()
        strat = results[0]
        
        # 收集结果
        final_value = self.cerebro.broker.getvalue()
        total_return = (final_value - initial_cash) / initial_cash
        
        # 获取分析器结果
        perf = strat.analyzers.performance.get_analysis()
        drawdown = strat.analyzers.drawdown.get_analysis()
        sharpe = strat.analyzers.sharpe.get_analysis()
        returns = strat.analyzers.returns.get_analysis()
        trade_analysis = strat.analyzers.trades.get_analysis()
        
        # 提取交易记录
        trades = self._extract_trades(trade_analysis)
        
        # 提取资金曲线
        equity_curve = self._extract_equity_curve()
        
        # 计算年化收益 (假设 252 个交易日)
        n_days = len(equity_curve)
        annual_return = (1 + total_return) ** (252 / max(n_days, 1)) - 1 if n_days > 0 else 0
        
        return {
            'config': {
                'ts_code': self.ts_code,
                'start_date': self.start_date,
                'end_date': self.end_date,
                'initial_cash': initial_cash,
            },
            'metrics': {
                'total_return': total_return,
                'annual_return': annual_return,
                'final_value': final_value,
                'sharpe_ratio': sharpe.get('sharperatio', None),
                'max_drawdown': drawdown['max_drawdown'],
                'max_drawdown_money': drawdown['max_drawdown_money'],
                'total_trades': perf['total_trades'],
                'winning_trades': perf['winning_trades'],
                'losing_trades': perf['losing_trades'],
                'win_rate': perf['win_rate'],
                'profit_factor': perf['profit_factor'],
                'avg_win': perf['avg_win'],
                'avg_loss': perf['avg_loss'],
                'avg_holding_days': perf['avg_holding_days'],
            },
            'equity_curve': equity_curve,
            'drawdown_curve': drawdown['drawdown_curve'],
            'trades': trades,
        }
        
    def _extract_trades(self, trade_analysis) -> list:
        """
        从 TradeAnalyzer 提取交易记录
        
        Args:
            trade_analysis: TradeAnalyzer 的分析结果
        
        Returns:
            交易记录列表
        """
        trades = []
        
        # TradeAnalyzer 返回的是嵌套字典，需要遍历
        if 'long' in trade_analysis:
            for trade_id, trade_data in trade_analysis['long'].items():
                if isinstance(trade_data, dict) and 'open' in trade_data:
                    open_dt = trade_data['open']['datetime']
                    close_dt = trade_data['close']['datetime'] if 'close' in trade_data else None
                    
                    trades.append({
                        'trade_id': trade_id,
                        'entry_date': open_dt.strftime('%Y-%m-%d') if hasattr(open_dt, 'strftime') else str(open_dt),
                        'exit_date': close_dt.strftime('%Y-%m-%d') if close_dt and hasattr(close_dt, 'strftime') else None,
                        'direction': 'long',
                        'entry_price': trade_data['open']['price'],
                        'exit_price': trade_data['close']['price'] if 'close' in trade_data else None,
                        'size': trade_data['size'],
                        'pnl': trade_data['pnl'],
                        'return': trade_data['pnl'] / (trade_data['open']['price'] * trade_data['size']) if trade_data['size'] > 0 else 0,
                        'exit_reason': 'strategy_signal',
                    })
        
        if 'short' in trade_analysis:
            for trade_id, trade_data in trade_analysis['short'].items():
                if isinstance(trade_data, dict) and 'open' in trade_data:
                    open_dt = trade_data['open']['datetime']
                    close_dt = trade_data['close']['datetime'] if 'close' in trade_data else None
                    
                    trades.append({
                        'trade_id': trade_id,
                        'entry_date': open_dt.strftime('%Y-%m-%d') if hasattr(open_dt, 'strftime') else str(open_dt),
                        'exit_date': close_dt.strftime('%Y-%m-%d') if close_dt and hasattr(close_dt, 'strftime') else None,
                        'direction': 'short',
                        'entry_price': trade_data['open']['price'],
                        'exit_price': trade_data['close']['price'] if 'close' in trade_data else None,
                        'size': trade_data['size'],
                        'pnl': trade_data['pnl'],
                        'return': trade_data['pnl'] / (trade_data['open']['price'] * trade_data['size']) if trade_data['size'] > 0 else 0,
                        'exit_reason': 'strategy_signal',
                    })
        
        return trades
        
    def _extract_equity_curve(self) -> list:
        """
        提取资金曲线
        
        Returns:
            资金曲线数据列表
        """
        equity = []
        
        # 简单方法：从 broker 获取最终值是不够的
        # 需要在回测过程中记录，这里简化为返回起始和结束值
        initial = self.cerebro.broker.startingcash
        final = self.cerebro.broker.getvalue()
        
        # 返回简单的时间序列（起始点和结束点）
        # 完整的资金曲线需要添加观察器，后续优化
        equity.append({
            'date': self.start_date,
            'value': initial,
        })
        equity.append({
            'date': self.end_date,
            'value': final,
        })
        
        return equity
