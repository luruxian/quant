"""Data service for fetching stock data from database"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy import text
from utils.db import SessionLocal


class DataService:
    def __init__(self):
        self.db = SessionLocal()

    def get_candlestick_data(
        self,
        ts_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get candlestick data for a stock (from stock_daily or index_daily)"""
        
        # Default: last 6 months
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')

        # Try stock_daily first, then index_daily
        query = """
            SELECT ts_code, trade_date, open, high, low, close, volume
            FROM stock_daily
            WHERE ts_code = :ts_code
              AND trade_date >= :start_date
              AND trade_date <= :end_date
            ORDER BY trade_date ASC
        """

        result = self.db.execute(
            text(query),
            {"ts_code": ts_code, "start_date": start_date, "end_date": end_date}
        ).fetchall()

        # If no data, try index_daily
        if not result:
            query = """
                SELECT ts_code, trade_date, open, high, low, close, volume
                FROM index_daily
                WHERE ts_code = :ts_code
                  AND trade_date >= :start_date
                  AND trade_date <= :end_date
                ORDER BY trade_date ASC
            """
            result = self.db.execute(
                text(query),
                {"ts_code": ts_code, "start_date": start_date, "end_date": end_date}
            ).fetchall()

        data = []
        for row in result:
            data.append({
                "time": row.trade_date.strftime('%Y-%m-%d') if isinstance(row.trade_date, datetime) else str(row.trade_date),
                "open": float(row.open) if row.open else 0,
                "high": float(row.high) if row.high else 0,
                "low": float(row.low) if row.low else 0,
                "close": float(row.close) if row.close else 0,
                "volume": float(row.volume) if row.volume else 0
            })

        # Get stock name
        name = self._get_stock_name(ts_code)

        return {
            "ts_code": ts_code,
            "name": name,
            "data": data
        }

    def get_signals(
        self,
        ts_code: str,
        days: int = 60
    ) -> Dict[str, Any]:
        """Get trading signals for a stock"""
        
        query = """
            SELECT ts_code, trade_date, direction, price, strategy
            FROM signal
            WHERE ts_code = :ts_code
            ORDER BY trade_date DESC
            LIMIT :days
        """

        result = self.db.execute(
            text(query),
            {"ts_code": ts_code, "days": days}
        ).fetchall()

        signals = []
        for row in result:
            signal_type = "buy" if row.direction == "LONG" else "sell"
            position = "belowBar" if row.direction == "LONG" else "aboveBar"
            
            signals.append({
                "time": row.trade_date.strftime('%Y-%m-%d') if isinstance(row.trade_date, datetime) else str(row.trade_date),
                "position": position,
                "direction": row.direction,
                "price": float(row.price) if row.price else 0,
                "type": signal_type,
                "strategy": row.strategy
            })

        # Reverse to chronological order
        signals.reverse()

        return {
            "ts_code": ts_code,
            "signals": signals
        }

    def get_indicators(
        self,
        ts_code: str,
        ma: str = "5,10,20,60"
    ) -> Dict[str, Any]:
        """Get technical indicators for a stock"""
        
        ma_list = [x.strip() for x in ma.split(',')]
        
        # Build query dynamically
        valid_ma = [m for m in ma_list if m in ['ma5', 'ma10', 'ma20', 'ma30', 'ma60', 'ma120', 'ema12', 'ema26', 'macd', 'macd_signal', 'macd_hist']]
        
        if not valid_ma:
            return {"ts_code": ts_code, "indicators": {}}
        
        ma_columns = ", ".join([f"{m}" for m in valid_ma])
        
        query = f"""
            SELECT trade_date, {ma_columns}
            FROM factor_ma
            WHERE ts_code = :ts_code
            ORDER BY trade_date DESC
            LIMIT 120
        """

        result = self.db.execute(
            text(query),
            {"ts_code": ts_code}
        ).fetchall()

        indicators = {m: [] for m in valid_ma}
        
        for row in result:
            time_str = row.trade_date.strftime('%Y-%m-%d') if isinstance(row.trade_date, datetime) else str(row.trade_date)
            for m in valid_ma:
                value = getattr(row, m, None)
                if value is not None:
                    indicators[m].append({
                        "time": time_str,
                        "value": float(value)
                    })

        # Reverse to chronological order
        for key in indicators:
            indicators[key].reverse()

        return {
            "ts_code": ts_code,
            "indicators": indicators
        }

    def _get_stock_name(self, ts_code: str) -> str:
        """Get stock name from database"""
        query = "SELECT name FROM stock_info WHERE ts_code = :ts_code"
        result = self.db.execute(text(query), {"ts_code": ts_code}).fetchone()
        if result:
            return result.name
        return ts_code

    def get_stock_list(self):
        """Get list of available stocks"""
        query = """
            SELECT ts_code, name 
            FROM stock_info 
            WHERE list_status = 'L'
            ORDER BY ts_code
            LIMIT 100
        """
        result = self.db.execute(text(query)).fetchall()
        return [{"ts_code": row[0], "name": row[1]} for row in result]

    def close(self):
        self.db.close()
