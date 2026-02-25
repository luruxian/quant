# 回测模块设计文档

**版本**: v1.0  
**创建时间**: 2026-02-25  
**状态**: 待评审

---

## 一、目标

构建基于 Backtrader 的回测系统，复用现有因子/策略引擎，提供完整的回测→分析→可视化流程。

### 核心需求

| 需求 | 说明 | 优先级 |
|------|------|--------|
| 历史数据回测 | 支持任意股票、任意时间段 | P0 |
| 策略信号回放 | 复用现有策略引擎 | P0 |
| 订单模拟 | 支持手续费、滑点、仓位管理 | P0 |
| 绩效分析 | 收益率、夏普、回撤等核心指标 | P0 |
| 可视化展示 | K 线 + 信号 + 资金曲线 | P0 |
| 交易记录 | 每笔交易的详细信息 | P1 |
| 多策略对比 | 同时回测多个策略 | P2 |
| 参数优化 | 策略参数网格搜索 | P2 |

---

## 二、架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      前端 (React)                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ 回测配置表单 │  │ 绩效指标卡  │  │ K 线 + 信号 + 资金曲线 │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                    交易记录表格                          ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              ↕ HTTP/JSON
┌─────────────────────────────────────────────────────────────┐
│                   后端 (FastAPI)                            │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  API Routes                                             ││
│  │  POST /api/backtest/run      - 执行回测                 ││
│  │  GET  /api/backtest/{id}     - 获取回测结果             ││
│  │  GET  /api/backtest/compare  - 多策略对比               ││
│  └─────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Backtest Engine (封装 Backtrader)                      ││
│  │  - data_feed.py    → PostgreSQL 数据适配                ││
│  │  - engine.py       → 回测执行引擎                       ││
│  │  - broker.py       → 券商模拟 (手续费/滑点)             ││
│  │  - analyzer.py     → 绩效分析器                         ││
│  │  - reporter.py     → 报告生成                           ││
│  └─────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────┐│
│  │  策略/因子引擎 (现有代码适配)                            ││
│  │  - strategies/ → Backtrader Strategy                    ││
│  │  - factors/    → Backtrader Indicator                   ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              ↕ SQLAlchemy
┌─────────────────────────────────────────────────────────────┐
│                   数据库 (PostgreSQL)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ stock_info  │  │ stock_daily │  │ backtest_results    │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│                                         (新增表)            │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 目录结构

```
projects/quant/src/backend/
├── backtest/                    # 新增回测模块
│   ├── __init__.py
│   ├── data_feed.py             # PostgreSQL 数据适配器
│   ├── engine.py                # 回测引擎封装
│   ├── broker.py                # 券商模拟配置
│   ├── analyzers/
│   │   ├── __init__.py
│   │   ├── performance.py       # 绩效分析器
│   │   └── drawdown.py          # 回撤分析器
│   └── reporter.py              # 报告生成
├── strategies/                  # 现有策略 (适配)
│   ├── base.py                  # 策略基类 → Backtrader Strategy
│   └── trend/ma_cross.py        # 示例策略
├── factors/                     # 现有因子 (适配)
│   ├── base.py                  # 因子基类 → Backtrader Indicator
│   └── technical/moving_avg.py  # 示例因子
├── api/
│   └── backtest.py              # 新增回测 API 路由
└── requirements.txt             # 添加 backtrader
```

---

## 三、数据流设计

### 3.1 回测执行流程

```
用户提交回测请求
      ↓
[POST /api/backtest/run]
      ↓
验证参数 (ts_code, start_date, end_date, strategy, params)
      ↓
从 stock_daily 加载 K 线数据 → Pandas DataFrame
      ↓
创建 Backtrader Cerebro 实例
      ↓
注入数据 (PostgresData Feed)
      ↓
注入策略 (动态加载策略类)
      ↓
配置 Broker (现金、手续费、滑点)
      ↓
添加分析器 (Sharpe, DrawDown, Returns)
      ↓
运行回测 cerebro.run()
      ↓
收集结果 (交易记录、绩效指标、资金曲线)
      ↓
存储到 backtest_results 表 (可选)
      ↓
返回 JSON 结果
```

