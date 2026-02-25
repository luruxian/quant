/**
 * 交易记录表格组件
 */
function TradeLogTable({ trades }) {
  if (!trades || trades.length === 0) {
    return (
      <div className="trade-table-empty">
        <p>暂无交易记录</p>
      </div>
    );
  }

  const formatMoney = (value) => {
    if (value === null || value === undefined) return '-';
    return value.toLocaleString('zh-CN', { 
      style: 'currency', 
      currency: 'CNY',
      minimumFractionDigits: 2 
    });
  };

  const formatPercent = (value) => {
    if (value === null || value === undefined) return '-';
    return `${(value * 100).toFixed(2)}%`;
  };

  return (
    <div className="trade-table">
      <h3>交易记录</h3>
      <table>
        <thead>
          <tr>
            <th>序号</th>
            <th>开仓日期</th>
            <th>平仓日期</th>
            <th>方向</th>
            <th>开仓价</th>
            <th>平仓价</th>
            <th>数量</th>
            <th>盈亏</th>
            <th>收益率</th>
          </tr>
        </thead>
        <tbody>
          {trades.map((trade, index) => (
            <tr key={index} className={trade.pnl > 0 ? 'profit' : 'loss'}>
              <td>{index + 1}</td>
              <td>{trade.entry_date}</td>
              <td>{trade.exit_date || '-'}</td>
              <td>
                <span className={`direction ${trade.direction}`}>
                  {trade.direction === 'long' ? '📈 多' : '📉 空'}
                </span>
              </td>
              <td>{trade.entry_price?.toFixed(2)}</td>
              <td>{trade.exit_price?.toFixed(2) || '-'}</td>
              <td>{trade.size?.toLocaleString()}</td>
              <td className={trade.pnl > 0 ? 'profit' : 'loss'}>
                {trade.pnl > 0 ? '+' : ''}{formatMoney(trade.pnl)}
              </td>
              <td className={trade.return > 0 ? 'profit' : 'loss'}>
                {formatPercent(trade.return)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <style>{`
        .trade-table {
          background: #1a1a2e;
          border-radius: 8px;
          padding: 20px;
          overflow-x: auto;
        }
        .trade-table h3 {
          color: #fff;
          margin: 0 0 16px 0;
          font-size: 16px;
        }
        .trade-table table {
          width: 100%;
          min-width: 900px;
          border-collapse: collapse;
        }
        .trade-table th,
        .trade-table td {
          padding: 12px 16px;
          text-align: center;
          font-size: 14px;
        }
        .trade-table th {
          background: #16213e;
          color: #8b8b9e;
          font-weight: 500;
        }
        .trade-table td {
          color: #d1d4dc;
          border-bottom: 1px solid #2b2b43;
        }
        .trade-table tr:hover {
          background: #16213e;
        }
        .trade-table .profit {
          color: #26a69a;
        }
        .trade-table .loss {
          color: #ef5350;
        }
        .trade-table .direction {
          padding: 4px 12px;
          border-radius: 4px;
          font-size: 13px;
        }
        .trade-table .direction.long {
          background: rgba(38, 166, 154, 0.2);
        }
        .trade-table .direction.short {
          background: rgba(239, 83, 80, 0.2);
        }
        .trade-table-empty {
          background: #1a1a2e;
          border-radius: 8px;
          padding: 40px;
          text-align: center;
          color: #8b8b9e;
        }
      `}</style>
    </div>
  );
}

export default TradeLogTable;
