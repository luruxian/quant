"""Stock API routes"""
from typing import Optional
from fastapi import APIRouter, Query
from services.data_service import DataService

router = APIRouter()


@router.get("/stocks")
def get_stock_list():
    """Get list of available stocks"""
    service = DataService()
    try:
        stocks = service.get_stock_list()
        return {"stocks": stocks}
    finally:
        service.close()


@router.get("/stock/{ts_code}")
def get_stock_data(
    ts_code: str,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
):
    """Get candlestick data for a stock"""
    service = DataService()
    try:
        result = service.get_candlestick_data(ts_code, start_date, end_date)
        return result
    finally:
        service.close()