### 3.2 数据结构

#### 请求参数
```json
{
  "ts_code": "000001.SZ",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "strategy": "ma_cross",
  "params": {
    "ma_fast": 5,
    "ma_slow": 10
  },
  "initial_cash": 1000000,
  "commission": 0.0003,
  "slippage": 0.002
}
```

#### 响应结果
```json
{
  "backtest_id": "bt_20260225_001",
  "status": "completed",
  "metrics": {
    "total_return": 0.235,
    "annual_return": 0.182,
    "sharpe_ratio": 1.45,
    "sortino_ratio": 1.82,
    "max_drawdown": -0.123,
    "win_rate": 0.62,
    "profit_factor": 2.1,
    "total_trades": 45,
    "winning_trades": 28,
    "losing_trades": 17,
    "avg_win": 0.034,
    "avg_loss": -0.018,
    "avg_holding_days": 5.2
  },
  "equity_curve": [
    {"date": "2024-01-01", "value": 1000000, "cash": 500000, "position": 500000},
    {"date": "2024-01-02", "value": 1023000, "cash": 520000, "position": 503000}
  ],
  "drawdown_curve": [
    {"date": "2024-01-01", "drawdown": 0},
    {"date": "2024-01-15", "drawdown": -0.05}
  ],
  "trades": [
    {
      "trade_id": 1,
      "entry_date": "2024-01-05",
      "exit_date": "2024-01-15",
      "direction": "long",
      "entry_price": 10.5,
      "exit_price": 11.2,
      "size": 50000,
      "pnl": 35000,
      "return": 0.067,
      "holding_days": 10,
      "exit_reason": "strategy_signal"
    }
  ],
  "signals": [
    {"date": "2024-01-05", "type": "buy", "price": 10.5, "reason": "MA5 crosses above MA10"},
    {"date": "2024-01-15", "type": "sell", "price": 11.2, "reason": "MA5 crosses below MA10"}
  ],
  "config": {
    "ts_code": "000001.SZ",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "strategy": "ma_cross",
    "initial_cash": 1000000
  }
}
```

---

## 四、核心模块设计

### 4.1 数据适配器 (`data_feed.py`)

```python
import backtrader as bt
import pandas as pd
from sqlalchemy import create_engine

class PostgresData(bt.feeds.PandasData):
    """从 PostgreSQL 加载股票数据"""
    
    params = (
        ('datetime', 'trade_date'),
        ('open', 'open'),
        ('high', 'high'),
        ('low', 'low'),
        ('close', 'close'),
        ('volume', 'vol'),
        ('openinterest', -1),  # 无持仓量
    )
    
    @classmethod
    def from_db(cls, ts_code: str, start_date: str, end_date: str):
        """
        从数据库加载数据
        
        Args:
            ts_code: 股票代码 (如 000001.SZ)
            start_date: 开始日期 (如 2024-01-01)
            end_date: 结束日期 (如 2024-12-31)
        
        Returns:
            PostgresData 实例
        """
        engine = create_engine('postgresql://postgres:postgres@localhost:5432/quant')
        query = """
            SELECT trade_date, open, high, low, close, vol
            FROM stock_daily
            WHERE ts_code = %s
            AND trade_date BETWEEN %s AND %s
            ORDER BY trade_date
        """
        df = pd.read_sql(query, engine, params=(ts_code, start_date, end_date))
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        df.set_index('trade_date', inplace=True)
        return cls(dataname=df)
```

### 4.2 策略适配器 (`strategies/base.py`)

