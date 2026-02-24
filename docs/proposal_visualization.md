# 可视化层方案 - K线与买卖点显示

## 1. 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                      前端 (React + lightweight-charts)        │
├─────────────────────────────────────────────────────────────┤
│  React + Vite                                                │
│  lightweight-charts (K线图)                                  │
│  + 买卖点标记 (Marker)                                      │
│  + 指标叠加 (MA/EMA)                                        │
└─────────────────────────────────────────────────────────────┘
                              │
                         HTTP / REST API
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      后端 (FastAPI)                          │
├─────────────────────────────────────────────────────────────┤
│  FastAPI (:8000)                                             │
│  - GET /api/stock/{ts_code}    获取K线数据                  │
│  - GET /api/signals/{ts_code}  获取买卖信号                  │
│  - GET /api/quote/{ts_code}     实时行情 (可选)             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      数据层 (PostgreSQL)                     │
└─────────────────────────────────────────────────────────────┘
```

## 2. 目录结构

```
quant/src/
├── backend/
│   ├── app.py                 # FastAPI 应用入口
│   ├── requirements.txt        # Python 依赖
│   ├── venv/                  # 虚拟环境
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py         # API 路由
│   │   └── stock.py           # 股票数据接口
│   ├── services/
│   │   ├── __init__.py
│   │   └── data_service.py   # 数据服务
│   └── utils/
│       ├── __init__.py
│       └── db.py              # 数据库工具
├── frontend/
│   ├── src/
│   │   ├── App.jsx            # 主组件
│   │   ├── App.css            # 样式
│   │   ├── main.jsx           # 入口
│   │   ├── api/
│   │   │   └── stockApi.js    # API 调用
│   │   └── components/
│   │       ├── KLineChart.jsx  # K线图表组件
│   │       └── StockSelector.jsx # 股票选择器
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── .env                   # 环境变量
└── README.md
```

## 3. API 设计

### 3.1 获取K线数据
```
GET /api/stock/{ts_code}?start_date=2024-01-01&end_date=2025-02-24

Response:
{
  "ts_code": "000001.SZ",
  "name": "平安银行",
  "data": [
    {
      "time": "2024-01-02",
      "open": 10.50,
      "high": 10.80,
      "low": 10.40,
      "close": 10.70,
      "volume": 1234567
    },
    ...
  ]
}
```

### 3.2 获取买卖信号
```
GET /api/signals/{ts_code}?days=60

Response:
{
  "ts_code": "000001.SZ",
  "signals": [
    {
      "time": "2024-03-15",
      "position": "LONG",
      "price": 12.50,
      "type": "buy"
    },
    {
      "time": "2024-05-20",
      "position": "EXIT",
      "price": 14.20,
      "type": "sell"
    },
    ...
  ]
}
```

### 3.3 获取技术指标
```
GET /api/indicators/{ts_code}?ma=5,10,20,60

Response:
{
  "ts_code": "000001.SZ",
  "indicators": {
    "ma5": [...],
    "ma10": [...],
    "ma20": [...],
    "ma60": [...]
  }
}
```

## 4. 前端实现 (React)

### 4.1 依赖
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "lightweight-charts": "^4.1.0",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.0",
    "vite": "^5.0.0"
  }
}
```

### 4.2 K线组件

```jsx
// components/KLineChart.jsx
import { createChart } from 'lightweight-charts';
import { useEffect, useRef } from 'react';

function KLineChart({ data, signals, indicators }) {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    chartRef.current = createChart(chartContainerRef.current, {
      width: 1200,
      height: 600,
      layout: {
        background: { type: 'solid', color: '#1a1a2e' },
        textColor: '#d1d4dc'
      },
      grid: {
        vertLines: { color: '#2b2b43' },
        horzLines: { color: '#2b2b43' }
      }
    });

    // K线系列
    const candleSeries = chartRef.current.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350'
    });

    candleSeries.setData(data);

    // 买卖点标记
    if (signals) {
      const markers = signals.map(s => ({
        time: s.time,
        position: s.type === 'buy' ? 'belowBar' : 'aboveBar',
        color: s.type === 'buy' ? '#26a69a' : '#ef5350',
        shape: s.type === 'buy' ? 'arrowUp' : 'arrowDown',
        text: s.type === 'buy' ? 'BUY' : 'SELL'
      }));
      candleSeries.setMarkers(markers);
    }

    // 均线
    if (indicators?.ma20) {
      const ma20Line = chartRef.current.addLineSeries({
        color: '#f2a900',
        lineWidth: 2,
        priceLineVisible: false
      });
      ma20Line.setData(indicators.ma20);
    }

    return () => chartRef.current.remove();
  }, [data, signals, indicators]);

  return <div ref={chartContainerRef} />;
}
```

## 5. 后端实现 (FastAPI)

### 5.1 主应用

```python
# app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import stock

app = FastAPI(title="Quant Trading API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stock.router, prefix="/api", tags=["stock"])

@app.get("/health")
def health_check():
    return {"status": "ok"}
```

### 5.2 路由

```python
# api/stock.py
from fastapi import APIRouter, Query
from services.data_service import DataService

router = APIRouter()
data_service = DataService()

@router.get("/stock/{ts_code}")
def get_stock_data(
    ts_code: str,
    start_date: str = Query(None),
    end_date: str = Query(None)
):
    return data_service.get_candlestick_data(ts_code, start_date, end_date)

@router.get("/signals/{ts_code}")
def get_signals(ts_code: str, days: int = Query(60)):
    return data_service.get_signals(ts_code, days)
```

## 6. 依赖

### 6.1 Python (requirements.txt)
```
fastapi
uvicorn
psycopg2-binary
sqlalchemy
pandas
tushare
python-dotenv
```

### 6.2 前端 (package.json)
```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  }
}
```

## 7. 端口

- 后端: `http://localhost:8000`
- 前端: `http://localhost:5173` (Vite dev server)

## 8. 实施计划

### Phase 1: 后端 FastAPI (1天)
- [ ] 搭建 FastAPI 项目
- [ ] 实现数据库连接
- [ ] 实现 K线数据接口
- [ ] 实现信号接口

### Phase 2: 前端 React (1.5天)
- [ ] 初始化 Vite + React 项目
- [ ] 集成 lightweight-charts
- [ ] 绘制K线图
- [ ] 添加买卖点标记
- [ ] 添加均线指标

### Phase 3: 集成与优化 (0.5天)
- [ ] 前后端联调
- [ ] 样式优化
- [ ] 股票选择器

---

*Created: 2026-02-24*
