"""均值回归策略"""
from typing import List, Dict, Any
import pandas as pd
from strategies.base import Strategy, Signal, Direction, SignalType


class RSIReversalStrategy(Strategy):
    """RSI 均值回归策略
    
    规则:
    - RSI < 30: 超卖，买入
    - RSI > 70: 超卖，卖出
    """
    
    def __init__(self, window: int = 14, oversold: float = 30, overbought: float = 70):
        self.window = window
        self.oversold = oversold
        self.overbought = overbought
    
    @property
    def name(self) -> str:
        return f"rsi_reversal_{self.window}"
    
    @property
    def description(self) -> str:
        return f"RSI均值回归策略 (超卖<{self.oversold}, 超买>{self.overbought})"
    
    def generate_signals(
        self, 
        prices: pd.DataFrame,
        factors: pd.DataFrame = None
    ) -> List[Signal]:
        signals = []
        
        if factors is None or factors.empty:
            return signals
        
        rsi_col = f'rsi{self.window}'
        if rsi_col not in factors.columns:
            return signals
        
        rsi_values = factors[rsi_col].values
        close_prices = prices['close'].values
        trade_dates = factors['trade_date'].values if 'trade_date' in factors.columns else range(len(prices))
        ts_code = prices['ts_code'].iloc[0] if 'ts_code' in prices.columns else 'UNKNOWN'
        
        for i in range(self.window, len(rsi_values)):
            if pd.isna(rsi_values[i]):
                continue
            
            # 超卖 -> 买入
            if rsi_values[i] < self.oversold:
                strength = (self.oversold - rsi_values[i]) / self.oversold
                signals.append(Signal(
                    ts_code=ts_code,
                    trade_date=str(trade_dates[i]),
                    direction=Direction.LONG,
                    signal_type=SignalType.BUY,
                    strength=strength,
                    price=float(close_prices[i]),
                    reason=f"RSI oversold ({rsi_values[i]:.1f})"
                ))
            
            # 超买 -> 卖出
            elif rsi_values[i] > self.overbought:
                strength = (rsi_values[i] - self.overbought) / (100 - self.overbought)
                signals.append(Signal(
                    ts_code=ts_code,
                    trade_date=str(trade_dates[i]),
                    direction=Direction.FLAT,
                    signal_type=SignalType.SELL,
                    strength=strength,
                    price=float(close_prices[i]),
                    reason=f"RSI overbought ({rsi_values[i]:.1f})"
                ))
        
        return signals


class BollingerReversalStrategy(Strategy):
    """布林带均值回归策略
    
    规则:
    - 价格触及下轨: 超卖，买入
    - 价格触及上轨: 超买，卖出
    """
    
    def __init__(self, window: int = 20, num_std: float = 2.0):
        self.window = window
        self.num_std = num_std
    
    @property
    def name(self) -> str:
        return f"bb_reversal_{self.window}"
    
    @property
    def description(self) -> str:
        return f"布林带均值回归策略 (N={self.window}, K={self.num_std})"
    
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
            close = prices['close'].iloc[i]
            curr_lower = lower.iloc[i]
            curr_upper = upper.iloc[i]
            
            # 触及下轨 -> 买入
            if close <= curr_lower:
                signals.append(Signal(
                    ts_code=ts_code,
                    trade_date=str(trade_dates[i]),
                    direction=Direction.LONG,
                    signal_type=SignalType.BUY,
                    strength=1.0,
                    price=float(close),
                    reason="Price at lower band"
                ))
            
            # 触及上轨 -> 卖出
            elif close >= curr_upper:
                signals.append(Signal(
                    ts_code=ts_code,
                    trade_date=str(trade_dates[i]),
                    direction=Direction.FLAT,
                    signal_type=SignalType.SELL,
                    strength=1.0,
                    price=float(close),
                    reason="Price at upper band"
                ))
        
        return signals


class MeanReversionStrategy(Strategy):
    """Z-Score 均值回归策略
    
    规则:
    - Z-Score < -2: 超卖，买入
    - Z-Score > 2: 超买，卖出
    """
    
    def __init__(self, window: int = 20, threshold: float = 2.0):
        self.window = window
        self.threshold = threshold
    
    @property
    def name(self) -> str:
        return f"mean_reversion_{self.window}"
    
    @property
    def description(self) -> str:
        return f"Z-Score均值回归策略 (N={self.window}, 阈值={self.threshold})"
    
    def generate_signals(
        self, 
        prices: pd.DataFrame,
        factors: pd.DataFrame = None
    ) -> List[Signal]:
        signals = []
        
        if factors is None or factors.empty:
            return signals
        
        zscore_col = f'zscore{self.window}'
        if zscore_col not in factors.columns:
            return signals
        
        zscore_values = factors[zscore_col].values
        close_prices = prices['close'].values
        trade_dates = factors['trade_date'].values if 'trade_date' in factors.columns else range(len(prices))
        ts_code = prices['ts_code'].iloc[0] if 'ts_code' in prices.columns else 'UNKNOWN'
        
        for i in range(self.window, len(zscore_values)):
            if pd.isna(zscore_values[i]):
                continue
            
            # Z-Score < -threshold -> 买入
            if zscore_values[i] < -self.threshold:
                strength = min(1.0, abs(zscore_values[i]) / self.threshold)
                signals.append(Signal(
                    ts_code=ts_code,
                    trade_date=str(trade_dates[i]),
                    direction=Direction.LONG,
                    signal_type=SignalType.BUY,
                    strength=strength,
                    price=float(close_prices[i]),
                    reason=f"Z-Score oversold ({zscore_values[i]:.2f})"
                ))
            
            # Z-Score > threshold -> 卖出
            elif zscore_values[i] > self.threshold:
                strength = min(1.0, abs(zscore_values[i]) / self.threshold)
                signals.append(Signal(
                    ts_code=ts_code,
                    trade_date=str(trade_dates[i]),
                    direction=Direction.FLAT,
                    signal_type=SignalType.SELL,
                    strength=strength,
                    price=float(close_prices[i]),
                    reason=f"Z-Score overbought ({zscore_values[i]:.2f})"
                ))
        
        return signals
