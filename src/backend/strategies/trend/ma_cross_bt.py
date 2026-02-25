"""
均线交叉策略 - Backtrader 版本

规则:
- 金叉 (买入): 快线从下穿过慢线
- 死叉 (卖出): 快线从上穿过慢线

参数:
- ma_fast: 快线周期 (默认 5)
- ma_slow: 慢线周期 (默认 10)
"""
import backtrader as bt
from strategies.backtrader_base import BaseStrategy


class MaCrossStrategy(BaseStrategy):
    """均线交叉策略"""
    
    params = (
        ('ma_fast', 5),
        ('ma_slow', 10),
        ('stake', 1000),
    )
    
    def __init__(self):
        super().__init__()
        
        # 添加均线指标
        self.ma_fast = bt.indicators.SimpleMovingAverage(
            self.dataclose, 
            period=self.params.ma_fast,
            plotname=f'MA{self.params.ma_fast}'
        )
        self.ma_slow = bt.indicators.SimpleMovingAverage(
            self.dataclose, 
            period=self.params.ma_slow,
            plotname=f'MA{self.params.ma_slow}'
        )
        
        # 交叉信号
        self.crossover = bt.indicators.CrossOver(self.ma_fast, self.ma_slow)
        
    def next(self):
        """每个 bar 调用 - 核心策略逻辑"""
        if self.order:
            return  # 等待订单完成
        
        # 金叉：快线上穿慢线 → 买入
        if self.crossover > 0:
            self.log(f'BUY SIGNAL - MA{self.params.ma_fast} crosses above MA{self.params.ma_slow}')
            self.notify_signal('buy', self.dataclose[0], 
                             f'MA{self.params.ma_fast} crosses above MA{self.params.ma_slow}')
            
            if not self.position:  # 无仓位时买入
                self._buy(size=self.params.stake)
        
        # 死叉：快线下穿慢线 → 卖出平仓
        elif self.crossover < 0:
            self.log(f'SELL SIGNAL - MA{self.params.ma_fast} crosses below MA{self.params.ma_slow}')
            self.notify_signal('sell', self.dataclose[0],
                             f'MA{self.params.ma_fast} crosses below MA{self.params.ma_slow}')
            
            if self.position:  # 有仓位时卖出
                self._sell()


class DualMaCrossStrategy(BaseStrategy):
    """
    双均线交叉策略 - 多周期确认
    
    使用 MA5/MA10 确认短期趋势，MA20/MA60 确认长期趋势
    """
    
    params = (
        ('short_fast', 5),
        ('short_slow', 10),
        ('long_fast', 20),
        ('long_slow', 60),
        ('stake', 1000),
    )
    
    def __init__(self):
        super().__init__()
        
        # 短期均线
        self.short_ma_fast = bt.indicators.SMA(
            self.dataclose, period=self.params.short_fast,
            plotname=f'MA{self.params.short_fast}'
        )
        self.short_ma_slow = bt.indicators.SMA(
            self.dataclose, period=self.params.short_slow,
            plotname=f'MA{self.params.short_slow}'
        )
        
        # 长期均线
        self.long_ma_fast = bt.indicators.SMA(
            self.dataclose, period=self.params.long_fast,
            plotname=f'MA{self.params.long_fast}'
        )
        self.long_ma_slow = bt.indicators.SMA(
            self.dataclose, period=self.params.long_slow,
            plotname=f'MA{self.params.long_slow}'
        )
        
        # 交叉信号
        self.short_cross = bt.indicators.CrossOver(self.short_ma_fast, self.short_ma_slow)
        self.long_cross = bt.indicators.CrossOver(self.long_ma_fast, self.long_ma_slow)
        
    def next(self):
        if self.order:
            return
        
        # 短期金叉 且 长期均线向上
        if self.short_cross > 0 and self.long_ma_fast[0] > self.long_ma_slow[0]:
            self.log('BUY SIGNAL - Short-term golden cross + long-term uptrend')
            self.notify_signal('buy', self.dataclose[0],
                             'Short-term golden cross + long-term uptrend')
            
            if not self.position:
                self._buy(size=self.params.stake)
        
        # 短期死叉 且 长期均线向下
        elif self.short_cross < 0 and self.long_ma_fast[0] < self.long_ma_slow[0]:
            self.log('SELL SIGNAL - Short-term death cross + long-term downtrend')
            self.notify_signal('sell', self.dataclose[0],
                             'Short-term death cross + long-term downtrend')
            
            if self.position:
                self._sell()
