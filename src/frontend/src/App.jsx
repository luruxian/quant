import { useState, useCallback, useEffect } from 'react';
import KLineChart from './components/KLineChart';
import StockSelector from './components/StockSelector';
import stockApi from './api/stockApi';
import './App.css';

function App() {
  const [selectedStock, setSelectedStock] = useState('000001.SZ');
  const [stockData, setStockData] = useState(null);
  const [signals, setSignals] = useState([]);
  const [indicators, setIndicators] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadData = useCallback(async (tsCode) => {
    setLoading(true);
    setError(null);

    try {
      // Fetch data in parallel
      const [stockResult, signalsResult, indicatorsResult] = await Promise.all([
        stockApi.getStockData(tsCode),
        stockApi.getSignals(tsCode),
        stockApi.getIndicators(tsCode, '5,10,20,60'),
      ]);

      setStockData(stockResult.data);
      setSignals(signalsResult.signals);
      setIndicators(indicatorsResult.indicators);
    } catch (err) {
      console.error('Failed to load data:', err);
      setError('加载数据失败，请检查后端服务是否启动');
      
      // Demo data when API fails
      setStockData(generateDemoData());
      setSignals(generateDemoSignals());
      setIndicators(generateDemoIndicators());
    } finally {
      setLoading(false);
    }
  }, []);

  // Load data when stock changes
  useEffect(() => {
    if (selectedStock) {
      loadData(selectedStock);
    }
  }, [selectedStock, loadData]);

  const handleStockSelect = (tsCode) => {
    setSelectedStock(tsCode);
    loadData(tsCode);
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>📈 量化交易可视化系统</h1>
        <div className="stock-info">
          {stockData && (
            <span className="stock-name">{stockData.name} - {selectedStock}</span>
          )}
        </div>
      </header>

      <main className="app-main">
        <aside className="sidebar">
          <StockSelector 
            selected={selectedStock} 
            onSelect={handleStockSelect} 
          />
        </aside>

        <section className="chart-section">
          {error && (
            <div className="error-message">
              {error}
              <br />
              <small>显示演示数据</small>
            </div>
          )}

          {loading ? (
            <div className="loading-container">
              <div className="loading">加载K线数据...</div>
            </div>
          ) : (
            <KLineChart 
              data={stockData} 
              signals={signals}
              indicators={indicators}
            />
          )}

          <div className="chart-legend">
            <span className="legend-item">
              <span className="legend-color" style={{ background: '#26a69a' }}></span>
              买入信号
            </span>
            <span className="legend-item">
              <span className="legend-color" style={{ background: '#ef5350' }}></span>
              卖出信号
            </span>
            <span className="legend-item">
              <span className="legend-color" style={{ background: '#fb8b24' }}></span>
              MA5
            </span>
            <span className="legend-item">
              <span className="legend-color" style={{ background: '#24a0fb' }}></span>
              MA10
            </span>
            <span className="legend-item">
              <span className="legend-color" style={{ background: '#f2a900' }}></span>
              MA20
            </span>
            <span className="legend-item">
              <span className="legend-color" style={{ background: '#9c27b0' }}></span>
              MA60
            </span>
          </div>
        </section>
      </main>
    </div>
  );
}

// Demo data generators (when API is unavailable)
function generateDemoData() {
  const data = [];
  let basePrice = 10;
  const startDate = new Date('2024-01-01');

  for (let i = 0; i < 120; i++) {
    const date = new Date(startDate);
    date.setDate(date.getDate() + i);
    
    const change = (Math.random() - 0.5) * 0.5;
    basePrice = Math.max(5, basePrice + change);
    
    const open = basePrice + (Math.random() - 0.5) * 0.3;
    const close = open + (Math.random() - 0.5) * 0.4;
    const high = Math.max(open, close) + Math.random() * 0.2;
    const low = Math.min(open, close) - Math.random() * 0.2;

    data.push({
      time: date.toISOString().split('T')[0],
      open: parseFloat(open.toFixed(2)),
      high: parseFloat(high.toFixed(2)),
      low: parseFloat(low.toFixed(2)),
      close: parseFloat(close.toFixed(2)),
      volume: Math.floor(Math.random() * 1000000) + 500000,
    });
  }
  return data;
}

function generateDemoSignals() {
  return [
    { time: '2024-03-15', position: 'belowBar', type: 'buy', price: 11.5 },
    { time: '2024-05-20', position: 'aboveBar', type: 'sell', price: 13.2 },
    { time: '2024-08-10', position: 'belowBar', type: 'buy', price: 10.8 },
    { time: '2024-11-05', position: 'aboveBar', type: 'sell', price: 12.5 },
  ];
}

function generateDemoIndicators() {
  const data = generateDemoData();
  const ma5 = [], ma10 = [], ma20 = [], ma60 = [];
  
  for (let i = 0; i < data.length; i++) {
    if (i >= 4) {
      const sum5 = data.slice(i - 4, i + 1).reduce((a, b) => a + b.close, 0);
      ma5.push({ time: data[i].time, value: parseFloat((sum5 / 5).toFixed(2)) });
    }
    if (i >= 9) {
      const sum10 = data.slice(i - 9, i + 1).reduce((a, b) => a + b.close, 0);
      ma10.push({ time: data[i].time, value: parseFloat((sum10 / 10).toFixed(2)) });
    }
    if (i >= 19) {
      const sum20 = data.slice(i - 19, i + 1).reduce((a, b) => a + b.close, 0);
      ma20.push({ time: data[i].time, value: parseFloat((sum20 / 20).toFixed(2)) });
    }
    if (i >= 59) {
      const sum60 = data.slice(i - 59, i + 1).reduce((a, b) => a + b.close, 0);
      ma60.push({ time: data[i].time, value: parseFloat((sum60 / 60).toFixed(2)) });
    }
  }
  
  return { ma5, ma10, ma20, ma60 };
}

export default App;
