"""因子和策略 API"""
from typing import Optional, List
from fastapi import APIRouter, Query
from pydantic import BaseModel

from factors import list_factors, get_factor, FACTOR_REGISTRY
from strategies import list_strategies, get_strategy, STRATEGY_REGISTRY
from engine.factor_engine import FactorEngine
from engine.strategy_engine import StrategyEngine

router = APIRouter()


# ============ 因子 API ============

@router.get("/factors")
def get_factor_list():
    """获取所有可用因子"""
    return {"factors": list_factors()}


@router.get("/factors/{ts_code}")
def get_factors(
    ts_code: str,
    names: str = Query(None, description="因子名称，逗号分隔"),
    start_date: str = Query(None, description="开始日期"),
    end_date: str = Query(None, description="结束日期")
):
    """获取股票的因子数据"""
    engine = FactorEngine()
    try:
        factor_names = names.split(',') if names else None
        df = engine.compute_factors_for_stock(ts_code, factor_names)
        
        if df.empty:
            return {"ts_code": ts_code, "data": []}
        
        # 转换为API响应格式
        data = []
        for _, row in df.iterrows():
            item = {
                "trade_date": str(row['trade_date']),
            }
            # 添加所有数值列
            for col in df.columns:
                if col not in ['trade_date', 'ts_code'] and pd.notna(row.get(col)):
                    item[col] = float(row[col])
            
            data.append(item)
        
        return {"ts_code": ts_code, "data": data}
    finally:
        engine.close()


@router.post("/factors/{ts_code}/compute")
def compute_factors(
    ts_code: str,
    names: str = Query(None, description="因子名称，逗号分隔")
):
    """计算并保存因子数据"""
    engine = FactorEngine()
    try:
        factor_names = names.split(',') if names else None
        engine.compute_and_save(ts_code, factor_names)
        return {"status": "ok", "ts_code": ts_code}
    finally:
        engine.close()


# ============ 策略 API ============

@router.get("/strategies")
def get_strategy_list():
    """获取所有可用策略"""
    return {"strategies": list_strategies()}


@router.get("/strategies/{strategy_name}")
def get_strategy_info(strategy_name: str):
    """获取策略详情"""
    try:
        strategy = get_strategy(strategy_name)
        return {
            "name": strategy.name,
            "description": strategy.description,
            "params": strategy.params
        }
    except ValueError as e:
        return {"error": str(e)}


@router.get("/signals/{ts_code}")
def get_signals(
    ts_code: str,
    strategy: str = Query(None, description="策略名称"),
    start_date: str = Query(None, description="开始日期"),
    end_date: str = Query(None, description="结束日期")
):
    """获取交易信号"""
    engine = StrategyEngine()
    try:
        if strategy:
            # 单策略
            signals = engine.run_strategy(strategy, ts_code, start_date, end_date)
            return {
                "ts_code": ts_code,
                "strategy": strategy,
                "signals": signals
            }
        else:
            # 所有策略
            results = engine.run_all_strategies(ts_code, start_date, end_date)
            
            # 汇总所有信号
            all_signals = []
            for strat_name, signals in results.items():
                for s in signals:
                    s['strategy'] = strat_name
                    all_signals.append(s)
            
            # 按日期排序
            all_signals.sort(key=lambda x: x['trade_date'])
            
            return {
                "ts_code": ts_code,
                "signals": all_signals
            }
    finally:
        engine.close()


@router.post("/signals/{ts_code}/run")
def run_strategy(
    ts_code: str,
    strategy: str = Query(..., description="策略名称"),
    start_date: str = Query(None, description="开始日期"),
    end_date: str = Query(None, description="结束日期"),
    save: bool = Query(False, description="是否保存到数据库")
):
    """运行策略生成信号"""
    engine = StrategyEngine()
    try:
        signals = engine.run_strategy(strategy, ts_code, start_date, end_date)
        
        if save:
            engine.save_signals(signals, strategy)
        
        return {
            "ts_code": ts_code,
            "strategy": strategy,
            "signals": signals,
            "count": len(signals)
        }
    finally:
        engine.close()


# ============ 技术指标 API ============

@router.get("/indicators/{ts_code}")
def get_indicators(
    ts_code: str,
    ma: str = Query("5,10,20,60", description="移动平均线，逗号分隔")
):
    """获取股票的技术指标"""
    from services.data_service import DataService
    service = DataService()
    try:
        result = service.get_indicators(ts_code, ma)
        return result
    finally:
        service.close()


# 导入pandas用于类型转换
import pandas as pd
