"""波动率因子"""
import pandas as pd
from typing import List
from factors.base import Factor


class BollingerBands(Factor):
    """布林带因子
    
    中轨 = MA(n)
    上轨 = MA(n) + 2 * STD
    下轨 = MA(n) - 2 * STD
    """
    
    def __init__(self, window: int = 20, num_std: float = 2.0):
        self.window = window
        self.num_std = num_std
    
    @property
    def name(self) -> str:
        return "bb"
    
    @property
    def description(self) -> str:
        return "布林带"
    
    def compute(self, data: pd.DataFrame) -> pd.DataFrame:
        if not self.validate_data(data):
            raise ValueError("数据缺少 close 列")
        
        result = pd.DataFrame(index=data.index)
        result['trade_date'] = data.get('trade_date', data.index)
        
        # Middle Band (MA)
        result[f'bb_mid{self.window}'] = data['close'].rolling(window=self.window).mean()
        
        # Standard Deviation
        std = data['close'].rolling(window=self.window).std()
        
        # Upper Band
        result[f'bb_upper{self.window}'] = result[f'bb_mid{self.window}'] + (self.num_std * std)
        
        # Lower Band
        result[f'bb_lower{self.window}'] = result[f'bb_mid{self.window}'] - (self.num_std * std)
        
        # %B = (Price - Lower) / (Upper - Lower)
        result[f'bb_pct{self.window}'] = (data['close'] - result[f'bb_lower{self.window}']) / \
                                         (result[f'bb_upper{self.window}'] - result[f'bb_lower{self.window}'])
        
        # Bandwidth
        result[f'bb_width{self.window}'] = (result[f'bb_upper{self.window}'] - result[f'bb_lower{self.window}']) / \
                                            result[f'bb_mid{self.window}']
        
        return result


class ATR(Factor):
    """ATR 平均真实波幅
    
    True Range = max(High-Low, |High-PrevClose|, |Low-PrevClose|)
    ATR = TR 的 n 日简单移动平均
    """
    
    def __init__(self, window: int = 14):
        self.window = window
    
    @property
    def name(self) -> str:
        return "atr"
    
    @property
    def description(self) -> str:
        return "平均真实波幅"
    
    def compute(self, data: pd.DataFrame) -> pd.DataFrame:
        if not all(col in data.columns for col in ['high', 'low', 'close']):
            raise ValueError("数据缺少 high, low, close 列")
        
        result = pd.DataFrame(index=data.index)
        result['trade_date'] = data.get('trade_date', data.index)
        
        # True Range
        high_low = data['high'] - data['low']
        high_close = abs(data['high'] - data['close'].shift(1))
        low_close = abs(data['low'] - data['close'].shift(1))
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        
        # ATR
        result[f'atr{self.window}'] = tr.rolling(window=self.window).mean()
        
        # ATR as percentage of close
        result[f'atr_pct{self.window}'] = result[f'atr{self.window}'] / data['close'] * 100
        
        return result


class StandardDeviation(Factor):
    """标准差因子"""
    
    def __init__(self, windows: List[int] = None):
        self.windows = windows or [5, 10, 20, 60]
    
    @property
    def name(self) -> str:
        return "std"
    
    @property
    def description(self) -> str:
        return "历史波动率 (标准差)"
    
    def compute(self, data: pd.DataFrame) -> pd.DataFrame:
        if not self.validate_data(data):
            raise ValueError("数据缺少 close 列")
        
        result = pd.DataFrame(index=data.index)
        result['trade_date'] = data.get('trade_date', data.index)
        
        for window in self.windows:
            col_name = f'std{window}'
            result[col_name] = data['close'].rolling(window=window).std()
        
        return result
