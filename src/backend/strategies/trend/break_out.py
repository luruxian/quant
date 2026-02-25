"""突破策略"""
from typing import List, Dict, Any
import pandas as pd
from strategies.base import Strategy, Signal, Direction, SignalType


class BreakOutStrategy(Strategy):
    """突破策略
    
    规则:
    - 向上突破: 收盘价突破N日最高价
    - 向下突破: 收盘价跌破N日最低价
    """
    
    def __init__(self, window: int = 20):
        self.window = window
    
    @property
    def name(self) -> str:
        return f"breakout_{self.window}"
    
    @property
    def description(self) -> str:
        return f"N日高低点突破策略 (N={self.window})"
    
    def generate_signals(
        self, 
        prices: pd.DataFrame,
        factors: pd.DataFrame = None
    ) -> List[Signal]:
        signals = []
        
        if not all(col in prices.columns for col in ['high', 'low', 'close']):
            return signals
        
        # 计算N日最高/最低价
        high_n = prices['high'].rolling(window=self.window).max()
        low_n = prices['low'].rolling(window=self.window).min()
        
        trade_dates = prices['trade_date'].values if 'trade_date' in prices.columns else range(len(prices))
        ts_code = prices['ts_code'].iloc[0] if 'ts_code' in prices.columns else 'UNKNOWN'
        
        for i in range(self.window, len(prices)):
            prev_close = prices['close'].iloc[i-1]
            curr_close = prices['close'].iloc[i]
            prev_high = high_n.iloc[i-1]
            curr_high = high_n.iloc[i]
            prev_low = low_n.iloc[i-1]
            curr_low = low_n.iloc[i]
            
            # 向上突破
            if prev_close <= prev_high and curr_close > curr_high:
                signals.append(Signal(
                    ts_code=ts_code,
                    trade_date=str(trade_dates[i]),
                    direction=Direction.LONG,
                    signal_type=SignalType.BUY,
                    strength=1.0,
                    price=float(curr_close),
                    reason=f"Breakout {self.window}-day high"
                ))
            
            # 向下突破
            elif prev_close >= prev_low and curr_close < curr_low:
                signals.append(Signal(
                    ts_code=ts_code,
                    trade_date=str(trade_dates[i]),
                    direction=Direction.FLAT,
                    signal_type=SignalType.SELL,
                    strength=1.0,
                    price=float(curr_close),
                    reason=f"Breakdown {self.window}-day low"
                ))
        
        return signals


class ChannelBreakoutStrategy(Strategy):
    """通道突破策略 (简化版)
    
    基于布林带上下轨突破
    """
    
    def __init__(self, window: int = 20, num_std: float = 2.0):
        self.window = window
        self.num_std = num_std
    
    @property
    def name(self) -> str:
        return "channel_breakout"
    
    @property
    def description(self) -> str:
        return "通道突破策略"
    
    def generate_signals(
        self, 
        prices: pd.DataFrame,
        factors: pd.DataFrame = None
    ) -> List[Signal]:
        signals = []
        
        if not all(col in prices.columns for col in ['close']):
            return signals
        
        # 计算布林带
        ma = prices['close'].rolling(window=self.window).mean()
        std = prices['close'].rolling(window=self.window).std()
        upper = ma + self.num_std * std
        lower = ma - self.num_std * std
        
        trade_dates = prices['trade_date'].values if 'trade_date' in prices.columns else range(len(prices))
        ts_code = prices['ts_code'].iloc[0] if 'ts_code' in prices.columns else 'UNKNOWN'
        
        for i in range(self.window, len(prices)):
            curr_close = prices['close'].iloc[i]
            curr_upper = upper.iloc[i]
            curr_lower = lower.iloc[i]
            
            # 突破上轨
            if curr_close > curr_upper:
                signals.append(Signal(
                    ts_code=ts_code,
                    trade_date=str(trade_dates[i]),
                    direction=Direction.LONG,
                    signal_type=SignalType.BUY,
                    strength=min(1.0, (curr_close - ma.iloc[i]) / (self.num_std * std.iloc[i]) + 1),
                    price=float(curr_close),
                    reason="Breakout upper band"
                ))
            
            # 跌破下轨
            elif curr_close < curr_lower:
                signals.append(Signal(
                    ts_code=ts_code,
                    trade_date=str(trade_dates[i]),
                    direction=Direction.FLAT,
                    signal_type=SignalType.SELL,
                    strength=1.0,
                    price=float(curr_close),
                    reason="Breakdown lower band"
                ))
        
        return signals
