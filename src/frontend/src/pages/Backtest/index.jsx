/**
 * 回测页面 - 主组件
 */
import { useState } from 'react';
import BacktestConfig from './components/BacktestConfig';
import MetricsCard from './components/MetricsCard';
import TradeLogTable from './components/TradeLogTable';
import { createChart } from 'lightweight-charts';

function BacktestPage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (config) => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch('/api/backtest/run', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || '回测失败');
      }

      setResult(data.data);
      
      // 回测完成后绘制图表
      setTimeout(() => {
        renderChart(data.data);
      }, 100);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const renderChart = (data) => {
    const container = document.getElementById('backtest-chart');
    if (!container) return;

    // 清除旧图表
    container.innerHTML = '';

    const chart = createChart(container, {
      layout: {
        background: { type: 'solid', color: '#1a1a2e' },
        textColor: '#d1d4dc',
      },
      grid: {
        vertLines: { color: '#2b2b43' },
        horzLines: { color: '#2b2b43' },
      },
      width: container.clientWidth || 800,
      height: 400,
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
      },
    });

    // 加载 K 线数据
    const tsCode = data.config.ts_code;
    const startDate = data.config.start_date;
    const endDate = data.config.end_date;

    fetch(`/api/stock/${tsCode}?start_date=${startDate}&end_date=${endDate}`)
      .then(res => res.json())
      .then(stockData => {
        if (!stockData.data || stockData.data.length === 0) return;

        const klineData = stockData.data.map(d => ({
          time: d.time,  // API 返回的是 time 字段
          open: d.open,
          high: d.high,
          low: d.low,
          close: d.close,
        }));

        // 添加 K 线
        const candleSeries = chart.addCandlestickSeries({
          upColor: '#26a69a',
          downColor: '#ef5350',
          borderVisible: false,
          wickUpColor: '#26a69a',
          wickDownColor: '#ef5350',
        });
        candleSeries.setData(klineData);

        // 添加买卖信号
        if (data.signals && data.signals.length > 0) {
          const markers = data.signals.map(s => {
            const [year, month, day] = s.date.split('-').map(Number);
            return {
              time: { year, month, day },
              position: s.type === 'buy' ? 'belowBar' : 'aboveBar',
              color: s.type === 'buy' ? '#26a69a' : '#ef5350',
              shape: s.type === 'buy' ? 'arrowUp' : 'arrowDown',
              text: s.type === 'buy' ? 'BUY' : 'SELL',
            };
          });
          candleSeries.setMarkers(markers);
        }

        chart.timeScale().fitContent();
      })
      .catch(err => console.error('Failed to load K-line data:', err));

    // 窗口大小变化时重绘
    const handleResize = () => {
      chart.applyOptions({
        width: container.clientWidth || 800,
      });
    };
    window.addEventListener('resize', handleResize);
  };

  return (
    <div className="backtest-page">
      <h1>回测系统</h1>
      
      <BacktestConfig onSubmit={handleSubmit} loading={loading} />

      {error && (
        <div className="error-message">
          <span>❌ {error}</span>
        </div>
      )}

      {result && (
        <>
          <MetricsCard metrics={result.metrics} />
          
          <div className="chart-section">
            <h3>K 线图表 (带买卖信号)</h3>
            <div id="backtest-chart"></div>
          </div>

          <TradeLogTable trades={result.trades} />
        </>
      )}

      <style>{`
        .backtest-page {
          padding: 20px;
          width: 100%;
          max-width: none;
          margin: 0 auto;
        }
        .backtest-page > h1 {
          display: none;
        }
        .error-message {
          background: rgba(239, 83, 80, 0.1);
          border: 1px solid #ef5350;
          border-radius: 8px;
          padding: 16px;
          margin-bottom: 20px;
          color: #ef5350;
        }
        .chart-section {
          background: #1a1a2e;
          border-radius: 8px;
          padding: 16px;
          margin-bottom: 20px;
        }
        .chart-section h3 {
          color: #fff;
          margin: 0 0 16px 0;
          font-size: 16px;
        }
        #backtest-chart {
          width: 100%;
          height: 500px;
        }
      `}</style>
    </div>
  );
}

export default BacktestPage;
