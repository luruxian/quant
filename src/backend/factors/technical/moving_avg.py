"""移动平均因子"""
import pandas as pd
from typing import List
from factors.base import Factor


class MovingAverage(Factor):
    """移动平均因子 (MA)
    
    计算收盘价的简单移动平均
    """
    
    def __init__(self, windows: List[int] = None):
        self.windows = windows or [5, 10, 20, 30, 60, 120, 250]
    
    @property
    def name(self) -> str:
        return "ma"
    
    @property
    def description(self) -> str:
        return "移动平均线"
    
    def compute(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算MA
        
        Args:
            data: DataFrame with 'close' column
            
        Returns:
            DataFrame with columns: ma5, ma10, ma20, ma30, ma60, ma120, ma250
        """
        if not self.validate_data(data):
            raise ValueError("数据缺少 close 列")
        
        result = pd.DataFrame(index=data.index)
        result['trade_date'] = data.get('trade_date', data.index)
        
        for window in self.windows:
            col_name = f'ma{window}'
            result[col_name] = data['close'].rolling(window=window).mean()
        
        return result
    
    def compute_ema(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算EMA (指数移动平均)"""
        if not self.validate_data(data):
            raise ValueError("数据缺少 close 列")
        
        result = pd.DataFrame(index=data.index)
        result['trade_date'] = data.get('trade_date', data.index)
        
        for window in self.windows:
            col_name = f'ema{window}'
            result[col_name] = data['close'].ewm(span=window, adjust=False).mean()
        
        return result


class ExponentialMovingAverage(Factor):
    """指数移动平均因子 (EMA)"""
    
    def __init__(self, windows: List[int] = None):
        self.windows = windows or [12, 26]
    
    @property
    def name(self) -> str:
        return "ema"
    
    @property
    def description(self) -> str:
        return "指数移动平均"
    
    def compute(self, data: pd.DataFrame) -> pd.DataFrame:
        if not self.validate_data(data):
            raise ValueError("数据缺少 close 列")
        
        result = pd.DataFrame(index=data.index)
        result['trade_date'] = data.get('trade_date', data.index)
        
        for window in self.windows:
            col_name = f'ema{window}'
            result[col_name] = data['close'].ewm(span=window, adjust=False).mean()
        
        return result
