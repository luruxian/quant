"""
Backtrader 策略基类 - 所有回测策略必须继承此类
"""
import backtrader as bt


class BaseStrategy(bt.Strategy):
    """
    Backtrader 策略基类
    
    提供通用的日志、订单管理、交易通知功能
    """
    
    # 策略参数 (子类可覆盖)
    params = (
        ('name', 'base_strategy'),
        ('printlog', False),
        ('stake', 1000),  # 每次交易股数
    )
    
    def __init__(self):
        """初始化策略"""
        self.dataclose = self.datas[0].close
        self.dataopen = self.datas[0].open
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        self.datavol = self.datas[0].volume
        
        self.order = None       # 当前订单
        self.buyprice = None    # 买入价格
        self.buycomm = None     # 买入手续费
        
        # 信号记录 (用于返回给前端)
        self.signals = []
        
    def notify_order(self, order):
        """
        订单状态变化时调用
        
        Args:
            order: Backtrader Order 对象
        """
        if order.status in [order.Submitted, order.Accepted]:
            return
        
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    f'BUY EXECUTED, Price: {order.executed.price:.2f}, '
                    f'Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}'
                )
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log(
                    f'SELL EXECUTED, Price: {order.executed.price:.2f}, '
                    f'Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}'
                )
            
            self.bar_executed = len(self)
            
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
        
        self.order = None
        
    def notify_trade(self, trade):
        """
        交易完成时调用
        
        Args:
            trade: Backtrader Trade 对象
        """
        if not trade.isclosed:
            return
        
        self.log(f'TRADE PROFIT, Gross: {trade.pnl:.2f}, Net: {trade.pnlcomm:.2f}')
        
    def notify_signal(self, signal_type: str, price: float, reason: str):
        """
        记录交易信号
        
        Args:
            signal_type: 'buy' 或 'sell'
            price: 信号价格
            reason: 信号原因
        """
        dt = self.datas[0].datetime.date(0)
        self.signals.append({
            'date': dt.strftime('%Y-%m-%d'),
            'type': signal_type,
            'price': price,
            'reason': reason,
        })
        
    def log(self, txt, dt=None):
        """
        日志记录
        
        Args:
            txt: 日志内容
            dt: 日期 (可选)
        """
        if self.params.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} {txt}')
            
    def _buy(self, size=None, price=None):
        """
        买入封装
        
        Args:
            size: 股数 (默认使用 params.stake)
            price: 限价 (默认市价单)
        """
        if self.order:
            return
            
        size = size or self.params.stake
        if price:
            self.order = bt.Strategy.buy(self, size=size, price=price, exectype=bt.Order.Limit)
        else:
            self.order = bt.Strategy.buy(self, size=size)
            
    def _sell(self, size=None, price=None):
        """
        卖出封装
        
        Args:
            size: 股数 (默认全部平仓)
            price: 限价 (默认市价单)
        """
        if self.order:
            return
            
        size = size or self.getposition().size
        if size > 0:
            if price:
                self.order = bt.Strategy.sell(self, size=size, price=price, exectype=bt.Order.Limit)
            else:
                self.order = bt.Strategy.sell(self, size=size)
