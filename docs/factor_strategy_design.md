# 因子层 & 策略层设计方案

## 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                      可视化层 (React)                         │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │ JSON API
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Layer (FastAPI)                     │
│  - /factors/*    因子数据查询                                 │
│  - /signals/*    信号数据查询                                │
│  - /backtest/*   回测结果                                   │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   因子层        │    │   策略层        │    │   数据层        │
│   Factor       │◄──►│   Strategy     │◄──►│   Data         │
│                 │    │                 │    │                 │
│ - 技术因子       │    │ - 信号生成      │    │ - stock_daily  │
│ - 价量因子       │    │ - 仓位管理      │    │ - index_daily  │
│ - 统计因子       │    │ - 风险控制      │    │ - factor_ma    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 核心原则

### 低耦合设计
1. **因子层** ↔ **策略层** 通过标准接口通信
2. 因子不知道策略的存在
3. 策略不知道数据从哪里来
4. 两者都可以独立测试和扩展

---

## 1. 因子层 (Factor Layer)

### 职责
- 纯数学计算，不包含交易逻辑
- 输入: 原始行情数据 (OHLCV)
- 输出: 因子值

### 因子分类

```
factors/
├── technical/          # 技术因子
│   ├── moving_avg.py   # MA, EMA
│   ├── momentum.py    # MACD, RSI, CCI
│   ├── volatility.py  # ATR, Bollinger
│   └── volume.py      # OBV, VWAP
│
├── statistical/        # 统计因子
│   ├── regression.py   # 线性回归
│   ├── zscore.py      # Z-Score
│   └── correlation.py # 相关系数
│
└── alpha/              # Alpha因子 (可选)
    ├── fundamentals.py # 市值, 市盈率
    └── alternative.py  # 另类数据
```

### 因子计算示例

```python
# factors/technical/moving_avg.py
class MovingAverage:
    """移动平均因子 - 纯计算，无交易逻辑"""
    
    def __init__(self, windows: list[int] = [5, 10, 20, 60]):
        self.windows = windows
    
    def compute(self, prices: pd.Series) -> pd.DataFrame:
        """计算MA
        
        Args:
            prices: 收盘价序列
            
        Returns:
            DataFrame with columns: ma5, ma10, ma20, ma60
        """
        result = {}
        for w in self.windows:
            if len(prices) >= w:
                result[f'ma{w}'] = prices.rolling(w).mean()
        return pd.DataFrame(result)
    
    def compute_ema(self, prices: pd.Series) -> pd.DataFrame:
        """计算EMA"""
        result = {}
        for w in self.windows:
            if len(prices) >= w:
                result[f'ema{w}'] = prices.ewm(span=w).mean()
        return pd.DataFrame(result)
```

### 因子注册机制

```python
# factors/__init__.py
from abc import ABC, abstractmethod

class Factor(ABC):
    """因子基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @abstractmethod
    def compute(self, data: pd.DataFrame) -> pd.DataFrame:
        pass

# 注册表
FACTOR_REGISTRY: dict[str, Factor] = {}

def register(name: str):
    """因子注册装饰器"""
    def decorator(cls):
        FACTOR_REGISTRY[name] = cls()
        return cls
    return decorator
```

---

## 2. 策略层 (Strategy Layer)

### 职责
- 消费因子数据
- 生成交易信号
- 不关心因子如何计算

### 策略分类

```
strategies/
├── trend/              # 趋势策略
│   ├── ma_cross.py     # 均线交叉
│   └── break_out.py   # 突破策略
│
├── mean_reversion/     # 均值回归
│   ├── bollinger.py   # 布林带
│   └── rsi_reversion.py # RSI回归
│
└── composite/          # 复合策略
    └── dual_thrust.py # Dual Thrust
```

### 策略接口

```python
# strategies/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

class Direction(Enum):
    LONG = "long"
    SHORT = "short"
    FLAT = "flat"

@dataclass
class Signal:
    """交易信号"""
    ts_code: str
    trade_date: str
    direction: Direction
    strength: float  # 0-1 信号强度
    price: float     # 信号价格
    reason: str      # 信号原因

class Strategy(ABC):
    """策略基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @abstractmethod
    def generate_signals(
        self, 
        factors: pd.DataFrame,
        prices: pd.DataFrame
    ) -> list[Signal]:
        """生成信号
        
        Args:
            factors: 因子数据 (由因子层提供)
            prices: 价格数据
            
        Returns:
            Signal列表
        """
        pass
```

### 策略示例 - 均线交叉

```python
# strategies/trend/ma_cross.py
from strategies.base import Strategy, Signal, Direction

class MACrossStrategy(Strategy):
    """均线交叉策略"""
    
    def __init__(self, fast: int = 5, slow: int = 20):
        self.fast = fast
        self.slow = slow
    
    @property
    def name(self) -> str:
        return f"MA{self.fast}_{self.slow}_Cross"
    
    def generate_signals(self, factors: pd.DataFrame, prices: pd.DataFrame) -> list[Signal]:
        signals = []
        
        # 获取MA值 (不关心MA如何计算)
        fast_ma = factors.get(f'ma{self.fast}')
        slow_ma = factors.get(f'ma{self.slow}')
        
        if fast_ma is None or slow_ma is None:
            return signals
        
        # 交叉检测
        for i in range(1, len(fast_ma)):
            if pd.notna(fast_ma.iloc[i]) and pd.notna(slow_ma.iloc[i]):
                # 金叉: 快线从下穿过慢线
                if fast_ma.iloc[i-1] <= slow_ma.iloc[i-1] and fast_ma.iloc[i] > slow_ma.iloc[i]:
                    signals.append(Signal(
                        ts_code=prices['ts_code'].iloc[i],
                        trade_date=str(prices['trade_date'].iloc[i]),
                        direction=Direction.LONG,
                        strength=1.0,
                        price=prices['close'].iloc[i],
                        reason=f"MA{self.fast} crosses above MA{self.slow}"
                    ))
                # 死叉: 快线从上穿过慢线
                elif fast_ma.iloc[i-1] >= slow_ma.iloc[i-1] and fast_ma.iloc[i] < slow_ma.iloc[i]:
                    signals.append(Signal(
                        ts_code=prices['ts_code'].iloc[i],
                        trade_date=str(prices['trade_date'].iloc[i]),
                        direction=Direction.FLAT,
                        strength=1.0,
                        price=prices['close'].iloc[i],
                        reason=f"MA{self.fast} crosses below MA{self.slow}"
                    ))
        
        return signals
```

---

## 3. 因子计算引擎

### 调度器

```python
# engine/scheduler.py
class FactorScheduler:
    """因子计算调度器"""
    
    def __init__(self, db_pool):
        self.db = db_pool
    
    def run_daily_factors(self, trade_date: str):
        """每日批量计算因子"""
        
        # 1. 获取需要计算的股票列表
        stocks = self.get_active_stocks()
        
        # 2. 获取原始行情数据
        prices = self.get_price_data(stocks, trade_date)
        
        # 3. 计算所有注册的因子
        for ts_code, df in prices.items():
            for name, factor in FACTOR_REGISTRY.items():
                try:
                    result = factor.compute(df)
                    self.save_factors(ts_code, trade_date, result)
                except Exception as e:
                    print(f"Factor {name} failed for {ts_code}: {e}")
    
    def get_active_stocks(self) -> list[str]:
        """获取活跃股票列表"""
        # 从数据库查询
        pass
    
    def get_price_data(self, stocks: list[str], date: str) -> dict:
        """获取行情数据"""
        # 从数据库查询
        pass
```

---

## 4. 信号执行引擎

```python
# engine/signals.py
class SignalEngine:
    """信号执行引擎"""
    
    def __init__(self, db_pool):
        self.db = db_pool
    
    def run_strategies(self, trade_date: str):
        """运行所有策略生成信号"""
        
        # 1. 获取因子数据
        factors = self.get_factors(trade_date)
        
        # 2. 获取价格数据
        prices = self.get_prices(trade_date)
        
        # 3. 运行每个策略
        for strategy in STRATEGY_REGISTRY.values():
            signals = strategy.generate_signals(factors, prices)
            
            # 4. 保存信号到数据库
            self.save_signals(signals)
    
    def get_factors(self, date: str) -> pd.DataFrame:
        """获取因子数据"""
        pass
```

---

## 5. 数据库扩展

### 新增因子表

```sql
-- 因子数据表
CREATE TABLE factor_values (
    id BIGSERIAL PRIMARY KEY,
    ts_code VARCHAR(20),
    trade_date DATE,
    factor_name VARCHAR(50),    -- 因子名称
    factor_value NUMERIC,       -- 因子值
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(ts_code, trade_date, factor_name)
);

-- 策略配置表
CREATE TABLE strategy_config (
    id BIGSERIAL PRIMARY KEY,
    strategy_name VARCHAR(50) UNIQUE,
    enabled BOOLEAN DEFAULT true,
    params JSONB,               -- 策略参数
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 信号表 (扩展)
ALTER TABLE signal ADD COLUMN strategy_id INTEGER REFERENCES strategy_config(id);
ALTER TABLE signal ADD COLUMN strength NUMERIC DEFAULT 1.0);
```

---

## 6. API 扩展

```python
# api/factors.py
@router.get("/factors/{ts_code}")
def get_factors(
    ts_code: str,
    start_date: str = None,
    end_date: str = None,
    factors: str = "ma5,ma10,ma20"  # 逗号分隔
):
    """获取因子数据"""
    pass

# api/strategies.py
@router.get("/strategies")
def list_strategies():
    """列出所有策略"""
    pass

@router.post("/strategies/{name}/run")
def run_strategy(name: str, trade_date: str):
    """运行指定策略"""
    pass

@router.get("/signals/{ts_code}")
def get_signals(
    ts_code: str,
    strategy: str = None,  # 按策略过滤
    start_date: str = None,
    end_date: str = None
):
    """获取交易信号"""
    pass
```

---

## 目录结构 (最终)

```
quant/
├── src/
│   ├── backend/
│   │   ├── app.py
│   │   ├── api/
│   │   │   ├── factors.py      # 因子API
│   │   │   ├── strategies.py   # 策略API
│   │   │   └── signals.py       # 信号API
│   │   ├── factors/            # 因子层
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── technical/
│   │   │   │   ├── moving_avg.py
│   │   │   │   ├── momentum.py
│   │   │   │   └── volatility.py
│   │   │   └── statistical/
│   │   │       ├── zscore.py
│   │   │       └── correlation.py
│   │   ├── strategies/          # 策略层
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── trend/
│   │   │   │   ├── ma_cross.py
│   │   │   │   └── break_out.py
│   │   │   └── mean_reversion/
│   │   │       ├── bollinger.py
│   │   │       └── rsi_reversion.py
│   │   ├── engine/             # 执行引擎
│   │   │   ├── scheduler.py    # 因子调度
│   │   │   └── signals.py       # 信号生成
│   │   ├── services/
│   │   └── utils/
│   │
│   └── frontend/
│
├── docs/
│   ├── factor_design.md         # 因子层设计
│   └── strategy_design.md       # 策略层设计
│
└── tests/
    ├── factors/
    └── strategies/
```

---

## 下一步

1. 确认方案
2. 先实现因子层 (technical factors)
3. 再实现策略层 (MA cross策略作为MVP)
4. 最后集成API

有问题或需要调整的地方吗？
