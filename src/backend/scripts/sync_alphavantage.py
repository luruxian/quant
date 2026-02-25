#!/usr/bin/env python3
"""
Alpha Vantage 数据同步脚本
用于外汇、加密货币、美股/指数数据
API: https://www.alphavantage.co/query
免费版限制: 5 calls/min, 500 calls/day
"""
import time
import logging
from datetime import datetime
import psycopg2
import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

API_KEY = "FN503KXKYK4X92Y9"
BASE_URL = "https://www.alphavantage.co/query"

DB_CONFIG = {
    'host': 'localhost',
    'database': 'quant',
    'user': 'postgres',
    'password': 'postgres'
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def sync_forex_av(conn, cur):
    """同步外汇数据 (Alpha Vantage)"""
    result = {'status': 'success', 'updated': 0, 'errors': []}
    
    pairs = [
        ('EURUSD', 'EUR', 'USD'),
        ('GBPUSD', 'GBP', 'USD'),
        ('USDJPY', 'USD', 'JPY'),
        ('USDCNY', 'USD', 'CNY'),
        ('DXY', 'USD', 'IDX'),  # 美元指数
    ]
    
    for ts_code, from_sym, to_sym in pairs:
        try:
            # 美元指数用 CRIX 替代
            if ts_code == 'DXY':
                func = "CRIX_DAILY"
                params = {"function": func, "symbol": "DBIQUSD", "apikey": API_KEY}
            else:
                func = "FX_DAILY"
                params = {"function": func, "from_symbol": from_sym, "to_symbol": to_sym, "apikey": API_KEY, "outputsize": "compact"}
            
            resp = requests.get(BASE_URL, params=params, timeout=30)
            data = resp.json()
            
            if "Error Message" in data or "Note" in data:
                result['errors'].append(f"{ts_code}: {data.get('Error Message') or data.get('Note')}")
                continue
            
            time_series = data.get("Time Series FX (Daily)") or data.get("Time Series (Daily)")
            if not time_series:
                result['errors'].append(f"{ts_code}: No data")
                continue
            
            cur.execute("SELECT MAX(trade_date) FROM forex_daily WHERE ts_code = %s", (ts_code,))
            db_latest = cur.fetchone()[0]
            
            for date_str, values in list(time_series.items())[:10]:
                trade_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                if db_latest and trade_date <= db_latest:
                    continue
                
                cur.execute(
                    'DELETE FROM forex_daily WHERE ts_code = %s AND trade_date = %s',
                    (ts_code, trade_date)
                )
                cur.execute(
                    '''INSERT INTO forex_daily (ts_code, trade_date, open, high, low, close, created_at)
                       VALUES (%s, %s, %s, %s, %s, %s, NOW())''',
                    (ts_code, trade_date, 
                     float(values['1. open']), float(values['2. high']),
                     float(values['3. low']), float(values['4. close']))
                )
                result['updated'] += 1
            
            logger.info(f"{ts_code}: 更新 {result['updated']} 条")
            
        except Exception as e:
            result['errors'].append(f"{ts_code}: {str(e)}")
        
        time.sleep(12)  # 免费版限制 5 calls/min
    
    return result

def sync_crypto_av(conn, cur):
    """同步加密货币数据 (Alpha Vantage)"""
    result = {'status': 'success', 'updated': 0, 'errors': []}
    
    cryptos = [('BTC', 'USD'), ('ETH', 'USD')]
    
    for ts_code, market in cryptos:
        try:
            params = {
                "function": "DIGITAL_CURRENCY_DAILY",
                "symbol": ts_code,
                "market": market,
                "apikey": API_KEY
            }
            
            resp = requests.get(BASE_URL, params=params, timeout=30)
            data = resp.json()
            
            if "Error Message" in data or "Note" in data:
                result['errors'].append(f"{ts_code}: {data.get('Error Message') or data.get('Note')}")
                continue
            
            time_series = data.get("Time Series (Digital Currency Daily)")
            if not time_series:
                result['errors'].append(f"{ts_code}: No data")
                continue
            
            cur.execute("SELECT MAX(trade_date) FROM crypto_daily WHERE ts_code = %s", (ts_code,))
            db_latest = cur.fetchone()[0]
            
            for date_str, values in list(time_series.items())[:10]:
                trade_date = datetime.strptime(date_str.split()[0], '%Y-%m-%d').date()
                if db_latest and trade_date <= db_latest:
                    continue
                
                cur.execute(
                    'DELETE FROM crypto_daily WHERE ts_code = %s AND trade_date = %s',
                    (ts_code, trade_date)
                )
                cur.execute(
                    '''INSERT INTO crypto_daily (ts_code, trade_date, open, high, low, close, volume, created_at)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())''',
                    (ts_code, trade_date,
                     float(values['1. open']), float(values['2. high']),
                     float(values['3. low']), float(values['4. close']),
                     float(values['5. volume']))
                )
                result['updated'] += 1
            
            logger.info(f"{ts_code}: 更新 {result['updated']} 条")
            
        except Exception as e:
            result['errors'].append(f"{ts_code}: {str(e)}")
        
        time.sleep(12)
    
    return result

def main():
    logger.info("=" * 60)
    logger.info("开始 Alpha Vantage 数据同步")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # 同步外汇
    logger.info("同步外汇数据...")
    forex_result = sync_forex_av(conn, cur)
    conn.commit()
    logger.info(f"外汇: 更新 {forex_result['updated']} 条, 错误: {forex_result['errors']}")
    
    # 同步加密货币
    logger.info("同步加密货币数据...")
    crypto_result = sync_crypto_av(conn, cur)
    conn.commit()
    logger.info(f"加密货币: 更新 {crypto_result['updated']} 条, 错误: {crypto_result['errors']}")
    
    cur.close()
    conn.close()
    
    logger.info("同步完成!")

if __name__ == "__main__":
    main()
