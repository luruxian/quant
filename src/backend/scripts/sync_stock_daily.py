#!/usr/bin/env python3
"""
从 Akshare 或 Tushare 获取股票日线数据并存储到数据库
注意遵守数据源的获取数据规则，避免高并发和过于频繁的数据获取

优先使用 Tushare（如果有 token），因为 Akshare 的东方财富接口可能有网络问题
"""
import time
import logging
from datetime import datetime, timedelta
from typing import List, Optional

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 数据库连接
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/quant"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def get_stock_list_from_db() -> List[str]:
    """从数据库获取股票列表"""
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT ts_code FROM stock_info WHERE list_status = 'L' ORDER BY ts_code")
        ).fetchall()
    return [row[0] for row in result]


def get_latest_date_from_db(ts_code: str) -> Optional[str]:
    """获取某只股票在数据库中的最新日期"""
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT MAX(trade_date) 
                FROM stock_daily 
                WHERE ts_code = :ts_code
            """),
            {"ts_code": ts_code}
        ).fetchone()
    return result[0].strftime('%Y-%m-%d') if result[0] else None


def fetch_daily_data_from_tushare(ts_code: str, start_date: str = None, token: str = None) -> pd.DataFrame:
    """
    从 Tushare 获取单只股票的日线数据
    
    注意：
    - 需要 Tushare token
    - 请求频率限制：每分钟 500 次
    - 每次请求之间添加适当延迟
    """
    try:
        import tushare as ts
        
        if token:
            pro = ts.pro_api(token)
        else:
            pro = ts.pro_api()
        
        # 格式转换: 2025-01-01 -> 20250101
        start = start_date.replace('-', '') if start_date else '19700101'
        end = datetime.now().strftime('%Y%m%d')
        
        # Tushare 获取日线
        df = pro.daily(ts_code=ts_code, start_date=start, end_date=end)
        
        if df is None or df.empty:
            logger.warning(f"{ts_code}: 无数据")
            return pd.DataFrame()
        
        # 重命名列
        df.rename(columns={
            'vol': 'volume',
        }, inplace=True)
        
        # 处理日期格式
        df['trade_date'] = pd.to_datetime(df['trade_date']).dt.strftime('%Y-%m-%d')
        
        # 选择需要的列（保持与数据库一致）
        columns = ['ts_code', 'trade_date', 'open', 'close', 'high', 'low', 
                   'volume', 'amount', 'pct_chg', 'turnover_rate']
        
        # Tushare 返回的字段可能不完整，只选择存在的列
        available_columns = [c for c in columns if c in df.columns]
        df = df[available_columns].copy()
        
        # 补充缺失的列
        if 'amplitude' not in df.columns:
            df['amplitude'] = None
        if 'change_amt' not in df.columns:
            df['change_amt'] = None
        
        return df
        
    except Exception as e:
        logger.error(f"{ts_code}: Tushare 获取数据失败 - {str(e)}")
        return pd.DataFrame()


def fetch_daily_data_from_akshare(ts_code: str, start_date: str = None) -> pd.DataFrame:
    """
    从 Akshare 获取单只股票的日线数据
    
    注意：
    - 遵守请求频率限制
    - 每次请求之间添加延迟
    - 东方财富接口可能有网络问题
    """
    try:
        import akshare as ak
        
        # 股票代码转换: 000001.SZ -> 000001
        symbol = ts_code.split('.')[0]
        
        # A股日线数据
        stock_zh_a_hist_df = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=start_date.replace('-', '') if start_date else "19700101",
            end_date=datetime.now().strftime('%Y%m%d'),
            adjust=""
        )
        
        if stock_zh_a_hist_df.empty:
            logger.warning(f"{ts_code}: 无数据")
            return pd.DataFrame()
        
        # 重命名列
        stock_zh_a_hist_df.rename(columns={
            '日期': 'trade_date',
            '股票代码': 'ts_code',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'amount',
            '振幅': 'amplitude',
            '涨跌幅': 'pct_chg',
            '涨跌额': 'change_amt',
            '换手率': 'turnover_rate'
        }, inplace=True)
        
        # 处理日期格式
        stock_zh_a_hist_df['trade_date'] = pd.to_datetime(stock_zh_a_hist_df['trade_date']).dt.strftime('%Y-%m-%d')
        stock_zh_a_hist_df['ts_code'] = ts_code
        
        # 选择需要的列
        columns = ['ts_code', 'trade_date', 'open', 'close', 'high', 'low', 
                   'volume', 'amount', 'amplitude', 'pct_chg', 'change_amt', 'turnover_rate']
        stock_zh_a_hist_df = stock_zh_a_hist_df[columns]
        
        return stock_zh_a_hist_df
        
    except Exception as e:
        logger.error(f"{ts_code}: Akshare 获取数据失败 - {str(e)}")
        return pd.DataFrame()


def save_to_db(df: pd.DataFrame, ts_code: str):
    """保存数据到数据库"""
    if df.empty:
        return 0
    
    with engine.connect() as conn:
        # 使用 INSERT ... ON CONFLICT 来处理重复数据
        for _, row in df.iterrows():
            conn.execute(
                text("""
                    INSERT INTO stock_daily 
                    (ts_code, trade_date, open, close, high, low, volume, amount, 
                     amplitude, pct_chg, change_amt, turnover_rate, created_at)
                    VALUES 
                    (:ts_code, :trade_date, :open, :close, :high, :low, :volume, :amount,
                     :amplitude, :pct_chg, :change_amt, :turnover_rate, :created_at)
                    ON CONFLICT (ts_code, trade_date) DO UPDATE SET
                        open = EXCLUDED.open,
                        close = EXCLUDED.close,
                        high = EXCLUDED.high,
                        low = EXCLUDED.low,
                        volume = EXCLUDED.volume,
                        amount = EXCLUDED.amount,
                        amplitude = EXCLUDED.amplitude,
                        pct_chg = EXCLUDED.pct_chg,
                        change_amt = EXCLUDED.change_amt,
                        turnover_rate = EXCLUDED.turnover_rate
                """),
                {
                    'ts_code': row['ts_code'],
                    'trade_date': row['trade_date'],
                    'open': float(row['open']) if pd.notna(row.get('open')) else None,
                    'close': float(row['close']) if pd.notna(row.get('close')) else None,
                    'high': float(row['high']) if pd.notna(row.get('high')) else None,
                    'low': float(row['low']) if pd.notna(row.get('low')) else None,
                    'volume': int(row['volume']) if pd.notna(row.get('volume')) else None,
                    'amount': float(row['amount']) if pd.notna(row.get('amount')) else None,
                    'amplitude': float(row['amplitude']) if pd.notna(row.get('amplitude')) else None,
                    'pct_chg': float(row['pct_chg']) if pd.notna(row.get('pct_chg')) else None,
                    'change_amt': float(row['change_amt']) if pd.notna(row.get('change_amt')) else None,
                    'turnover_rate': float(row['turnover_rate']) if pd.notna(row.get('turnover_rate')) else None,
                    'created_at': datetime.now()
                }
            )
        conn.commit()
    
    return len(df)


def sync_stock_daily_data(source: str = 'tushare', limit: int = None, delay: float = 0.5, token: str = None):
    """
    同步股票日线数据
    
    参数:
        source: 数据源 ('tushare' 或 'akshare')
        limit: 限制处理的股票数量（用于测试）
        delay: 每次请求之间的延迟（秒），遵守数据源频率限制
        token: Tushare token（必需 if source='tushare'）
    
    注意：
    - Tushare: 每分钟 500 次请求，建议 delay >= 0.12 秒
    - Akshare: 建议 delay >= 1 秒，避免被封
    """
    # 获取股票列表
    stock_list = get_stock_list_from_db()
    if limit:
        stock_list = stock_list[:limit]
    
    total_stocks = len(stock_list)
    success_count = 0
    error_count = 0
    
    logger.info(f"开始同步 {total_stocks} 只股票的日线数据 (数据源: {source})")
    
    for i, ts_code in enumerate(stock_list, 1):
        try:
            # 获取数据库中该股票的最新日期
            latest_date = get_latest_date_from_db(ts_code)
            
            # 如果有最新日期，从最新日期的下一天开始获取
            start_date = None
            if latest_date:
                start_date = (datetime.strptime(latest_date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
                # 检查是否需要更新（如果最新日期是今天或昨天，则跳过）
                if (datetime.now() - datetime.strptime(latest_date, '%Y-%m-%d')).days <= 1:
                    logger.info(f"[{i}/{total_stocks}] {ts_code}: 数据已是最新 ({latest_date})")
                    continue
            
            logger.info(f"[{i}/{total_stocks}] {ts_code}: 获取数据 from {start_date or '全部'}")
            
            # 从数据源获取数据
            if source == 'tushare':
                df = fetch_daily_data_from_tushare(ts_code, start_date, token)
            else:
                df = fetch_daily_data_from_akshare(ts_code, start_date)
            
            if df.empty:
                logger.warning(f"[{i}/{total_stocks}] {ts_code}: 无数据")
                continue
            
            # 保存到数据库
            saved_count = save_to_db(df, ts_code)
            success_count += 1
            logger.info(f"[{i}/{total_stocks}] {ts_code}: 成功保存 {saved_count} 条记录")
            
            # 遵守请求频率限制
            if i < total_stocks:
                time.sleep(delay)
                
        except Exception as e:
            error_count += 1
            logger.error(f"[{i}/{total_stocks}] {ts_code}: 错误 - {str(e)}")
            # 遇到错误时增加延迟
            time.sleep(delay * 2)
    
    logger.info(f"同步完成: 成功 {success_count}, 失败 {error_count}")
    return {
        'total': total_stocks,
        'success': success_count,
        'error': error_count
    }


if __name__ == "__main__":
    import sys
    import os
    
    # 解析命令行参数
    # python sync_stock_daily.py [source] [limit] [delay]
    # source: tushare (默认) 或 akshare
    
    source = sys.argv[1] if len(sys.argv) > 1 else 'tushare'
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    delay = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
    
    # 获取 Tushare token
    token = os.environ.get('TUSHARE_TOKEN') or '4cc87c1b8cd2cb407e74ceaebf9e1c8a6231508e91494c48c20d0daa'
    
    if source == 'tushare' and not token:
        logger.error("Tushare 需要 token，请设置 TUSHARE_TOKEN 环境变量或在 .env 中配置")
        sys.exit(1)
    
    # 如果使用 akshare 且失败，会自动跳过
    sync_stock_daily_data(source=source, limit=limit, delay=delay, token=token)
