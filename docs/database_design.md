# 数据库表设计方案 (更新版)

## 数据源说明

| 数据类型 | 数据源 | 说明 |
|---------|--------|------|
| 股票基本信息 | tushare `stock_basic` | 需token，但权限有限 |
| 个股日线数据 | akshare `stock_zh_a_hist` | 免费，无需token |
| 指数日线数据 | akshare `stock_zh_index_daily` | 免费，无需token |

---

## 表结构设计

### 1. 股票基本信息表 (stock_info)

**来源**: tushare `stock_basic`

```sql
CREATE TABLE stock_info (
    id BIGSERIAL PRIMARY KEY,
    
    -- 股票代码 (主键)
    ts_code VARCHAR(20) NOT NULL UNIQUE,
    symbol VARCHAR(10),                    -- 股票代码 (如 000001)
    name VARCHAR(100) NOT NULL,             -- 股票名称
    
    -- 市场与板块
    market VARCHAR(20),                    -- 市场 (主板/创业板/科创板/北交所)
    area VARCHAR(50),                      -- 所属地区
    industry VARCHAR(100),                 -- 所属行业
    industry分类 VARCHAR(50),              -- 行业分类
    
    -- 上市信息
    list_date DATE,                        -- 上市日期
    delist_date DATE,                      -- 退市日期
    is_hs VARCHAR(1),                      -- 是否沪深港通 (N/0/1/2)
    
    -- 状态
    status VARCHAR(20) DEFAULT 'ACTIVE',  -- 状态: ACTIVE/DELISTED
    source VARCHAR(20) DEFAULT 'TUSHARE',   -- 数据来源
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_stock_info_ts_code ON stock_info(ts_code);
CREATE INDEX idx_stock_info_name ON stock_info(name);
CREATE INDEX idx_stock_info_market ON stock_info(market);
CREATE INDEX idx_stock_info_industry ON stock_info(industry);
```

---

### 2. 个股日线行情表 (stock_daily)

**来源**: akshare `stock_zh_a_hist`

| akshare字段 | 数据库字段 | 类型 | 说明 |
|------------|-----------|------|------|
| 日期 | trade_date | DATE | 交易日期 |
| 股票代码 | ts_code | VARCHAR(20) | 股票代码 |
| 开盘 | open | DECIMAL(12, 2) | 开盘价 |
| 收盘 | close | DECIMAL(12, 2) | 收盘价 |
| 最高 | high | DECIMAL(12, 2) | 最高价 |
| 最低 | low | DECIMAL(12, 2) | 最低价 |
| 成交量 | volume | BIGINT | 成交量 (手) |
| 成交额 | amount | DECIMAL(20, 2) | 成交额 (元) |
| 振幅 | amplitude | DECIMAL(10, 4) | 振幅 (%) |
| 涨跌幅 | pct_chg | DECIMAL(10, 4) | 涨跌幅 (%) |
| 涨跌额 | change | DECIMAL(12, 4) | 涨跌额 (元) |
| 换手率 | turnover_rate | DECIMAL(10, 4) | 换手率 (%) |

```sql
CREATE TABLE stock_daily (
    id BIGSERIAL PRIMARY KEY,
    
    ts_code VARCHAR(20) NOT NULL,           -- 股票代码
    trade_date DATE NOT NULL,              -- 交易日期
    
    -- 价格数据
    open DECIMAL(12, 2),                  -- 开盘价
    close DECIMAL(12, 2),                  -- 收盘价
    high DECIMAL(12, 2),                  -- 最高价
    low DECIMAL(12, 2),                   -- 最低价
    
    -- 量价数据
    volume BIGINT,                        -- 成交量 (手)
    amount DECIMAL(20, 2),                -- 成交额 (元)
    
    -- 衍生指标
    amplitude DECIMAL(10, 4),             -- 振幅 (%)
    pct_chg DECIMAL(10, 4),               -- 涨跌幅 (%)
    change DECIMAL(12, 4),                -- 涨跌额 (元)
    turnover_rate DECIMAL(10, 4),         -- 换手率 (%)
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(ts_code, trade_date)
);

CREATE INDEX idx_stock_daily_ts_code ON stock_daily(ts_code);
CREATE INDEX idx_stock_daily_trade_date ON stock_daily(trade_date);
CREATE INDEX idx_stock_daily_ts_date ON stock_daily(ts_code, trade_date DESC);
```

---

### 3. 指数日线行情表 (index_daily)

**来源**: akshare `stock_zh_index_daily`

| akshare字段 | 数据库字段 | 类型 | 说明 |
|------------|-----------|------|------|
| date | trade_date | DATE | 交易日期 |
| open | open | DECIMAL(12, 2) | 开盘点位 |
| high | high | DECIMAL(12, 2) | 最高点位 |
| low | low | DECIMAL(12, 2) | 最低点位 |
| close | close | DECIMAL(12, 2) | 收盘点位 |
| volume | volume | BIGINT | 成交量 (元) |

```sql
CREATE TABLE index_daily (
    id BIGSERIAL PRIMARY KEY,
    
    ts_code VARCHAR(20) NOT NULL,           -- 指数代码 (如 000001.SH)
    trade_date DATE NOT NULL,              -- 交易日期
    
    -- 价格数据
    open DECIMAL(16, 2),                  -- 开盘点位
    high DECIMAL(16, 2),                  -- 最高点位
    low DECIMAL(16, 2),                   -- 最低点位
    close DECIMAL(16, 2),                 -- 收盘点位
    
    volume BIGINT,                        -- 成交量 (元)
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(ts_code, trade_date)
);

CREATE INDEX idx_index_daily_ts_code ON index_daily(ts_code);
CREATE INDEX idx_index_daily_trade_date ON index_daily(trade_date DESC);
```

