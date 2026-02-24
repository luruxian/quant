import { useState, useEffect } from 'react';
import stockApi from '../api/stockApi';

function StockSelector({ onSelect, selected }) {
  const [stocks, setStocks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [customCode, setCustomCode] = useState('');

  useEffect(() => {
    loadStocks();
  }, []);

  const loadStocks = async () => {
    try {
      const data = await stockApi.getStockList();
      setStocks(data.stocks || []);
    } catch (error) {
      console.error('Failed to load stocks:', error);
      // Fallback stocks
      setStocks([
        { ts_code: '000001.SZ', name: '平安银行' },
        { ts_code: '600519.SH', name: '贵州茅台' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = (tsCode) => {
    onSelect(tsCode);
  };

  const handleCustomSubmit = (e) => {
    e.preventDefault();
    if (customCode.trim()) {
      onSelect(customCode.trim());
    }
  };

  return (
    <div className="stock-selector">
      <div className="selector-header">
        <h3>选择股票</h3>
      </div>

      {loading ? (
        <div className="loading">加载中...</div>
      ) : (
        <>
          <div className="stock-list">
            {stocks.map((stock) => (
              <button
                key={stock.ts_code}
                className={`stock-item ${selected === stock.ts_code ? 'active' : ''}`}
                onClick={() => handleSelect(stock.ts_code)}
              >
                <span className="stock-code">{stock.ts_code}</span>
                <span className="stock-name">{stock.name}</span>
              </button>
            ))}
          </div>

          <form onSubmit={handleCustomSubmit} className="custom-input">
            <input
              type="text"
              placeholder="输入股票代码 (如 000001.SZ)"
              value={customCode}
              onChange={(e) => setCustomCode(e.target.value)}
            />
            <button type="submit">添加</button>
          </form>
        </>
      )}
    </div>
  );
}

export default StockSelector;
