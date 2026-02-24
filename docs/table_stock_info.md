# stock_info 表设计

## 数据源
- **接口**: tushare `stock_basic`
- **文档**: https://tushare.pro/document/2?doc_id=25
- **权限**: 2000积分起

## 字段映射

| tushare字段 | 数据库字段 | 类型 | 说明 |
|------------|-----------|------|------|
| ts_code | ts_code | VARCHAR(20) | **TS代码** (主键, e.g. 000001.SZ) |
| symbol | symbol | VARCHAR(10) | 股票代码 (e.g. 000001) |
| name | name | VARCHAR(100) | **股票名称** |
| area | area | VARCHAR(50) | 地域 |
| industry | industry | VARCHAR(100) | 所属行业 |
| fullname | full_name | VARCHAR(200) | 股票全称 |
| enname | en_name | VARCHAR(200) | 英文全称 |
| cnspell | cn_spell | VARCHAR(50) | 拼音缩写 |
| market | market | VARCHAR(20) | 市场类型 (主板/创业板/科创板/CDR/北交所) |
| exchange | exchange | VARCHAR(10) | 交易所代码 (SSE/SZSE/BSE) |
| curr_type | curr_type | VARCHAR(10) | 交易货币 |
| list_status | list_status | VARCHAR(1) | 上市状态 (L/D/G/P) |
| list_date | list_date | DATE | 上市日期 |
| delist_date | delist_date | DATE | 退市日期 |
| is_hs | is_hs | VARCHAR(1) | 沪深港通标的 (N/H/S) |
| act_name | act_name | VARCHAR(100) | 实控人名称 |
| act_ent_type | act_ent_type | VARCHAR(50) | 实控人企业性质 |

## 建表 SQL

```sql
-- 股票基本信息表
CREATE TABLE stock_info (
    id BIGSERIAL PRIMARY KEY,
    
    -- 股票代码 (唯一键)
    ts_code VARCHAR(20) NOT NULL UNIQUE,
    symbol VARCHAR(10),                    -- 股票代码 (如 000001)
    
    -- 基本信息
    name VARCHAR(100) NOT NULL,           -- 股票名称
    full_name VARCHAR(200),               -- 股票全称
    en_name VARCHAR(200),                -- 英文全称
    cn_spell VARCHAR(50),                -- 拼音缩写
    
    -- 市场与地域
    market VARCHAR(20),                   -- 市场类型 (主板/创业板/科创板/CDR/北交所)
    exchange VARCHAR(10),                -- 交易所 (SSE/SZSE/BSE)
    area VARCHAR(50),                    -- 地域
    industry VARCHAR(100),               -- 所属行业
    curr_type VARCHAR(10),               -- 交易货币 (CNY/USD/HKD)
    
    -- 上市信息
    list_status VARCHAR(1) DEFAULT 'L', -- 上市状态 (L/D/G/P)
    list_date DATE,                      -- 上市日期
    delist_date DATE,                    -- 退市日期
    
    -- 沪港通
    is_hs VARCHAR(1),                   -- 沪深港通标的 (N/H/S)
    
    -- 实控人信息
    act_name VARCHAR(100),               -- 实控人名称
    act_ent_type VARCHAR(50),           -- 实控人企业性质
    
    -- 元数据
    source VARCHAR(20) DEFAULT 'TUSHARE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_stock_info_ts_code ON stock_info(ts_code);
CREATE INDEX idx_stock_info_symbol ON stock_info(symbol);
CREATE INDEX idx_stock_info_name ON stock_info(name);
CREATE INDEX idx_stock_info_market ON stock_info(market);
CREATE INDEX idx_stock_info_exchange ON stock_info(exchange);
CREATE INDEX idx_stock_info_industry ON stock_info(industry);
CREATE INDEX idx_stock_info_list_status ON stock_info(list_status);
CREATE INDEX idx_stock_info_area ON stock_info(area);
```

## list_status 说明

| 值 | 说明 |
|----|------|
| L | 上市 |
| D | 退市 |
| G | 过会未交易 |
| P | 暂停上市 |

## is_hs 说明

| 值 | 说明 |
|----|------|
| N | 否 |
| H | 沪股通 |
| S | 深股通 |

## 示例数据

| ts_code | symbol | name | market | exchange | area | industry | list_date |
|---------|---------|------|--------|----------|------|----------|------------|
| 000001.SZ | 000001 | 平安银行 | 主板 | SZSE | 深圳 | 银行 | 1991-04-03 |
| 600519.SH | 600519 | 贵州茅台 | 主板 | SSE | 贵州 | 白酒 | 2001-08-27 |
| 688111.SH | 688111 | 华兴源创 | 科创板 | SSE | 江苏 | 半导体 | 2019-07-22 |

---

*Created: 2026-02-24*
*Source: https://tushare.pro/document/2?doc_id=25*
