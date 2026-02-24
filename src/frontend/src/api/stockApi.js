import axios from 'axios';

const API_BASE = '/api';

export const stockApi = {
  /**
   * Get candlestick data
   * @param {string} tsCode - Stock code (e.g., '000001.SZ')
   * @param {string} startDate - Start date (YYYY-MM-DD)
   * @param {string} endDate - End date (YYYY-MM-DD)
   */
  getStockData: async (tsCode, startDate, endDate) => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    
    const response = await axios.get(
      `${API_BASE}/stock/${tsCode}?${params.toString()}`
    );
    return response.data;
  },

  /**
   * Get trading signals
   * @param {string} tsCode - Stock code
   * @param {number} days - Number of days
   */
  getSignals: async (tsCode, days = 60) => {
    const response = await axios.get(
      `${API_BASE}/signals/${tsCode}?days=${days}`
    );
    return response.data;
  },

  /**
   * Get technical indicators
   * @param {string} tsCode - Stock code
   * @param {string} ma - Moving averages (comma separated, e.g., '5,10,20,60')
   */
  getIndicators: async (tsCode, ma = '5,10,20,60') => {
    const response = await axios.get(
      `${API_BASE}/indicators/${tsCode}?ma=${ma}`
    );
    return response.data;
  },

  /**
   * Get list of available stocks
   */
  getStockList: async () => {
    const response = await axios.get(`${API_BASE}/stocks`);
    return response.data;
  }
};

export default stockApi;
