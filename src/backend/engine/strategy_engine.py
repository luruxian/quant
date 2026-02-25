"""策略执行引擎"""
import pandas as pd
from typing import List, Dict
from strategies import STRATEGY_REGISTRY, get_strategy
from factors import get_factor
from utils.db import SessionLocal
from sqlalchemy import text


class StrategyEngine:
    """策略执行引擎"""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def run_strategy(
        self, 
        strategy_name: str, 
        ts_code: str,
        start_date: str = None,
        end_date: str = None
    ) -> List[Dict]:
        """运行单个策略生成信号
        
        Args:
            strategy_name: 策略名称
            ts_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            信号列表
        """
        # 获取策略
        strategy = get_strategy(strategy_name)
        
        # 获取价格数据
        prices = self._get_price_data(ts_code, start_date, end_date)
        
        if prices.empty:
            return []
        
        # 优先使用数据库中的因子，如果没有则计算
        factors = self._get_factor_data(ts_code, start_date, end_date)
        
        if not factors.empty:
            # 使用数据库因子
            data = pd.merge(prices, factors, on='trade_date', how='left')
        else:
            data = prices.copy()
            # 计算所需因子
            required_factors = self._get_required_factors(strategy_name)
            
            for factor_name in required_factors:
                try:
                    factor = get_factor(factor_name)
                    factor_result = factor.compute(prices)
                    # 重命名列避免冲突
                    factor_result = factor_result.rename(columns={c: f'{c}_calc' for c in factor_result.columns if c != 'trade_date'})
                    data = pd.merge(data, factor_result, on='trade_date', how='left')
                except Exception as e:
                    print(f"因子 {factor_name} 计算失败: {e}")
        
        # 生成信号
        signals = strategy.generate_signals(data, data)
        
        return [s.to_dict() for s in signals]
    
    def run_all_strategies(
        self, 
        ts_code: str,
        start_date: str = None,
        end_date: str = None
    ) -> Dict[str, List[Dict]]:
        """运行所有策略"""
        
        results = {}
        
        for name in STRATEGY_REGISTRY.keys():
            try:
                signals = self.run_strategy(name, ts_code, start_date, end_date)
                results[name] = signals
            except Exception as e:
                print(f"策略 {name} 执行失败: {e}")
                results[name] = []
        
        return results
    
    def save_signals(self, signals: List[Dict], strategy_name: str):
        """保存信号到数据库"""
        
        for signal in signals:
            self.db.execute(text("""
                INSERT INTO signal (ts_code, trade_date, strategy, direction, signal_type, price, reason)
                VALUES (:ts_code, :trade_date, :strategy, :direction, :signal_type, :price, :reason)
            """), {
                'ts_code': signal['ts_code'],
                'trade_date': signal['trade_date'],
                'strategy': strategy_name,
                'direction': signal['direction'],
                'signal_type': signal['signal_type'],
                'price': signal['price'],
                'reason': signal['reason'],
            })
        
        self.db.commit()
        print(f"✅ 保存 {len(signals)} 条信号")
    
    def _get_price_data(
        self, 
        ts_code: str, 
        start_date: str = None,
        end_date: str = None
    ) -> pd.DataFrame:
        """获取价格数据"""
        
        query = """
            SELECT ts_code, trade_date, open, high, low, close, volume
            FROM stock_daily
            WHERE ts_code = :ts_code
        """
        
        params = {'ts_code': ts_code}
        
        if start_date:
            query += " AND trade_date >= :start_date"
            params['start_date'] = start_date
        
        if end_date:
            query += " AND trade_date <= :end_date"
            params['end_date'] = end_date
        
        query += " ORDER BY trade_date ASC"
        
        result = self.db.execute(text(query), params)
        rows = result.fetchall()
        
        if not rows:
            return pd.DataFrame()
        
        df = pd.DataFrame(rows, columns=['ts_code', 'trade_date', 'open', 'high', 'low', 'close', 'volume'])
        
        # 转换数值类型
        for col in ['open', 'high', 'low', 'close']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
        
        return df
    
    def _get_factor_data(
        self, 
        ts_code: str,
        start_date: str = None,
        end_date: str = None
    ) -> pd.DataFrame:
        """获取因子数据"""
        
        query = """
            SELECT trade_date, ma5, ma10, ma20, ma30, ma60, ma120
            FROM factor_ma
            WHERE ts_code = :ts_code
        """
        
        params = {'ts_code': ts_code}
        
        if start_date:
            query += " AND trade_date >= :start_date"
            params['start_date'] = start_date
        
        if end_date:
            query += " AND trade_date <= :end_date"
            params['end_date'] = end_date
        
        query += " ORDER BY trade_date ASC"
        
        result = self.db.execute(text(query), params)
        rows = result.fetchall()
        
        if not rows:
            return pd.DataFrame()
        
        df = pd.DataFrame(rows, columns=['trade_date', 'ma5', 'ma10', 'ma20', 'ma30', 'ma60', 'ma120'])
        
        # 转换数值类型
        for col in df.columns:
            if col != 'trade_date':
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    def _get_required_factors(self, strategy_name: str) -> List[str]:
        """获取策略需要的因子"""
        
        # 简化：根据策略名返回所需因子
        if 'ma_cross' in strategy_name:
            return ['ma']
        elif 'breakout' in strategy_name:
            return []
        elif 'rsi_reversal' in strategy_name:
            return ['rsi']
        elif 'bb_reversal' in strategy_name:
            return []
        elif 'mean_reversion' in strategy_name:
            return ['zscore']
        
        return []
    
    def close(self):
        self.db.close()


if __name__ == "__main__":
    # 测试
    engine = StrategyEngine()
    signals = engine.run_strategy('ma_cross_5_20', '000001.SZ')
    print(f"生成 {len(signals)} 个信号:")
    for s in signals:
        print(f"  {s['trade_date']}: {s['direction']} {s['reason']}")
    engine.close()
