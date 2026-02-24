# A股趋势策略量化交易系统 - MVP方案

## 1. 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      数据层                                  │
├─────────────────────────────────────────────────────────────┤
│  tushare / akshare  ──>  数据采集服务  ──>  PostgreSQL     │
│                                          (行情/因子/持仓)   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      策略层                                  │
├─────────────────────────────────────────────────────────────┤
│  趋势策略 (MA/EMA)  ──>  信号生成  ──>  交易信号           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      执行层                                  │
├─────────────────────────────────────────────────────────────┤
│  券商API (模拟/实盘)  ──>  订单管理  ──>  持仓管理         │
└─────────────────────────────────────────────────────────────┘
```

## 2. 数据库设计

### 2.1 表结构

```sql
-- 行情数据（日线）
CREATE TABLE daily_price (
    id SERIAL PRIMARY KEY,
    ts_code VARCHAR(20) NOT NULL,  -- 股票代码 (e.g. 000001.SZ)
    trade_date DATE NOT NULL,
    open DECIMAL(10, 2),
    high DECIMAL(10, 2),
    low DECIMAL(10, 2),
    close DECIMAL(10, 2),
    volume DECIMAL(20, 2),
    amount DECIMAL(20, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ts_code, trade_date)
);

-- 因子数据
CREATE TABLE factors (
    id SERIAL PRIMARY KEY,
    ts_code VARCHAR(20) NOT NULL,
    trade_date DATE NOT NULL,
    ma5 DECIMAL(10, 2),
    ma10 DECIMAL(10, 2),
    ma20 DECIMAL(10, 2),
    ma60 DECIMAL(10, 2),
    ema12 DECIMAL(10, 2),
    ema26 DECIMAL(10, 2),
    atr DECIMAL(10, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ts_code, trade_date)
);

-- 交易信号
CREATE TABLE signals (
    id SERIAL PRIMARY KEY,
    ts_code VARCHAR(20) NOT NULL,
    trade_date DATE NOT NULL,
    direction VARCHAR(10) NOT NULL,  -- 'LONG', 'SHORT', 'EXIT'
    price DECIMAL(10, 2),
    strength DECIMAL(5, 4),  -- 信号强度 0-1
    strategy VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 持仓记录
CREATE TABLE positions (
    id SERIAL PRIMARY KEY,
    ts_code VARCHAR(20) NOT NULL,
    direction VARCHAR(10) NOT NULL,  -- 'LONG', 'SHORT'
    quantity INTEGER NOT NULL,
    entry_price DECIMAL(10, 2),
    entry_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'OPEN',  -- 'OPEN', 'CLOSED'
    pnl DECIMAL(10, 2),  -- 盈亏
    closed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 回测结果
CREATE TABLE backtest_results (
    id SERIAL PRIMARY KEY,
    strategy_name VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_return DECIMAL(10, 4),
    sharpe_ratio DECIMAL(10, 4),
    max_drawdown DECIMAL(10, 4),
    win_rate DECIMAL(10, 4),
    params JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 3. 项目结构

```
quant/
├── configs/
│   ├── config.yaml          # 主配置
│   ├── database.yaml        # 数据库配置
│   └── strategies.yaml     # 策略参数
├── data/
│   ├── raw/                # 原始数据
│   └── processed/          # 处理后数据
├── src/
│   ├── __init__.py
│   ├── main.py             # 入口
│   ├── config.py           # 配置加载
│   ├── database.py         # 数据库连接
│   ├── data_fetcher/      # 数据获取
│   │   ├── __init__.py
│   │   ├── tushare_client.py
│   │   └── akshare_client.py
│   ├── processors/         # 数据处理
│   │   ├── __init__.py
│   │   ├── cleaner.py
│   │   └── factor_calculator.py
│   ├── strategies/         # 策略
│   │   ├── __init__.py
│   │   └── trend_strategy.py
│   ├── backtest/           # 回测
│   │   ├── __init__.py
│   │   └── engine.py
│   └── execution/          # 执行
│       ├── __init__.py
│       └── simulator.py    # 模拟交易
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_factor_analysis.ipynb
│   └── 03_backtest.ipynb
├── logs/
└── requirements.txt
```

## 4. MVP 实现步骤

### 步骤1: 环境搭建
- 安装依赖
- 配置数据库连接

### 步骤2: 数据采集
- tushare/akshare 获取日线数据
- 自动存入 PostgreSQL

### 步骤3: 因子计算
- 计算 MA/EMA 均线
- 计算 ATR 波动率

### 步骤4: 趋势策略实现
- 策略逻辑：MA20 上穿 MA60 -> 多头入场
- 回测验证

### 步骤5: 信号生成与模拟交易
- 每日生成交易信号
- 模拟下单与持仓管理

## 5. 趋势策略逻辑 (MVP)

```python
# 伪代码
def generate_signal(df):
    """
    双均线交叉策略
    - 金叉 (MA20 > MA60): 买入信号 LONG死叉 (MA20 < MA60
    - ): 卖出信号 EXIT
    """
    if df['ma20'] > df['ma60'] and df['ma20_prev'] <= df['ma60_prev']:
        return 'LONG'
    elif df['ma20'] < df['ma60'] and df['ma20_prev'] >= df['ma60_prev']:
        return 'EXIT'
    return None
```

## 6. 依赖

```txt
pandas
numpy
psycopg2-binary
sqlalchemy
tushare
akshare
pyyaml
jupyter
```

## 7. 下一步

1. 确认方案
2. 创建数据库表
3. 开始代码实现

---

*Created: 2026-02-24*
