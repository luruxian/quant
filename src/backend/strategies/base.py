"""策略基类"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any
import pandas as pd


class Direction(Enum):
    """交易方向"""
    LONG = "long"
    SHORT = "short"
    FLAT = "flat"


class SignalType(Enum):
    """信号类型"""
    BUY = "buy"
    SELL = "sell"
    CLOSE = "close"


@dataclass
class Signal:
    """交易信号"""
    ts_code: str
    trade_date: str
    direction: Direction
    signal_type: SignalType
    strength: float  # 0-1 信号强度
    price: float     # 信号价格
    reason: str      # 信号原因
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'ts_code': self.ts_code,
            'trade_date': self.trade_date,
            'direction': self.direction.value,
            'signal_type': self.signal_type.value,
            'strength': self.strength,
            'price': self.price,
            'reason': self.reason
        }


class Strategy(ABC):
    """策略基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """策略名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """策略描述"""
        pass
    
    @property
    def params(self) -> Dict[str, Any]:
        """策略参数"""
        return {}
    
    @abstractmethod
    def generate_signals(
        self, 
        prices: pd.DataFrame,
        factors: pd.DataFrame = None
    ) -> List[Signal]:
        """生成信号
        
        Args:
            prices: 价格数据 (OHLCV)
            factors: 因子数据 (可选)
            
        Returns:
            Signal列表
        """
        pass
    
    def validate_data(self, prices: pd.DataFrame) -> bool:
        """验证输入数据"""
        required = ['ts_code', 'trade_date', 'close']
        return all(col in prices.columns for col in required)
