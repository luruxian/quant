"""均线交叉策略"""
from typing import List, Dict, Any
import pandas as pd
from strategies.base import Strategy, Signal, Direction, SignalType


class MACrossStrategy(Strategy):
    """均线交叉策略
    
    规则:
    - 金叉 (买入): 快线从下穿过慢线
    - 死叉 (卖出): 快线从上穿过慢线
    
    参数:
    - fast: 快线周期 (默认5)
    - slow: 慢线周期 (默认20)
    """
    
    def __init__(self, fast: int = 5, slow: int = 20):
        self._fast = fast
        self._slow = slow
    
    @property
    def name(self) -> str:
        return f"ma_cross_{self._fast}_{self._slow}"
    
    @property
    def description(self) -> str:
        return f"均线交叉策略 (MA{self._fast} vs MA{self._slow})"
    
    @property
    def params(self) -> Dict[str, Any]:
        return {
            'fast': self._fast,
            'slow': self._slow
        }
    
    def generate_signals(
        self, 
        prices: pd.DataFrame,
        factors: pd.DataFrame = None
    ) -> List[Signal]:
        signals = []
        
        if factors is None or factors.empty:
            return signals
        
        # 获取MA列名
        fast_col = f'ma{self._fast}'
        slow_col = f'ma{self._slow}'
        
        if fast_col not in factors.columns or slow_col not in factors.columns:
            return signals
        
        # 获取数据
        ma_fast = factors[fast_col].values
        ma_slow = factors[slow_col].values
        close_prices = prices['close'].values
        trade_dates = factors['trade_date'].values if 'trade_date' in factors.columns else range(len(prices))
        ts_code = prices['ts_code'].iloc[0] if 'ts_code' in prices.columns else 'UNKNOWN'
        
        # 交叉检测
        for i in range(1, len(ma_fast)):
            if pd.isna(ma_fast[i]) or pd.isna(ma_slow[i]):
                continue
            
            # 金叉: 快线从下穿过慢线
            if ma_fast[i-1] <= ma_slow[i-1] and ma_fast[i] > ma_slow[i]:
                signals.append(Signal(
                    ts_code=ts_code,
                    trade_date=str(trade_dates[i]),
                    direction=Direction.LONG,
                    signal_type=SignalType.BUY,
                    strength=1.0,
                    price=float(close_prices[i]),
                    reason=f"MA{self._fast} crosses above MA{self._slow}"
                ))
            
            # 死叉: 快线从上穿过慢线
            elif ma_fast[i-1] >= ma_slow[i-1] and ma_fast[i] < ma_slow[i]:
                signals.append(Signal(
                    ts_code=ts_code,
                    trade_date=str(trade_dates[i]),
                    direction=Direction.FLAT,
                    signal_type=SignalType.SELL,
                    strength=1.0,
                    price=float(close_prices[i]),
                    reason=f"MA{self._fast} crosses below MA{self._slow}"
                ))
        
        return signals


class DualMACrossStrategy(Strategy):
    """双均线交叉策略 (多周期确认)
    
    使用MA5/MA10确认短期趋势，MA20/MA60确认长期趋势
    """
    
    def __init__(self, short_fast: int = 5, short_slow: int = 10, 
                 long_fast: int = 20, long_slow: int = 60):
        self.short_fast = short_fast
        self.short_slow = short_slow
        self.long_fast = long_fast
        self.long_slow = long_slow
    
    @property
    def name(self) -> str:
        return "dual_ma_cross"
    
    @property
    def description(self) -> str:
        return "双周期均线交叉策略"
    
    def generate_signals(
        self, 
        prices: pd.DataFrame,
        factors: pd.DataFrame = None
    ) -> List[Signal]:
        signals = []
        
        if factors is None or factors.empty:
            return signals
        
        # 获取MA列
        ma_cols = [f'ma{i}' for i in [self.short_fast, self.short_slow, 
                                       self.long_fast, self.long_slow]]
        
        if not all(col in factors.columns for col in ma_cols):
            return signals
        
        # 短期均线交叉
        ma1_fast = factors[f'ma{self.short_fast}'].values
        ma1_slow = factors[f'ma{self.short_slow}'].values
        
        # 长期均线交叉
        ma2_fast = factors[f'ma{self.long_fast}'].values
        ma2_slow = factors[f'ma{self.long_slow}'].values
        
        close_prices = prices['close'].values
        trade_dates = factors['trade_date'].values if 'trade_date' in factors.columns else range(len(prices))
        ts_code = prices['ts_code'].iloc[0] if 'ts_code' in prices.columns else 'UNKNOWN'
        
        for i in range(1, len(ma1_fast)):
            if any(pd.isna(x) for x in [ma1_fast[i], ma1_slow[i], ma2_fast[i], ma2_slow[i]]):
                continue
            
            # 短期金叉 且 长期向上
            if (ma1_fast[i-1] <= ma1_slow[i-1] and ma1_fast[i] > ma1_slow[i] and
                ma2_fast[i] > ma2_slow[i]):
                signals.append(Signal(
                    ts_code=ts_code,
                    trade_date=str(trade_dates[i]),
                    direction=Direction.LONG,
                    signal_type=SignalType.BUY,
                    strength=0.8,
                    price=float(close_prices[i]),
                    reason="Short-term golden cross + long-term uptrend"
                ))
            
            # 短期死叉 且 长期向下
            elif (ma1_fast[i-1] >= ma1_slow[i-1] and ma1_fast[i] < ma1_slow[i] and
                  ma2_fast[i] < ma2_slow[i]):
                signals.append(Signal(
                    ts_code=ts_code,
                    trade_date=str(trade_dates[i]),
                    direction=Direction.FLAT,
                    signal_type=SignalType.SELL,
                    strength=0.8,
                    price=float(close_prices[i]),
                    reason="Short-term death cross + long-term downtrend"
                ))
        
        return signals