```python
import backtrader as bt

class BaseStrategy(bt.Strategy):
    """策略基类 - 所有策略必须继承此类"""
    
    params = (
        ('name', 'base_strategy'),
        ('printlog', False),
    )
    
    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None
        self.buycomm = None
        
    def notify_order(self, order):
        """订单状态通知"""
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}, '
                        f'Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:
                self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}, '
                        f'Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
        self.order = None
        
    def notify_trade(self, trade):
        """交易完成通知"""
        if trade.isclosed:
            self.log(f'TRADE PROFIT, Gross: {trade.pnl:.2f}, Net: {trade.pnlcomm:.2f}')
            
    def log(self, txt, dt=None):
        """日志记录"""
        if self.params.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} {txt}')
```

### 4.3 回测引擎 (`engine.py`)

```python
import backtrader as bt
from datetime import datetime
from .data_feed import PostgresData
from .analyzers.performance import PerformanceAnalyzer
from .analyzers.drawdown import DrawDownAnalyzer

class BacktestEngine:
    """回测引擎封装"""
    
    def __init__(
        self,
        initial_cash: float = 1000000,
        commission: float = 0.0003,
        slippage: float = 0.002,
        stake: int = 1000
    ):
        """
        初始化回测引擎
        
        Args:
            initial_cash: 初始资金
            commission: 手续费率 (默认万分之三)
            slippage: 滑点 (默认 0.2%)
            stake: 每次交易股数
        """
        self.cerebro = bt.Cerebro()
        self.cerebro.broker.setcash(initial_cash)
        self.cerebro.broker.setcommission(commission=commission)
        self.cerebro.broker.set_slippage_perc(slippage)
        self.stake = stake
        
        # 添加分析器
        self.cerebro.addanalyzer(PerformanceAnalyzer, _name='performance')
        self.cerebro.addanalyzer(DrawDownAnalyzer, _name='drawdown')
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        self.cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        
    def add_data(self, ts_code: str, start_date: str, end_date: str):
        """添加股票数据"""
        data = PostgresData.from_db(ts_code, start_date, end_date)
        self.cerebro.adddata(data)
        self.ts_code = ts_code
        
    def add_strategy(self, strategy_cls, **params):
        """添加策略"""
        self.cerebro.addstrategy(strategy_cls, **params)
        
    def run(self) -> dict:
        """执行回测"""
        results = self.cerebro.run()
        strat = results[0]
        
        # 收集结果
        return {
            'initial_cash': self.cerebro.broker.startingcash,
            'final_value': self.cerebro.broker.getvalue(),
            'total_return': (self.cerebro.broker.getvalue() - self.cerebro.broker.startingcash) / self.cerebro.broker.startingcash,
            'sharpe_ratio': strat.analyzers.sharpe.get_analysis().get('sharperatio', None),
            'max_drawdown': strat.analyzers.drawdown.get_analysis()['max_drawdown'],
            'trades': self._extract_trades(strat),
            'equity_curve': self._extract_equity_curve(strat),
        }
        
    def _extract_trades(self, strat) -> list:
        """提取交易记录"""
        # 从观察器中提取
        trades = []
        for trade in strat.analyzers.trades.get_analysis():
            trades.append({
                'entry_date': trade.open.datetime,
                'exit_date': trade.close.datetime,
                'direction': 'long' if trade.size > 0 else 'short',
                'entry_price': trade.open.price,
                'exit_price': trade.close.price,
                'size': trade.size,
                'pnl': trade.pnl,
                'return': trade.pnl / (trade.open.price * trade.size),
            })
        return trades
        
    def _extract_equity_curve(self, strat) -> list:
        """提取资金曲线"""
        # 从观察器中提取
        equity = []
        for line in strat.observers.broker.getlines():
            equity.append({
                'date': line.datetime.date(),
                'value': line[0],
            })
        return equity
```

### 4.4 绩效分析器 (`analyzers/performance.py`)

