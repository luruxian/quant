#!/usr/bin/env python3
"""
从 Akshare 获取股票日线数据并存储到数据库
注意遵守 akshare 的获取数据规则，避免高并发和过于频繁的数据获取
"""
import time
import logging
from datetime import datetime, timedelta
from typing import List, Optional

import akshare as ak
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


def fetch_daily_data_from_akshare(ts_code: str, start_date: str = None) -> pd.DataFrame:
    """
    从 Akshare 获取单只股票的日线数据
    
    注意：
    - 遵守请求频率限制
    - 每次请求之间添加延迟
    """
    try:
        # 股票代码转换: 000001.SZ -> 000001
        symbol = ts_code.split('.')[0]
        
        # A股日线数据
        stock_zh_a_hist_df = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=start_date or "19700101",
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
        logger.error(f"{ts_code}: 获取数据失败 - {str(e)}")
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
                    'open': float(row['open']) if pd.notna(row['open']) else None,
                    'close': float(row['close']) if pd.notna(row['close']) else None,
                    'high': float(row['high']) if pd.notna(row['high']) else None,
                    'low': float(row['low']) if pd.notna(row['low']) else None,
                    'volume': int(row['volume']) if pd.notna(row['volume']) else None,
                    'amount': float(row['amount']) if pd.notna(row['amount']) else None,
                    'amplitude': float(row['amplitude']) if pd.notna(row['amplitude']) else None,
                    'pct_chg': float(row['pct_chg']) if pd.notna(row['pct_chg']) else None,
                    'change_amt': float(row['change_amt']) if pd.notna(row['change_amt']) else None,
                    'turnover_rate': float(row['turnover_rate']) if pd.notna(row['turnover_rate']) else None,
                    'created_at': datetime.now()
                }
            )
        conn.commit()
    
    return len(df)


def sync_stock_daily_data(limit: int = None, delay: float = 1.0):
    """
    同步股票日线数据
    
    参数:
        limit: 限制处理的股票数量（用于测试）
        delay: 每次请求之间的延迟（秒），遵守 akshare 频率限制
    """
    # 获取股票列表
    stock_list = get_stock_list_from_db()
    if limit:
        stock_list = stock_list[:limit]
    
    total_stocks = len(stock_list)
    success_count = 0
    error_count = 0
    
    logger.info(f"开始同步 {total_stocks} 只股票的日线数据")
    
    for i, ts_code in enumerate(stock_list, 1):
        try:
            # 获取数据库中该股票的最新日期
            latest_date = get_latest_date_from_db(ts_code)
            
            # 如果有最新日期，从最新日期的下一天开始获取
            start_date = None
            if latest_date:
                start_date = (datetime.strptime(latest_date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y%m%d')
                # 检查是否需要更新（如果最新日期是今天或昨天，则跳过）
                if (datetime.now() - datetime.strptime(latest_date, '%Y-%m-%d')).days <= 1:
                    logger.info(f"[{i}/{total_stocks}] {ts_code}: 数据已是最新 ({latest_date})")
                    continue
            
            logger.info(f"[{i}/{total_stocks}] {ts_code}: 获取数据 from {start_date or '全部'}")
            
            # 从 Akshare 获取数据
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
    
    # 可以通过命令行参数控制
    # python sync_akshare_daily.py [limit] [delay]
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    delay = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
    
    sync_stock_daily_data(limit=limit, delay=delay)
