/**
 * 绩效指标卡片组件
 */
function MetricsCard({ metrics }) {
  if (!metrics) return null;

  const formatPercent = (value) => {
    if (value === null || value === undefined) return '-';
    return `${(value * 100).toFixed(2)}%`;
  };

  const formatNumber = (value) => {
    if (value === null || value === undefined) return '-';
    return value.toFixed(2);
  };

  const formatMoney = (value) => {
    if (value === null || value === undefined) return '-';
    return value.toLocaleString('zh-CN', { 
      style: 'currency', 
      currency: 'CNY',
      minimumFractionDigits: 2 
    });
  };

  const cards = [
    {
      label: '总收益率',
      value: formatPercent(metrics.total_return),
      color: metrics.total_return > 0 ? '#26a69a' : '#ef5350',
      tooltip: '回测期间的总收益率'
    },
    {
      label: '年化收益',
      value: formatPercent(metrics.annual_return),
      color: metrics.annual_return > 0 ? '#26a69a' : '#ef5350',
      tooltip: '年化后的收益率'
    },
    {
      label: '夏普比率',
      value: metrics.sharpe_ratio?.toFixed(2) || '-',
      color: metrics.sharpe_ratio > 1 ? '#26a69a' : metrics.sharpe_ratio > 0 ? '#f2a900' : '#ef5350',
      tooltip: '风险调整后的收益指标，越高越好'
    },
    {
      label: '最大回撤',
      value: formatPercent(metrics.max_drawdown),
      color: '#ef5350',
      tooltip: '历史最大亏损幅度'
    },
    {
      label: '胜率',
      value: formatPercent(metrics.win_rate),
      color: metrics.win_rate > 0.5 ? '#26a69a' : '#ef5350',
      tooltip: '盈利交易占比'
    },
    {
      label: '盈亏比',
      value: metrics.profit_factor === Infinity ? '∞' : formatNumber(metrics.profit_factor),
      color: metrics.profit_factor > 1 ? '#26a69a' : '#ef5350',
      tooltip: '平均盈利/平均亏损'
    },
    {
      label: '交易次数',
      value: metrics.total_trades || 0,
      color: '#24a0fb',
      tooltip: '总交易次数'
    },
    {
      label: '盈亏交易',
      value: `${metrics.winning_trades || 0} / ${metrics.losing_trades || 0}`,
      color: '#24a0fb',
      tooltip: '盈利次数 / 亏损次数'
    }
  ];

  return (
    <div className="metrics-card">
      {cards.map((card, index) => (
        <div key={index} className="metric-item" title={card.tooltip}>
          <div className="metric-label">{card.label}</div>
          <div className="metric-value" style={{ color: card.color }}>
            {card.value}
          </div>
        </div>
      ))}

      <style>{`
        .metrics-card {
          display: grid;
          grid-template-columns: repeat(8, 1fr);
          gap: 16px;
          margin-bottom: 20px;
        }
        .metric-item {
          background: #1a1a2e;
          padding: 20px;
          border-radius: 8px;
          text-align: center;
        }
        .metric-label {
          color: #8b8b9e;
          font-size: 13px;
          margin-bottom: 10px;
        }
        .metric-value {
          font-size: 22px;
          font-weight: 600;
        }
        @media (max-width: 1200px) {
          .metrics-card {
            grid-template-columns: repeat(4, 1fr);
          }
        }
      `}</style>
    </div>
  );
}

export default MetricsCard;
