"""策略注册表"""
from typing import Dict, Type
from strategies.base import Strategy
from strategies.trend import (
    MACrossStrategy, DualMACrossStrategy,
    BreakOutStrategy, ChannelBreakoutStrategy
)
from strategies.mean_reversion import (
    RSIReversalStrategy, BollingerReversalStrategy, MeanReversionStrategy
)


# 策略注册表
STRATEGY_REGISTRY: Dict[str, Strategy] = {
    # 趋势策略
    'ma_cross_5_20': MACrossStrategy(fast=5, slow=20),
    'ma_cross_10_60': MACrossStrategy(fast=10, slow=60),
    'ma_cross_5_10': MACrossStrategy(fast=5, slow=10),
    'dual_ma_cross': DualMACrossStrategy(
        short_fast=5, short_slow=10,
        long_fast=20, long_slow=60
    ),
    'breakout_20': BreakOutStrategy(window=20),
    'breakout_60': BreakOutStrategy(window=60),
    'channel_breakout': ChannelBreakoutStrategy(window=20, num_std=2.0),
    
    # 均值回归策略
    'rsi_reversal_14': RSIReversalStrategy(window=14, oversold=30, overbought=70),
    'rsi_reversal_6': RSIReversalStrategy(window=6, oversold=25, overbought=75),
    'bb_reversal_20': BollingerReversalStrategy(window=20, num_std=2.0),
    'mean_reversion_20': MeanReversionStrategy(window=20, threshold=2.0),
}


def get_strategy(name: str) -> Strategy:
    """获取策略实例"""
    if name not in STRATEGY_REGISTRY:
        raise ValueError(f"未知策略: {name}")
    return STRATEGY_REGISTRY[name]


def list_strategies() -> Dict[str, str]:
    """列出所有策略"""
    return {name: strategy.description for name, strategy in STRATEGY_REGISTRY.items()}


__all__ = ['STRATEGY_REGISTRY', 'get_strategy', 'list_strategies']
