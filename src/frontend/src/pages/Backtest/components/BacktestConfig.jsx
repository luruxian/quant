/**
 * 回测配置表单组件
 */
import { useState, useEffect } from 'react';

function BacktestConfig({ onSubmit, loading }) {
  const [stocks, setStocks] = useState([]);
  const [config, setConfig] = useState({
    ts_code: '000001.SZ',
    start_date: '2025-01-02',
    end_date: '2025-12-31',
    strategy: 'ma_cross',
    params: {
      ma_fast: 5,
      ma_slow: 10
    },
    initial_cash: 1000000,
    commission: 0.0003,
    slippage: 0.002
  });

  // 加载股票列表
  useEffect(() => {
    fetch('/api/stocks')
      .then(res => res.json())
      .then(data => {
        setStocks(data.stocks?.slice(0, 100) || []);
      })
      .catch(err => console.error('Failed to load stocks:', err));
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(config);
  };

  const updateConfig = (key, value) => {
    setConfig(prev => ({ ...prev, [key]: value }));
  };

  const updateParams = (key, value) => {
    setConfig(prev => ({
      ...prev,
      params: { ...prev.params, [key]: Number(value) }
    }));
  };

  return (
    <form onSubmit={handleSubmit} className="backtest-config">
      <div className="config-row">
        <div className="config-item">
          <label>股票代码</label>
          <select 
            value={config.ts_code} 
            onChange={e => updateConfig('ts_code', e.target.value)}
          >
            {stocks.map(stock => (
              <option key={stock.ts_code} value={stock.ts_code}>
                {stock.ts_code} - {stock.name}
              </option>
            ))}
          </select>
        </div>

        <div className="config-item">
          <label>策略</label>
          <select 
            value={config.strategy}
            onChange={e => updateConfig('strategy', e.target.value)}
          >
            <option value="ma_cross">均线交叉策略 (MA5/MA10)</option>
            <option value="dual_ma_cross">双均线交叉策略</option>
          </select>
        </div>
      </div>

      <div className="config-row">
        <div className="config-item">
          <label>开始日期</label>
          <input 
            type="date" 
            value={config.start_date}
            onChange={e => updateConfig('start_date', e.target.value)}
          />
        </div>

        <div className="config-item">
          <label>结束日期</label>
          <input 
            type="date" 
            value={config.end_date}
            onChange={e => updateConfig('end_date', e.target.value)}
          />
        </div>
      </div>

      {config.strategy === 'ma_cross' && (
        <div className="config-row">
          <div className="config-item">
            <label>快线周期</label>
            <input 
              type="number" 
              value={config.params.ma_fast}
              onChange={e => updateParams('ma_fast', e.target.value)}
              min={1}
              max={60}
            />
          </div>

          <div className="config-item">
            <label>慢线周期</label>
            <input 
              type="number" 
              value={config.params.ma_slow}
              onChange={e => updateParams('ma_slow', e.target.value)}
              min={1}
              max={120}
            />
          </div>
        </div>
      )}

      <div className="config-row">
        <div className="config-item">
          <label>初始资金</label>
          <input 
            type="number" 
            value={config.initial_cash}
            onChange={e => updateConfig('initial_cash', Number(e.target.value))}
            step={10000}
          />
        </div>

        <div className="config-item">
          <label>手续费率</label>
          <input 
            type="number" 
            value={config.commission}
            onChange={e => updateConfig('commission', Number(e.target.value))}
            step={0.0001}
            min={0}
            max={0.01}
          />
        </div>

        <div className="config-item">
          <label>滑点</label>
          <input 
            type="number" 
            value={config.slippage}
            onChange={e => updateConfig('slippage', Number(e.target.value))}
            step={0.001}
            min={0}
            max={0.1}
          />
        </div>
      </div>

      <button type="submit" className="submit-btn" disabled={loading}>
        {loading ? '回测中...' : '开始回测'}
      </button>

      <style>{`
        .backtest-config {
          background: #1a1a2e;
          padding: 24px;
          border-radius: 8px;
          margin-bottom: 20px;
          display: flex;
          flex-wrap: wrap;
          gap: 20px;
          align-items: flex-end;
        }
        .config-row {
          display: flex;
          gap: 16px;
          flex-wrap: wrap;
        }
        .config-item {
          min-width: 180px;
          flex: 1;
        }
        .config-item label {
          display: block;
          color: #8b8b9e;
          font-size: 12px;
          margin-bottom: 6px;
        }
        .config-item input,
        .config-item select {
          width: 100%;
          padding: 10px 14px;
          background: #16213e;
          border: 1px solid #2b2b43;
          border-radius: 4px;
          color: #fff;
          font-size: 14px;
        }
        .config-item input:focus,
        .config-item select:focus {
          outline: none;
          border-color: #26a69a;
        }
        .submit-btn {
          padding: 10px 32px;
          background: #26a69a;
          border: none;
          border-radius: 4px;
          color: #fff;
          font-size: 14px;
          cursor: pointer;
          transition: background 0.2s;
          white-space: nowrap;
        }
        .submit-btn:hover:not(:disabled) {
          background: #2bbbad;
        }
        .submit-btn:disabled {
          background: #4a4a5a;
          cursor: not-allowed;
        }
      `}</style>
    </form>
  );
}

export default BacktestConfig;