```python
import backtrader as bt

class PerformanceAnalyzer(bt.Analyzer):
    """自定义绩效分析器"""
    
    def __init__(self):
        self.win_trades = 0
        self.loss_trades = 0
        self.total_pnl = 0
        self.gross_profit = 0
        self.gross_loss = 0
        
    def notify_trade(self, trade):
        if trade.isclosed:
            self.total_pnl += trade.pnl
            if trade.pnl > 0:
                self.win_trades += 1
                self.gross_profit += trade.pnl
            else:
                self.loss_trades += 1
                self.gross_loss += abs(trade.pnl)
                
    def get_analysis(self):
        total_trades = self.win_trades + self.loss_trades
        win_rate = self.win_trades / total_trades if total_trades > 0 else 0
        profit_factor = self.gross_profit / self.gross_loss if self.gross_loss > 0 else float('inf')
        
        return {
            'total_trades': total_trades,
            'winning_trades': self.win_trades,
            'losing_trades': self.loss_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'total_pnl': self.total_pnl,
        }
```

### 4.5 API 路由 (`api/backtest.py`)

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import date

router = APIRouter(prefix='/backtest', tags=['backtest'])

class BacktestRequest(BaseModel):
    ts_code: str
    start_date: str
    end_date: str
    strategy: str
    params: Optional[Dict[str, Any]] = {}
    initial_cash: float = 1000000
    commission: float = 0.0003
    slippage: float = 0.002

