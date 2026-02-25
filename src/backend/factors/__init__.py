"""因子注册表"""
from typing import Dict, Type
from factors.base import Factor
from factors.technical import (
    MovingAverage, MACD, RSI, CCI, 
    BollingerBands, ATR, StandardDeviation,
    OBV, VWAP, VolumeRatio, TurnoverRate
)
from factors.statistical import ZScore, Correlation, Skewness, Kurtosis


# 因子注册表
FACTOR_REGISTRY: Dict[str, Factor] = {
    # 技术因子
    'ma': MovingAverage(windows=[5, 10, 20, 30, 60, 120, 250]),
    'ema': MovingAverage(windows=[12, 26]),
    'macd': MACD(),
    'rsi': RSI(windows=[6, 12, 24]),
    'cci': CCI(window=14),
    'bb': BollingerBands(window=20, num_std=2.0),
    'atr': ATR(window=14),
    'std': StandardDeviation(windows=[5, 10, 20, 60]),
    'obv': OBV(),
    'vwap': VWAP(),
    'volume_ratio': VolumeRatio(window=5),
    'turnover': TurnoverRate(),
    
    # 统计因子
    'zscore': ZScore(windows=[20, 60]),
    'correlation': Correlation(target='volume', windows=[20, 60]),
    'skewness': Skewness(windows=[20, 60]),
    'kurtosis': Kurtosis(windows=[20, 60]),
}


def get_factor(name: str) -> Factor:
    """获取因子实例"""
    if name not in FACTOR_REGISTRY:
        raise ValueError(f"未知因子: {name}")
    return FACTOR_REGISTRY[name]


def list_factors() -> Dict[str, str]:
    """列出所有因子"""
    return {name: factor.description for name, factor in FACTOR_REGISTRY.items()}


__all__ = ['FACTOR_REGISTRY', 'get_factor', 'list_factors']
