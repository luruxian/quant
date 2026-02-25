"""Yahoo Finance API routes"""
from typing import Optional
from fastapi import APIRouter, Query
import yfinance as yf
from datetime import datetime

router = APIRouter()


@router.get("/yf/{symbol}")
def get_yf_data(
    symbol: str,
    period: str = Query("1y", description="Period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Get candlestick data from Yahoo Finance"""
    try:
        ticker = yf.Ticker(symbol)
        
        if start_date and end_date:
            df = ticker.history(start=start_date, end=end_date)
        else:
            df = ticker.history(period=period)
        
        if df.empty:
            return {"error": f"No data for {symbol}"}
        
        data = []
        for idx, row in df.iterrows():
            data.append({
                "time": idx.strftime('%Y-%m-%d') if isinstance(idx, datetime) else str(idx),
                "open": float(row['Open']) if row['Open'] else 0,
                "high": float(row['High']) if row['High'] else 0,
                "low": float(row['Low']) if row['Low'] else 0,
                "close": float(row['Close']) if row['Close'] else 0,
                "volume": float(row['Volume']) if row['Volume'] else 0
            })
        
        return {
            "symbol": symbol,
            "data": data
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/yf/search/{query}")
def search_yf(query: str):
    """Search Yahoo Finance for symbols"""
    try:
        tickers = yf.Tickers(query)
        results = []
        for symbol in tickers.tickers:
            try:
                info = symbol.info
                results.append({
                    "symbol": symbol.ticker,
                    "name": info.get('shortName') or info.get('longName', ''),
                    "type": info.get('quoteType', '')
                })
            except:
                pass
        return {"results": results[:10]}
    except Exception as e:
        return {"error": str(e)}
