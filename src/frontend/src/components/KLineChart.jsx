import { createChart, ColorType } from 'lightweight-charts';
import { useEffect, useRef } from 'react';

function KLineChart({ data, signals, indicators, onChartReady }) {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!chartContainerRef.current || !data || data.length === 0) {
      return;
    }

    // Create chart
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#1a1a2e' },
        textColor: '#d1d4dc',
      },
      grid: {
        vertLines: { color: '#2b2b43' },
        horzLines: { color: '#2b2b43' },
      },
      width: chartContainerRef.current.clientWidth || 1200,
      height: 500,
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
      },
    });

    chartRef.current = chart;

    // Add candlestick series
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    });

    candleSeries.setData(data);

    // Add markers (signals)
    if (signals && signals.length > 0) {
      const markers = signals.map((s) => ({
        time: s.time,
        position: s.position,
        color: s.type === 'buy' ? '#26a69a' : '#ef5350',
        shape: s.type === 'buy' ? 'arrowUp' : 'arrowDown',
        text: s.type === 'buy' ? 'BUY' : 'SELL',
      }));
      candleSeries.setMarkers(markers);
    }

    // Add moving averages
    const maColors = {
      ma5: '#fb8b24',
      ma10: '#24a0fb',
      ma20: '#f2a900',
      ma60: '#9c27b0',
    };

    if (indicators) {
      Object.entries(indicators).forEach(([key, value]) => {
        if (value && value.length > 0) {
          const lineSeries = chart.addLineSeries({
            color: maColors[key] || '#ffffff',
            lineWidth: key === 'ma5' ? 1 : 2,
            priceLineVisible: false,
            crosshairMarkerVisible: false,
          });
          lineSeries.setData(value);
        }
      });
    }

    // Fit content
    chart.timeScale().fitContent();

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    // Callback for parent
    if (onChartReady) {
      onChartReady(chart);
    }

    // Cleanup - 使用 ref 标记避免重复销毁
    return () => {
      window.removeEventListener('resize', handleResize);
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, [data, signals, indicators]);

  return (
    <div
      ref={chartContainerRef}
      style={{ width: '100%', height: '500px' }}
    />
  );
}

export default KLineChart;
