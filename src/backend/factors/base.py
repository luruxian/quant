"""因子基类"""
from abc import ABC, abstractmethod
from typing import Any
import pandas as pd


class Factor(ABC):
    """因子基类 - 所有因子的父类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """因子名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """因子描述"""
        pass
    
    @abstractmethod
    def compute(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算因子
        
        Args:
            data: 包含 OHLCV 的 DataFrame
            
        Returns:
            因子计算结果 DataFrame
        """
        pass
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """验证输入数据"""
        required_cols = ['close']
        return all(col in data.columns for col in required_cols)
