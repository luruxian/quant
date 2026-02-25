"""因子计算引擎"""
import pandas as pd
from typing import Dict, List
from factors import FACTOR_REGISTRY, get_factor
from utils.db import SessionLocal
from sqlalchemy import text


class FactorEngine:
    """因子计算引擎"""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def compute_factors_for_stock(
        self, 
        ts_code: str, 
        factor_names: List[str] = None
    ) -> pd.DataFrame:
        """为单个股票计算因子
        
        Args:
            ts_code: 股票代码
            factor_names: 要计算的因子列表，None表示全部
            
        Returns:
            包含所有因子的DataFrame
        """
        # 获取行情数据
        prices = self._get_price_data(ts_code)
        
        if prices.empty:
            return pd.DataFrame()
        
        # 确定要计算的因子
        if factor_names is None:
            factor_names = list(FACTOR_REGISTRY.keys())
        
        # 计算所有因子
        result = pd.DataFrame()
        result['trade_date'] = prices['trade_date']
        result['ts_code'] = ts_code
        
        for name in factor_names:
            try:
                factor = get_factor(name)
                factor_result = factor.compute(prices)
                
                # 合并因子结果（排除trade_date列）
                for col in factor_result.columns:
                    if col != 'trade_date':
                        result[col] = factor_result[col].values
                        
            except Exception as e:
                print(f"因子 {name} 计算失败: {e}")
                continue
        
        return result
    
    def compute_and_save(
        self, 
        ts_code: str, 
        factor_names: List[str] = None
    ):
        """计算因子并保存到数据库"""
        
        factors_df = self.compute_factors_for_stock(ts_code, factor_names)
        
        if factors_df.empty:
            print(f"无数据: {ts_code}")
            return
        
        # 保存到 factor_ma 表（简化：只保存MA相关列）
        for _, row in factors_df.iterrows():
            trade_date = row['trade_date']
            
            # MA因子
            ma_cols = {col: row[col] for col in factors_df.columns 
                      if col.startswith('ma') and pd.notna(row.get(col))}
            
            if ma_cols:
                self.db.execute(text("""
                    INSERT INTO factor_ma (ts_code, trade_date, ma5, ma10, ma20, ma30, ma60, ma120)
                    VALUES (:ts_code, :trade_date, :ma5, :ma10, :ma20, :ma30, :ma60, :ma120)
                    ON CONFLICT (ts_code, trade_date) DO UPDATE SET
                        ma5 = EXCLUDED.ma5,
                        ma10 = EXCLUDED.ma10,
                        ma20 = EXCLUDED.ma20,
                        ma60 = EXCLUDED.ma60
                """), {
                    'ts_code': ts_code,
                    'trade_date': trade_date,
                    'ma5': ma_cols.get('ma5'),
                    'ma10': ma_cols.get('ma10'),
                    'ma20': ma_cols.get('ma20'),
                    'ma30': ma_cols.get('ma30'),
                    'ma60': ma_cols.get('ma60'),
                    'ma120': ma_cols.get('ma120'),
                })
        
        self.db.commit()
        print(f"✅ {ts_code}: {len(factors_df)} 条因子数据")
    
    def _get_price_data(self, ts_code: str) -> pd.DataFrame:
        """从数据库获取行情数据"""
        
        result = self.db.execute(text("""
            SELECT trade_date, open, high, low, close, volume
            FROM stock_daily
            WHERE ts_code = :ts_code
            ORDER BY trade_date ASC
        """), {'ts_code': ts_code})
        
        rows = result.fetchall()
        
        if not rows:
            return pd.DataFrame()
        
        df = pd.DataFrame(rows, columns=['trade_date', 'open', 'high', 'low', 'close', 'volume'])
        return df
    
    def close(self):
        self.db.close()


if __name__ == "__main__":
    # 测试
    engine = FactorEngine()
    engine.compute_and_save('000001.SZ', ['ma', 'macd', 'rsi'])
    engine.close()
