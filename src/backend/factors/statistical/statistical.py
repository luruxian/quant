"""统计因子"""
import pandas as pd
import numpy as np
from typing import List
from factors.base import Factor


class ZScore(Factor):
    """Z-Score 标准化因子
    
    Z = (X - mean) / std
    """
    
    def __init__(self, windows: List[int] = None):
        self.windows = windows or [20, 60]
    
    @property
    def name(self) -> str:
        return "zscore"
    
    @property
    def description(self) -> str:
        return "Z-Score 标准化"
    
    def compute(self, data: pd.DataFrame) -> pd.DataFrame:
        if not self.validate_data(data):
            raise ValueError("数据缺少 close 列")
        
        result = pd.DataFrame(index=data.index)
        result['trade_date'] = data.get('trade_date', data.index)
        
        for window in self.windows:
            col_name = f'zscore{window}'
            
            mean = data['close'].rolling(window=window).mean()
            std = data['close'].rolling(window=window).std()
            
            result[col_name] = (data['close'] - mean) / std
        
        return result


class Correlation(Factor):
    """相关系数因子
    
    计算价格与成交量、价格与指数的相关系数
    """
    
    def __init__(self, target: str = 'volume', windows: List[int] = None):
        self.target = target
        self.windows = windows or [20, 60]
    
    @property
    def name(self) -> str:
        return "correlation"
    
    @property
    def description(self) -> str:
        return f"价格与{self.target}的相关系数"
    
    def compute(self, data: pd.DataFrame) -> pd.DataFrame:
        if not self.validate_data(data):
            raise ValueError("数据缺少 close 列")
        
        if self.target not in data.columns:
            raise ValueError(f"数据缺少 {self.target} 列")
        
        result = pd.DataFrame(index=data.index)
        result['trade_date'] = data.get('trade_date', data.index)
        
        for window in self.windows:
            col_name = f'corr_{self.target}_{window}'
            result[col_name] = data['close'].rolling(window=window).corr(data[self.target])
        
        return result


class Skewness(Factor):
    """偏度因子
    
    衡量数据分布的不对称程度
    """
    
    def __init__(self, windows: List[int] = None):
        self.windows = windows or [20, 60]
    
    @property
    def name(self) -> str:
        return "skewness"
    
    @property
    def description(self) -> str:
        return "收益率偏度"
    
    def compute(self, data: pd.DataFrame) -> pd.DataFrame:
        if not self.validate_data(data):
            raise ValueError("数据缺少 close 列")
        
        result = pd.DataFrame(index=data.index)
        result['trade_date'] = data.get('trade_date', data.index)
        
        # 计算收益率
        returns = data['close'].pct_change()
        
        for window in self.windows:
            col_name = f'skew{window}'
            result[col_name] = returns.rolling(window=window).skew()
        
        return result


class Kurtosis(Factor):
    """峰度因子
    
    衡量数据分布的尾部厚度
    """
    
    def __init__(self, windows: List[int] = None):
        self.windows = windows or [20, 60]
    
    @property
    def name(self) -> str:
        return "kurtosis"
    
    @property
    def description(self) -> str:
        return "收益率峰度"
    
    def compute(self, data: pd.DataFrame) -> pd.DataFrame:
        if not self.validate_data(data):
            raise ValueError("数据缺少 close 列")
        
        result = pd.DataFrame(index=data.index)
        result['trade_date'] = data.get('trade_date', data.index)
        
        # 计算收益率
        returns = data['close'].pct_change()
        
        for window in self.windows:
            col_name = f'kurt{window}'
            result[col_name] = returns.rolling(window=window).kurt()
        
        return result
