#!/usr/bin/env python3
"""
每日数据同步脚本 - 定时任务
自动获取并更新股票、指数、大宗商品、国债收益率、存贷款利率数据
"""
import sys
import logging
import time
from datetime import datetime
import psycopg2
import yfinance as yf
import requests

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/a123/.openclaw/workspace/projects/quant/data_sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DB_CONFIG = {
    'host': 'localhost',
    'database': 'quant',
    'user': 'postgres',
    'password': 'postgres'
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def sync_commodity_data(conn, cur):
    """同步大宗商品数据"""
    result = {'status': 'success', 'updated': 0, 'errors': []}
    
    symbols_map = {
        'CL': 'CL=F',      # WTI原油
        'BZ': 'BZ=F',      # 布伦特原油
        'CORN': 'ZC=F',    # 玉米
        'NG': 'UNG',       # 天然气
        'SOY': 'ZS=F',     # 大豆
        'WHEAT': 'ZW=F',   # 小麦
        'XAGUSD': 'SI=F',  # 白银
    }
    
    # 获取数据库最新日期
    cur.execute("SELECT ts_code, MAX(trade_date) FROM commodity_daily GROUP BY ts_code")
    db_latest = {row[0]: row[1] for row in cur.fetchall() if row[0] != 'XAUUSD'}
    
    for ts_code, sym in symbols_map.items():
        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period='10d')
            
            for date, row in hist.iterrows():
                trade_date = date.date()
                latest_db_date = db_latest.get(ts_code)
                
                if latest_db_date and trade_date <= latest_db_date:
                    continue
                
                cur.execute(
                    'DELETE FROM commodity_daily WHERE ts_code = %s AND trade_date = %s',
                    (ts_code, trade_date)
                )
                cur.execute(
                    '''INSERT INTO commodity_daily (ts_code, trade_date, open, high, low, close, volume, created_at)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())''',
                    (ts_code, trade_date, float(row['Open']), float(row['High']), 
                     float(row['Low']), float(row['Close']), int(row['Volume']))
                )
                result['updated'] += 1
                
        except Exception as e:
            result['errors'].append(f"{ts_code}: {str(e)}")
    
    time.sleep(10)  # 避免请求过快触发限速
    return result

def sync_index_data(conn, cur):
    """同步全球指数数据"""
    result = {'status': 'success', 'updated': 0, 'errors': []}
    
    index_map = {
        'DJI': '^DJI',      # 道琼斯
        'IXIC': '^IXIC',    # 纳斯达克
        'SPX': '^GSPC',     # 标普500
        'NKY': '^N225',     # 日经
    }
    
    cur.execute("SELECT MAX(trade_date) FROM index_daily WHERE ts_code = 'DJI'")
    db_latest = cur.fetchone()[0]
    
    for ts_code, sym in index_map.items():
        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period='10d')
            
            for date, row in hist.iterrows():
                trade_date = date.date()
                if trade_date <= db_latest:
                    continue
                
                cur.execute(
                    'DELETE FROM index_daily WHERE ts_code = %s AND trade_date = %s',
                    (ts_code, trade_date)
                )
                cur.execute(
                    'INSERT INTO index_daily (ts_code, trade_date, open, high, low, close, volume) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                    (ts_code, trade_date, float(row['Open']), float(row['High']), 
                     float(row['Low']), float(row['Close']), int(row['Volume']))
                )
                result['updated'] += 1
                
        except Exception as e:
            result['errors'].append(f"{ts_code}: {str(e)}")
    
    time.sleep(10)  # 避免请求过快触发限速
    return result

def sync_bond_yield(conn, cur):
    """同步国债收益率"""
    result = {'status': 'success', 'updated': 0, 'errors': []}
    
    try:
        resp = requests.get('https://eodhd.com/api/ust/yield-rates?api_token=69a18f8552c015.26099933', timeout=30)
        data = resp.json()['data']
        
        tenor_map = {
            '1M': 'US_1M', '1.5M': 'US_1_5M', '2M': 'US_2M', '3M': 'US_3M',
            '4M': 'US_4M', '6M': 'US_6M', '1Y': 'US_1Y', '2Y': 'US_2Y',
            '3Y': 'US_3Y', '5Y': 'US_5Y', '7Y': 'US_7Y', '10Y': 'US_10Y',
            '20Y': 'US_20Y', '30Y': 'US_30Y'
        }
        
        cur.execute("SELECT MAX(trade_date) FROM bond_yield WHERE ts_code = 'US_10Y'")
        db_latest = str(cur.fetchone()[0] or '2020-01-01')
        
        for item in data:
            date = item['date']
            tenor = tenor_map.get(item['tenor'])
            if tenor and date > db_latest:
                cur.execute(
                    'DELETE FROM bond_yield WHERE ts_code = %s AND trade_date = %s',
                    (tenor, date)
                )
                cur.execute(
                    'INSERT INTO bond_yield (ts_code, trade_date, yield) VALUES (%s, %s, %s)',
                    (tenor, date, item['rate'])
                )
                result['updated'] += 1
                
    except Exception as e:
        result['status'] = 'error'
        result['errors'].append(str(e))
    
    return result

