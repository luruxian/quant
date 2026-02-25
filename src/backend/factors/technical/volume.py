"""价量因子"""
import pandas as pd
from typing import List
from factors.base import Factor


class OBV(Factor):
    """OBV 能量潮
    
    累计成交量
    """
    
    @property
    def name(self) -> str:
        return "obv"
    
    @property
    def description(self) -> str:
        return "能量潮"
    
    def compute(self, data: pd.DataFrame) -> pd.DataFrame:
        if not all(col in data.columns for col in ['close', 'volume']):
            raise ValueError("数据缺少 close, volume 列")
        
        result = pd.DataFrame(index=data.index)
        result['trade_date'] = data.get('trade_date', data.index)
        
        # Calculate OBV
        close_diff = data['close'].diff()
        
        obv = pd.Series(index=data.index, dtype=float)
        obv.iloc[0] = data['volume'].iloc[0]
        
        for i in range(1, len(data)):
            if close_diff.iloc[i] > 0:
                obv.iloc[i] = obv.iloc[i-1] + data['volume'].iloc[i]
            elif close_diff.iloc[i] < 0:
                obv.iloc[i] = obv.iloc[i-1] - data['volume'].iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        result['obv'] = obv
        
        # OBV change rate
        result['obv_change'] = obv.pct_change()
        
        return result


class VWAP(Factor):
    """VWAP 成交量加权平均价
    
    VWAP = Sum(Price * Volume) / Sum(Volume)
    """
    
    @property
    def name(self) -> str:
        return "vwap"
    
    @property
    def description(self) -> str:
        return "成交量加权平均价"
    
    def compute(self, data: pd.DataFrame) -> pd.DataFrame:
        if not all(col in data.columns for col in ['high', 'low', 'close', 'volume']):
            raise ValueError("数据缺少 high, low, close, volume 列")
        
        result = pd.DataFrame(index=data.index)
        result['trade_date'] = data.get('trade_date', data.index)
        
        # Typical Price
        tp = (data['high'] + data['low'] + data['close']) / 3
        
        # VWAP
        result['vwap'] = (tp * data['volume']).cumsum() / data['volume'].cumsum()
        
        return result


class VolumeRatio(Factor):
    """量比因子
    
    量比 = 当日每分钟平均成交量 / 过去5日每分钟平均成交量
    """
    
    def __init__(self, window: int = 5):
        self.window = window
    
    @property
    def name(self) -> str:
        return "volume_ratio"
    
    @property
    def description(self) -> str:
        return "量比"
    
    def compute(self, data: pd.DataFrame) -> pd.DataFrame:
        if not all(col in data.columns for col in ['volume']):
            raise ValueError("数据缺少 volume 列")
        
        result = pd.DataFrame(index=data.index)
        result['trade_date'] = data.get('trade_date', data.index)
        
        # 5日平均成交量
        avg_volume = data['volume'].rolling(window=self.window * 5).mean()
        
        # 量比
        result['volume_ratio'] = data['volume'] / avg_volume
        
        return result


class TurnoverRate(Factor):
    """换手率因子"""
    
    @property
    def name(self) -> str:
        return "turnover"
    
    @property
    def description(self) -> str:
        return "换手率"
    
    def compute(self, data: pd.DataFrame) -> pd.DataFrame:
        if not all(col in data.columns for col in ['volume']):
            raise ValueError("数据缺少 volume 列")
        
        result = pd.DataFrame(index=data.index)
        result['trade_date'] = data.get('trade_date', data.index)
        
        # 换手率 (假设流通股本 = 收盘价 * 成交量 / 1000，简化的计算方式)
        # 实际应该从 stock_info 获取流通股本
        if 'amount' in data.columns:
            result['turnover_rate'] = (data['amount'] / 1e8)  # 简化估算
        else:
            result['turnover_rate'] = data['volume'].pct_change()
        
        # 5日平均换手率
        result['turnover_ma5'] = result['turnover_rate'].rolling(window=5).mean()
        
        return result