@router.post('/run')
async def run_backtest(request: BacktestRequest):
    """执行回测"""
    try:
        # 动态加载策略
        strategy_module = __import__(
            f'strategies.{request.strategy}',
            fromlist=['']
        )
        StrategyClass = getattr(strategy_module, request.strategy.title().replace('_', '') + 'Strategy')
        
        # 创建引擎
        engine = BacktestEngine(
            initial_cash=request.initial_cash,
            commission=request.commission,
            slippage=request.slippage
        )
        
        # 添加数据和策略
        engine.add_data(request.ts_code, request.start_date, request.end_date)
        engine.add_strategy(StrategyClass, **request.params)
        
        # 运行回测
        results = engine.run()
        
        return {
            'status': 'success',
            'data': results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/{backtest_id}')
async def get_backtest_result(backtest_id: str):
    """获取回测结果"""
    # TODO: 从数据库加载
    pass
```

---

## 五、前端设计

### 5.1 页面结构

```
src/frontend/src/pages/
└── Backtest/
    ├── index.jsx              # 回测主页面
    ├── components/
    │   ├── BacktestConfig.jsx # 回测配置表单
    │   ├── MetricsCard.jsx    # 绩效指标卡片
    │   ├── EquityChart.jsx    # 资金曲线图
    │   ├── DrawdownChart.jsx  # 回撤曲线图
    │   └── TradeLogTable.jsx  # 交易记录表格
    └── utils/
        └── formatters.js      # 数据格式化工具
```

### 5.2 回测配置表单

```jsx
function BacktestConfig({ onSubmit }) {
  const [config, setConfig] = useState({
    ts_code: '000001.SZ',
    start_date: '2024-01-01',
    end_date: '2024-12-31',
    strategy: 'ma_cross',
    initial_cash: 1000000,
    commission: 0.0003,
    slippage: 0.002,
    params: {
      ma_fast: 5,
      ma_slow: 10
    }
  });

  return (
    <form onSubmit={() => onSubmit(config)}>
      <Select label="股票" value={config.ts_code} onChange={...}>
        {/* 从 /api/stocks 加载 */}
      </Select>
      
      <DateRangePicker 
        start={config.start_date} 
        end={config.end_date}
      />
      
      <Select label="策略" value={config.strategy}>
        <Option value="ma_cross">均线交叉</Option>
        <Option value="break_out">突破策略</Option>
        <Option value="rsi_reversion">RSI 均值回归</Option>
      </Select>
      
      <InputGroup label="策略参数">
        <NumberInput label="快线周期" value={config.params.ma_fast} />
        <NumberInput label="慢线周期" value={config.params.ma_slow} />
      </InputGroup>
      
      <NumberInput label="初始资金" value={config.initial_cash} />
      <NumberInput label="手续费率" value={config.commission} step={0.0001} />
      <NumberInput label="滑点" value={config.slippage} step={0.001} />
      
      <Button type="submit">开始回测</Button>
    </form>
  );
}
```

### 5.3 绩效指标卡片

```jsx
function MetricsCard({ metrics }) {
  return (
    <div className="grid grid-cols-4 gap-4">
      <MetricCard 
        label="总收益率" 
        value={`${(metrics.total_return * 100).toFixed(2)}%`}
        trend={metrics.total_return > 0 ? 'up' : 'down'}
      />
      <MetricCard 
        label="年化收益" 
        value={`${(metrics.annual_return * 100).toFixed(2)}%`}
      />
      <MetricCard 
        label="夏普比率" 
        value={metrics.sharpe_ratio?.toFixed(2) || '-'}
        good={metrics.sharpe_ratio > 1}
      />
      <MetricCard 
        label="最大回撤" 
        value={`${(metrics.max_drawdown * 100).toFixed(2)}%`}
        trend="down"
      />
      <MetricCard 
        label="胜率" 
        value={`${(metrics.win_rate * 100).toFixed(1)}%`}
      />
      <MetricCard 
        label="盈亏比" 
        value={metrics.profit_factor?.toFixed(2) || '-'}
      />
      <MetricCard 
        label="总交易数" 
        value={metrics.total_trades}
      />
      <MetricCard 
        label="平均持仓天数" 
        value={metrics.avg_holding_days?.toFixed(1) || '-'}
      />
    </div>
  );
}
```

### 5.4 K 线 + 资金曲线图

```jsx
function BacktestChart({ klineData, signals, equityCurve }) {
  const chartRef = useRef(null);
  
  useEffect(() => {
    const chart = createChart(chartRef.current, { ... });
    
    // K 线
    const candleSeries = chart.addCandlestickSeries();
    candleSeries.setData(klineData);
    
    // 买卖信号
    const markers = signals.map(s => ({
      time: s.date,
      position: s.type === 'buy' ? 'belowBar' : 'aboveBar',
      color: s.type === 'buy' ? '#26a69a' : '#ef5350',
      shape: s.type === 'buy' ? 'arrowUp' : 'arrowDown',
      text: s.type === 'buy' ? 'BUY' : 'SELL',
    }));
    candleSeries.setMarkers(markers);
    
    // 资金曲线 (叠加)
    const equitySeries = chart.addLineSeries({
      color: '#fb8b24',
      lineWidth: 2,
      priceScaleId: 'right', // 右侧坐标轴
    });
    equitySeries.setData(equityCurve.map(e => ({
      time: e.date,
      value: e.value
    })));
    
    return () => chart.remove();
  }, [klineData, signals, equityCurve]);
  
  return <div ref={chartRef} style={{ height: '600px' }} />;
}
```

### 5.5 交易记录表格

```jsx
function TradeLogTable({ trades }) {
  return (
    <Table data={trades}>
      <Column field="entry_date" header="开仓日期" />
      <Column field="exit_date" header="平仓日期" />
      <Column field="direction" header="方向" 
        body={t => t.direction === 'long' ? '📈 多' : '📉 空'}
      />
      <Column field="entry_price" header="开仓价" />
      <Column field="exit_price" header="平仓价" />
      <Column field="size" header="数量" />
      <Column field="pnl" header="盈亏" 
        body={t => (
          <span className={t.pnl > 0 ? 'text-green' : 'text-red'}>
            {t.pnl > 0 ? '+' : ''}{t.pnl.toFixed(2)}
          </span>
        )}
      />
      <Column field="return" header="收益率" 
        body={t => `${(t.return * 100).toFixed(2)}%`}
      />
      <Column field="holding_days" header="持仓天数" />
    </Table>
  );
}
```

---

## 六、数据库设计

### 6.1 回测结果表

```sql
CREATE TABLE backtest_results (
    id SERIAL PRIMARY KEY,
    backtest_id VARCHAR(50) UNIQUE NOT NULL,
    ts_code VARCHAR(20) NOT NULL,
    strategy VARCHAR(50) NOT NULL,
    params JSONB,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    initial_cash DECIMAL(20, 2) NOT NULL,
    final_value DECIMAL(20, 2) NOT NULL,
    total_return DECIMAL(10, 6) NOT NULL,
    sharpe_ratio DECIMAL(10, 4),
    max_drawdown DECIMAL(10, 6),
    win_rate DECIMAL(10, 4),
    total_trades INTEGER,
    equity_curve JSONB,  -- 存储资金曲线数据
    trades JSONB,        -- 存储交易记录
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_backtest_ts_code ON backtest_results(ts_code);
CREATE INDEX idx_backtest_strategy ON backtest_results(strategy);
CREATE INDEX idx_backtest_created ON backtest_results(created_at);
```

---

## 七、实施计划

### Phase 1: 核心功能 (P0) - 预计 1 天

| 任务 | 文件 | 工时 |
|------|------|------|
| 安装 backtrader | requirements.txt | 10 min |
| 数据适配器 | backtest/data_feed.py | 30 min |
| 策略基类适配 | strategies/base.py | 30 min |
| 回测引擎封装 | backtest/engine.py | 1 hour |
| 绩效分析器 | backtest/analyzers/*.py | 1 hour |
| API 路由 | api/backtest.py | 30 min |
| 单元测试 | tests/test_backtest.py | 1 hour |

### Phase 2: 前端展示 (P0) - 预计 2 小时

| 任务 | 文件 | 工时 |
|------|------|------|
| 回测配置表单 | BacktestConfig.jsx | 30 min |
| 绩效指标卡片 | MetricsCard.jsx | 20 min |
| K 线 + 资金曲线 | BacktestChart.jsx | 40 min |
| 交易记录表格 | TradeLogTable.jsx | 30 min |

### Phase 3: 优化增强 (P1/P2) - 预计 1 天

| 任务 | 工时 |
|------|------|
| 回测结果持久化 | 1 hour |
| 多策略对比 | 2 hours |
| 参数网格搜索 | 2 hours |
| 导出报告 (PDF/Excel) | 2 hours |
| 实盘对接预留接口 | 1 hour |

**总计：约 1.5 天**

---

## 八、风险与注意事项

### 技术风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| Backtrader 学习曲线 | 中 | 先实现简单策略，逐步复杂化 |
| 数据量大导致回测慢 | 中 | 支持数据采样、分段回测 |
| 复权数据处理 | 高 | 需要确认 stock_daily 是否包含复权数据 |
| 停牌股票处理 | 中 | Backtrader 默认跳过无数据日期 |

### 业务风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 回测过拟合 | 高 | 支持样本外测试、交叉验证 |
| 手续费/滑点设置不合理 | 中 | 提供默认值，允许用户调整 |
| 未来函数 | 高 | 代码审查，确保策略不使用未来数据 |

---

## 九、验收标准

### 功能验收

- [ ] 能够成功运行单只股票回测
- [ ] 绩效指标计算正确 (与手工计算对比)
- [ ] 买卖信号在 K 线图上正确显示
- [ ] 资金曲线与交易记录一致
- [ ] API 响应时间 < 10 秒 (1 年数据)

### 性能验收

- [ ] 回测 1 年日线数据 < 5 秒
- [ ] 前端图表渲染 < 1 秒
- [ ] 支持并发 5 个回测任务

### 用户体验验收

- [ ] 配置表单直观易用
- [ ] 绩效指标有 tooltip 解释
- [ ] 交易记录支持排序/筛选
- [ ] 支持导出回测报告

---

## 十、后续扩展

1. **多标的组合回测** - 支持一篮子股票同时回测
2. **实时回测** - 接入实时行情，模拟盘中回测
3. **策略市场** - 用户上传/分享策略
4. **机器学习** - 集成 ML 模型预测
5. **实盘对接** - 对接券商 API 实盘交易

---

**评审人**: _____________  
**评审日期**: _____________  
**评审意见**: _____________
