"""
回测 API 路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import date

router = APIRouter(prefix='/backtest', tags=['backtest'])


class BacktestRequest(BaseModel):
    """回测请求"""
    ts_code: str = Field(..., description="股票代码", example="000001.SZ")
    start_date: str = Field(..., description="开始日期", example="2024-01-01")
    end_date: str = Field(..., description="结束日期", example="2024-12-31")
    strategy: str = Field(..., description="策略名称", example="ma_cross")
    params: Optional[Dict[str, Any]] = Field(
        default_factory=dict, 
        description="策略参数",
        example={"ma_fast": 5, "ma_slow": 10}
    )
    initial_cash: float = Field(1000000, description="初始资金", example=1000000)
    commission: float = Field(0.0003, description="手续费率", example=0.0003)
    slippage: float = Field(0.002, description="滑点", example=0.002)
    stake: int = Field(1000, description="每次交易股数", example=1000)


class BacktestResponse(BaseModel):
    """回测响应"""
    status: str
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


@router.post('/run', response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest):
    """
    执行回测
    
    支持策略:
    - ma_cross: 均线交叉策略
    - dual_ma_cross: 双均线交叉策略
    """
    try:
        # 动态加载策略
        strategy_map = {
            'ma_cross': ('strategies.trend.ma_cross_bt', 'MaCrossStrategy'),
            'dual_ma_cross': ('strategies.trend.ma_cross_bt', 'DualMaCrossStrategy'),
        }
        
        if request.strategy not in strategy_map:
            raise HTTPException(
                status_code=400, 
                detail=f"Unknown strategy: {request.strategy}. Available: {list(strategy_map.keys())}"
            )
        
        module_name, class_name = strategy_map[request.strategy]
        strategy_module = __import__(module_name, fromlist=[class_name])
        StrategyClass = getattr(strategy_module, class_name)
        
        # 导入回测引擎
        from backtest.engine import BacktestEngine
        
        # 创建引擎
        engine = BacktestEngine(
            initial_cash=request.initial_cash,
            commission=request.commission,
            slippage=request.slippage,
            stake=request.stake
        )
        
        # 添加数据和策略
        engine.add_data(request.ts_code, request.start_date, request.end_date)
        engine.add_strategy(StrategyClass, **request.params)
        
        # 运行回测
        results = engine.run()
        
        # 添加信号数据
        if hasattr(engine.cerebro.runstrats[0][0], 'signals'):
            results['signals'] = engine.cerebro.runstrats[0][0].signals
        
        return {
            'status': 'success',
            'data': results
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")


@router.get('/strategies')
async def list_strategies():
    """获取可用策略列表"""
    return {
        'strategies': [
            {
                'name': 'ma_cross',
                'display_name': '均线交叉策略',
                'description': '快慢均线交叉产生买卖信号',
                'params': {
                    'ma_fast': {'type': 'int', 'default': 5, 'min': 1, 'max': 20},
                    'ma_slow': {'type': 'int', 'default': 10, 'min': 5, 'max': 60},
                }
            },
            {
                'name': 'dual_ma_cross',
                'display_name': '双均线交叉策略',
                'description': '多周期均线确认，提高信号质量',
                'params': {
                    'short_fast': {'type': 'int', 'default': 5, 'min': 1, 'max': 20},
                    'short_slow': {'type': 'int', 'default': 10, 'min': 5, 'max': 60},
                    'long_fast': {'type': 'int', 'default': 20, 'min': 10, 'max': 60},
                    'long_slow': {'type': 'int', 'default': 60, 'min': 30, 'max': 120},
                }
            }
        ]
    }


@router.get('/test')
async def test_backtest():
    """测试回测接口"""
    return {
        'status': 'ok',
        'message': 'Backtest API is running'
    }
