"""
PostgreSQL 数据适配器 - 将数据库数据转换为 Backtrader 格式
"""
import backtrader as bt
import pandas as pd
from sqlalchemy import create_engine
import os


class PostgresData(bt.feeds.PandasData):
    """
    从 PostgreSQL 加载股票数据到 Backtrader
    
    列名映射：
    - trade_date → datetime
    - open, high, low, close, volume → 直接使用
    """
    
    params = (
        ('datetime', 0),  # 使用第0列 (trade_date)
        ('open', 1),
        ('high', 2),
        ('low', 3),
        ('close', 4),
        ('volume', 5),
        ('openinterest', -1),
    )
    
    @classmethod
    def from_db(cls, ts_code: str, start_date: str, end_date: str):
        """
        从数据库加载股票数据
        
        Args:
            ts_code: 股票代码 (如 000001.SZ)
            start_date: 开始日期 (如 2024-01-01)
            end_date: 结束日期 (如 2024-12-31)
        
        Returns:
            PostgresData 实例
        """
        # 从环境变量或默认配置获取数据库连接
        db_url = os.getenv(
            'DATABASE_URL',
            'postgresql://postgres:postgres@localhost:5432/quant'
        )
        engine = create_engine(db_url)
        
        query = """
            SELECT trade_date, open, high, low, close, volume
            FROM stock_daily
            WHERE ts_code = %s
            AND trade_date BETWEEN %s AND %s
            ORDER BY trade_date
        """
        
        df = pd.read_sql(query, engine, params=(ts_code, start_date, end_date))
        
        if df.empty:
            raise ValueError(f"No data found for {ts_code} between {start_date} and {end_date}")
        
        # 转换日期格式
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        
        return cls(dataname=df)
