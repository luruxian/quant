# 量化交易系统 - 技术文档

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         前端 (React)                            │
│                   localhost:5173                               │
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│  │ 股票选择器  │───►│  K线图表   │───►│  交易信号标记       │ │
│  └─────────────┘    └─────────────┘    └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ HTTP API
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      后端 API (FastAPI)                         │
│                   localhost:8000                               │
│                                                                 │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐│
│  │ Stock API   │  │ Factor API   │  │  Strategy API          ││
│  │ /api/stock  │  │ /api/factors │  │  /api/strategies      ││
│  └─────────────┘  └──────────────┘  └────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         数据层                                  │
│                  PostgreSQL (localhost:5432)                     │
│                                                                 │
│  ┌────────────┐ ┌────────────┐ ┌──────────┐ ┌──────────────┐  │
│  │ stock_info │ │stock_daily │ │factor_ma │ │   signal     │  │
│  └────────────┘ └────────────┘ └──────────┘ └──────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 核心模块

### 1. 数据层 (Data Layer)

**数据库表**:
| 表名 | 说明 |
|------|------|
| `stock_info` | 股票基本信息 (5485只) |
| `stock_daily` | 个股日线行情 (OHLCV) |
| `index_daily` | 指数日线行情 |
| `factor_ma` | 技术因子 (MA/EMA/MACD) |
| `signal` | 交易信号 |
| `position` | 持仓记录 |
| `backtest_result` | 回测结果 |

### 2. 因子层 (Factor Layer)

**位置**: `src/backend/factors/`

```
factors/
├── __init__.py          # 因子注册表
├── base.py              # 因子基类 (Factor)
├── technical/           # 技术因子
│   ├── moving_avg.py    # MA, EMA
│   ├── momentum.py     # MACD, RSI, CCI
│   ├── volatility.py   # Bollinger Bands, ATR
│   └── volume.py       # OBV, VWAP
└── statistical/        # 统计因子
    └── statistical.py  # Z-Score, Correlation
```

**已实现因子 (16个)**:

| 类别 | 因子 | 说明 |
|------|------|------|
| 趋势 | `ma` | 简单移动平均 |
| 趋势 | `ema` | 指数移动平均 |
| 趋势 | `macd` | MACD 指标 |
| 动量 | `rsi` | 相对强弱指标 |
| 动量 | `cci` | 商品通道指数 |
| 波动率 | `bb` | 布林带 |
| 波动率 | `atr` | 平均真实波幅 |
| 波动率 | `std` | 标准差 |
| 价量 | `obv` | 能量潮 |
| 价量 | `vwap` | 成交量加权均价 |
| 价量 | `volume_ratio` | 量比 |
| 价量 | `turnover` | 换手率 |
| 统计 | `zscore` | Z-Score 标准化 |
| 统计 | `correlation` | 相关系数 |
| 统计 | `skewness` | 偏度 |
| 统计 | `kurtosis` | 峰度 |

**使用方式**:
```python
from factors import FACTOR_REGISTRY, get_factor

# 获取因子
factor = get_factor('ma')

# 计算因子
result = factor.compute(price_data)
```

### 3. 策略层 (Strategy Layer)

**位置**: `src/backend/strategies/`

```
strategies/
├── __init__.py          # 策略注册表
├── base.py              # 策略基类 (Strategy, Signal)
├── trend/               # 趋势策略
│   ├── ma_cross.py     # 均线交叉策略
│   └── break_out.py    # 突破策略
└── mean_reversion/     # 均值回归策略
    └── rsi_reversion.py
```

**已实现策略 (11个)**:

| 类别 | 策略名 | 说明 |
|------|--------|------|
| 趋势 | `ma_cross_5_20` | 5日/20日均线交叉 |
| 趋势 | `ma_cross_10_60` | 10日/60日均线交叉 |
| 趋势 | `ma_cross_5_10` | 5日/10日均线交叉 |
| 趋势 | `dual_ma_cross` | 双周期均线交叉 |
| 趋势 | `breakout_20` | 20日高点突破 |
| out_60`趋势 | `break | 60日高点突破 |
| 趋势 | `channel_breakout` | 布林带通道突破 |
| 均值回归 | `rsi_reversal_14` | RSI 超买超卖 |
| 均值回归 | `rsi_reversal_6` | 6日 RSI |
| 均值回归 | `bb_reversal_20` | 布林带回归 |
| 均值回归 | `mean_reversion_20` | Z-Score 回归 |

**策略接口**:
```python
from strategies.base import Strategy, Signal, Direction, SignalType

class MyStrategy(Strategy):
    @property
    def name(self) -> str:
        return "my_strategy"
    
    def generate_signals(self, prices, factors) -> List[Signal]:
        # 生成信号逻辑
        return signals
```

### 4. 执行引擎 (Engine)

**因子引擎** (`engine/factor_engine.py`):
- 从数据库获取行情数据
- 计算因子值
- 保存到数据库

**策略引擎** (`engine/strategy_engine.py`):
- 获取价格和因子数据
- 运行策略生成信号
- 可选保存到数据库

### 5. API 层

| 接口 | 说明 | 示例 |
|------|------|------|
| `GET /api/stocks` | 股票列表 | |
| `GET /api/stock/{ts_code}` | K线数据 | `/api/stock/000001.SZ` |
| `GET /api/indicators/{ts_code}` | 均线数据 | `/api/indicators/000001.SZ?ma=ma5,ma20` |
| `GET /api/factors` | 因子列表 | |
| `GET /api/factors/{ts_code}` | 因子数据 | `/api/factors/000001.SZ?names=ma,rsi` |
| `GET /api/strategies` | 策略列表 | |
| `GET /api/strategies/{name}` | 策略详情 | |
| `GET /api/signals/{ts_code}` | 交易信号 | `/api/signals/000001.SZ?strategy=ma_cross_5_20` |
| `POST /api/signals/{ts_code}/run` | 运行策略 | |

## 数据流向

```
1. 数据获取
   akshare/tushare ──► stock_daily ──► factor_ma

2. 因子计算
   stock_daily ──► Factor.compute() ──► factor_ma

3. 信号生成
   stock_daily + factor_ma ──► Strategy.generate_signals() ──► signal

4. 可视化
   前端 ──► /api/stock/{} ──► K线图
   前端 ──► /api/signals/{} ──► 信号标记
```

## 启动方式

```bash
# 后端
cd src/backend
python3 -m uvicorn app:app --host 0.0.0.0 --port 8000

# 前端
cd src/frontend
npm run dev
```

## 扩展系统

### 添加新因子
1. 在 `factors/technical/` 或 `factors/statistical/` 创建因子类
2. 继承 `Factor` 基类
3. 实现 `compute()` 方法
4. 在 `factors/__init__.py` 注册

### 添加新策略
1. 在 `strategies/trend/` 或 `strategies/mean_reversion/` 创建策略类
2. 继承 `Strategy` 基类
3. 实现 `generate_signals()` 方法
4. 在 `strategies/__init__.py` 注册

## 项目结构

```
quant/
├── src/
│   ├── backend/
│   │   ├── app.py              # FastAPI 应用
│   │   ├── api/                # API 路由
│   │   │   ├── stock.py
│   │   │   └── factors_strategies.py
│   │   ├── factors/            # 因子层
│   │   ├── strategies/         # 策略层
│   │   ├── engine/             # 执行引擎
│   │   ├── services/           # 数据服务
│   │   └── utils/              # 工具
│   └── frontend/               # React 前端
│       └── src/
│           ├── components/     # K线图组件
│           └── api/            # API 调用
├── docs/                       # 设计文档
└── tests/                      # 单元测试
```
