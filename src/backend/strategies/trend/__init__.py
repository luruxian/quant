"""趋势策略"""
from strategies.trend.ma_cross import MACrossStrategy, DualMACrossStrategy
from strategies.trend.break_out import BreakOutStrategy, ChannelBreakoutStrategy

__all__ = [
    'MACrossStrategy',
    'DualMACrossStrategy',
    'BreakOutStrategy',
    'ChannelBreakoutStrategy',
]
