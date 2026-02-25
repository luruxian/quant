"""动量因子"""
import pandas as pd
from typing import List
from factors.base import Factor


class MACD(Factor):
    """MACD 因子
    
    Moving Average Convergence Divergence
    - DIF = EMA12 - EMA26
    - DEA = EMA9
    - MACD = 2 * (DIF - DEA)
    """
    
    @property
    def name(self) -> str:
        return "macd"
    
    @property
    def description(self) -> str:
        return "MACD 异同移动平均线"
    
    def compute(self, data: pd.DataFrame) -> pd.DataFrame:
        if not self.validate_data(data):
            raise ValueError("数据缺少 close 列")
        
        result = pd.DataFrame(index=data.index)
        result['trade_date'] = data.get('trade_date', data.index)
        
        # 计算EMA
        ema12 = data['close'].ewm(span=12, adjust=False).mean()
        ema26 = data['close'].ewm(span=26, adjust=False).mean()
        
        # DIF (MACD Line)
        result['dif'] = ema12 - ema26
        
        # DEA (Signal Line)
        result['dea'] = result['dif'].ewm(span=9, adjust=False).mean()
        
        # MACD Histogram
        result['macd'] = 2 * (result['dif'] - result['dea'])
        
        return result


class RSI(Factor):
    """RSI 相对强弱指标
    
    RSI = 100 - 100/(1 + RS)
    RS = n日内上涨幅度均值 / n日内下跌幅度均值
    """
    
    def __init__(self, windows: List[int] = None):
        self.windows = windows or [6, 12, 24]
    
    @property
    def name(self) -> str:
        return "rsi"
    
    @property
    def description(self) -> str:
        return "相对强弱指标"
    
    def compute(self, data: pd.DataFrame) -> pd.DataFrame:
        if not self.validate_data(data):
            raise ValueError("数据缺少 close 列")
        
        result = pd.DataFrame(index=data.index)
        result['trade_date'] = data.get('trade_date', data.index)
        
        delta = data['close'].diff()
        
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        for window in self.windows:
            col_name = f'rsi{window}'
            
            avg_gain = gain.rolling(window=window).mean()
            avg_loss = loss.rolling(window=window).mean()
            
            rs = avg_gain / avg_loss
            result[col_name] = 100 - (100 / (1 + rs))
        
        return result


class CCI(Factor):
    """CCI 商品通道指数
    
    CCI = (TP - MA) / (0.015 * MD)
    TP = (High + Low + Close) / 3
    """
    
    def __init__(self, window: int = 14):
        self.window = window
    
    @property
    def name(self) -> str:
        return "cci"
    
    @property
    def description(self) -> str:
        return "商品通道指数"
    
    def compute(self, data: pd.DataFrame) -> pd.DataFrame:
        if not all(col in data.columns for col in ['high', 'low', 'close']):
            raise ValueError("数据缺少 high, low, close 列")
        
        result = pd.DataFrame(index=data.index)
        result['trade_date'] = data.get('trade_date', data.index)
        
        # Typical Price
        tp = (data['high'] + data['low'] + data['close']) / 3
        
        # Simple Moving Average of TP
        sma = tp.rolling(window=self.window).mean()
        
        # Mean Deviation
        md = tp.rolling(window=self.window).apply(
            lambda x: abs(x - x.mean()).mean(), raw=True
        )
        
        # CCI
        result['cci'] = (tp - sma) / (0.015 * md)
        
        return result