---

### 4. 均线因子表 (factor_ma)

**计算来源**: 基于 stock_daily.close 计算

```sql
CREATE TABLE factor_ma (
    id BIGSERIAL PRIMARY KEY,
    
    ts_code VARCHAR(20) NOT NULL,
    trade_date DATE NOT NULL,
    
    -- 简单移动平均线
    ma5 DECIMAL(12, 4),                   -- 5日均线
    ma10 DECIMAL(12, 4),                  -- 10日均线
    ma20 DECIMAL(12, 4),                  -- 20日均线
    ma30 DECIMAL(12, 4),                  -- 30日均线
    ma60 DECIMAL(12, 4),                  -- 60日均线
    ma120 DECIMAL(12, 4),                 -- 120日均线
    ma250 DECIMAL(12, 4),                 -- 250日均线
    
    -- 指数移动平均线
    ema12 DECIMAL(12, 4),                 -- EMA12
    ema26 DECIMAL(12, 4),                 -- EMA26
    
    -- MACD
    macd DECIMAL(12, 6),                  -- DIF (快线)
    macd_signal DECIMAL(12, 6),           -- DEA (信号线)
    macd_hist DECIMAL(12, 6),              -- MACD柱状图
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(ts_code, trade_date)
);

CREATE INDEX idx_factor_ma_ts_date ON factor_ma(ts_code, trade_date DESC);
```

---

### 5. 交易信号表 (signal)

```sql
CREATE TABLE signal (
    id BIGSERIAL PRIMARY KEY,
    
    ts_code VARCHAR(20) NOT NULL,
    trade_date DATE NOT NULL,
    
    strategy VARCHAR(50) NOT NULL,         -- 策略名称
    direction VARCHAR(10) NOT NULL,        -- 信号方向: LONG/SHORT/EXIT
    
    price DECIMAL(12, 2),                 -- 信号价格
    strength DECIMAL(5, 4),               -- 信号强度 (0-1)
    
    reason TEXT,                          -- 信号原因
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_signal_ts_date ON signal(ts_code, trade_date DESC);
CREATE INDEX idx_signal_strategy ON signal(strategy);
```

---

### 6. 持仓记录表 (position)

```sql
CREATE TABLE position (
    id BIGSERIAL PRIMARY KEY,
    
    ts_code VARCHAR(20) NOT NULL,
    direction VARCHAR(10) NOT NULL,        -- 持仓方向: LONG/SHORT
    
    quantity INTEGER NOT NULL DEFAULT 0,   -- 持仓数量 (股)
    
    entry_price DECIMAL(12, 2),          -- 入场价格
    entry_date DATE NOT NULL,             -- 入场日期
    
    exit_price DECIMAL(12, 2),            -- 出场价格
    exit_date DATE,                       -- 出场日期
    
    status VARCHAR(20) DEFAULT 'OPEN',   -- 状态: OPEN/CLOSED
    
    pnl DECIMAL(14, 2),                  -- 盈亏金额
    pnl_pct DECIMAL(10, 4),             -- 盈亏比例 (%)
    
    commission DECIMAL(12, 2) DEFAULT 0, -- 手续费
    slippage DECIMAL(12, 2) DEFAULT 0,  -- 滑点
    
    signal_id BIGINT,                     -- 对应信号ID
    strategy VARCHAR(50),                -- 策略名称
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_position_status ON position(status);
CREATE INDEX idx_position_ts_code ON position(ts_code);
```

---

### 7. 回测结果表 (backtest_result)

```sql
CREATE TABLE backtest_result (
    id BIGSERIAL PRIMARY KEY,
    
    strategy_name VARCHAR(50) NOT NULL,    -- 策略名称
    ts_code VARCHAR(20),                 -- 股票代码
    
    start_date DATE NOT NULL,            -- 回测开始日期
    end_date DATE NOT NULL,              -- 回测结束日期
    
    -- 收益指标
    total_return DECIMAL(12, 4),        -- 总收益率 (%)
    annual_return DECIMAL(12, 4),       -- 年化收益率 (%)
    
    -- 风险指标
    sharpe_ratio DECIMAL(10, 4),        -- 夏普比率
    max_drawdown DECIMAL(12, 4),        -- 最大回撤 (%)
    volatility DECIMAL(12, 4),           -- 年化波动率 (%)
    
    -- 交易统计
    total_trades INTEGER,               -- 总交易次数
    win_trades INTEGER,                  -- 盈利次数
    loss_trades INTEGER,                 -- 亏损次数
    win_rate DECIMAL(10, 4),            -- 胜率 (%)
    
    avg_profit DECIMAL(14, 2),          -- 平均盈利
    avg_loss DECIMAL(14, 2),            -- 平均亏损
    profit_loss_ratio DECIMAL(10, 4),   -- 盈亏比
    
    params JSONB,                        -- 策略参数
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_backtest_strategy ON backtest_result(strategy_name);
```

---

## 数据获取流程

```
┌─────────────┐     stock_info      ┌─────────────┐
│  tushare    │ ─────────────────► │  PostgreSQL │
│ stock_basic │                    └─────────────┘
└─────────────┘                            │
                                           ▼
┌─────────────┐     stock_daily     ┌─────────────┐
│   akshare   │ ─────────────────► │  PostgreSQL │
│stock_zh_a.. │                    └─────────────┘
└─────────────┘                            │
                                           ▼
┌─────────────┐     factor_ma       ┌─────────────┐
│   计算      │ ─────────────────► │  PostgreSQL │
│   (Python)  │                    └─────────────┘
└─────────────┘
```

---

*Updated: 2026-02-24*