def sync_forex_data(conn, cur):
    """同步外汇数据"""
    result = {'status': 'success', 'updated': 0, 'errors': []}
    
    forex_map = {
        'EURUSD': 'EURUSD=X',
        'GBPUSD': 'GBPUSD=X',
        'USDJPY': 'JPY=X',
        'USDCNY': 'CNY=X',
        'DXY': 'DX-Y.NYB',
    }
    
    cur.execute("SELECT ts_code, MAX(trade_date) FROM forex_daily GROUP BY ts_code")
    db_latest = {row[0]: row[1] for row in cur.fetchall()}
    
    for ts_code, sym in forex_map.items():
        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period='10d')
            
            for date, row in hist.iterrows():
                trade_date = date.date()
                latest_db_date = db_latest.get(ts_code)
                
                if latest_db_date and trade_date <= latest_db_date:
                    continue
                
                cur.execute(
                    'DELETE FROM forex_daily WHERE ts_code = %s AND trade_date = %s',
                    (ts_code, trade_date)
                )
                cur.execute(
                    'INSERT INTO forex_daily (ts_code, trade_date, open, high, low, close) VALUES (%s, %s, %s, %s, %s, %s)',
                    (ts_code, trade_date, float(row['Open']), float(row['High']), 
                     float(row['Low']), float(row['Close']))
                )
                result['updated'] += 1
                
        except Exception as e:
            result['errors'].append(f"{ts_code}: {str(e)}")
    
    time.sleep(10)  # 避免请求过快触发限速
    return result

def sync_crypto_data(conn, cur):
    """同步加密货币数据"""
    result = {'status': 'success', 'updated': 0, 'errors': []}
    
    crypto_map = {
        'BTC': 'BTC-USD',
        'ETH': 'ETH-USD',
    }
    
    cur.execute("SELECT ts_code, MAX(trade_date) FROM crypto_daily GROUP BY ts_code")
    db_latest = {row[0]: row[1] for row in cur.fetchall()}
    
    for ts_code, sym in crypto_map.items():
        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period='10d')
            
            for date, row in hist.iterrows():
                trade_date = date.date()
                latest_db_date = db_latest.get(ts_code)
                
                if latest_db_date and trade_date <= latest_db_date:
                    continue
                
                cur.execute(
                    'DELETE FROM crypto_daily WHERE ts_code = %s AND trade_date = %s',
                    (ts_code, trade_date)
                )
                cur.execute(
                    'INSERT INTO crypto_daily (ts_code, trade_date, open, high, low, close, volume) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                    (ts_code, trade_date, float(row['Open']), float(row['High']), 
                     float(row['Low']), float(row['Close']), int(row['Volume']))
                )
                result['updated'] += 1
                
        except Exception as e:
            result['errors'].append(f"{ts_code}: {str(e)}")
    
    time.sleep(10)  # 避免请求过快触发限速
    return result

def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("开始每日数据同步任务")
    start_time = datetime.now()
    
    report = {
        'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S'),
        'tasks': [],
        'total_updated': 0,
        'all_success': True
    }
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # 1. 大宗商品
        logger.info("同步大宗商品数据...")
        result = sync_commodity_data(conn, cur)
        report['tasks'].append({'name': '大宗商品', **result})
        if result['status'] != 'success' or result['errors']:
            report['all_success'] = False
        report['total_updated'] += result['updated']
        logger.info(f"大宗商品: {result['status']}, 更新 {result['updated']} 条")
        
        # 2. 全球指数
        logger.info("同步全球指数...")
        result = sync_index_data(conn, cur)
        report['tasks'].append({'name': '全球指数', **result})
        if result['status'] != 'success' or result['errors']:
            report['all_success'] = False
        report['total_updated'] += result['updated']
        logger.info(f"全球指数: {result['status']}, 更新 {result['updated']} 条")
        
        # 3. 国债收益率
        logger.info("同步国债收益率...")
        result = sync_bond_yield(conn, cur)
        report['tasks'].append({'name': '国债收益率', **result})
        if result['status'] != 'success' or result['errors']:
            report['all_success'] = False
        report['total_updated'] += result['updated']
        logger.info(f"国债收益率: {result['status']}, 更新 {result['updated']} 条")
        
        # 4. 外汇
        logger.info("同步外汇数据...")
        result = sync_forex_data(conn, cur)
        report['tasks'].append({'name': '外汇', **result})
        if result['status'] != 'success' or result['errors']:
            report['all_success'] = False
        report['total_updated'] += result['updated']
        logger.info(f"外汇: {result['status']}, 更新 {result['updated']} 条")
        
        # 5. 加密货币
        logger.info("同步加密货币...")
        result = sync_crypto_data(conn, cur)
        report['tasks'].append({'name': '加密货币', **result})
        if result['status'] != 'success' or result['errors']:
            report['all_success'] = False
        report['total_updated'] += result['updated']
        logger.info(f"加密货币: {result['status']}, 更新 {result['updated']} 条")
        
        conn.commit()
        
    except Exception as e:
        logger.error(f"同步出错: {str(e)}")
        conn.rollback()
        report['error'] = str(e)
        report['all_success'] = False
        
    finally:
        cur.close()
        conn.close()
    
    end_time = datetime.now()
    report['end_time'] = end_time.strftime('%Y-%m-%d %H:%M:%S')
    report['duration'] = str(end_time - start_time)
    
    # 生成报告
    logger.info("=" * 60)
    logger.info("数据同步完成")
    logger.info(f"总更新: {report['total_updated']} 条")
    logger.info(f"状态: {'全部成功' if report['all_success'] else '部分失败'}")
    
    # 输出JSON格式报告（供后续解析）
    import json
    report_json = json.dumps(report, ensure_ascii=False, indent=2)
    print("\n=== REPORT JSON ===")
    print(report_json)
    print("=== END REPORT ===")
    
    return 0 if report['all_success'] else 1

if __name__ == '__main__':
    sys.exit(main())
