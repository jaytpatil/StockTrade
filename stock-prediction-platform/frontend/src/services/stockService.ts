import api from './api';

export const StockService = {
  // Fetch all registered stocks
  async getStocks() {
    try {
      const response = await api.get('/stocks');
      return response.data;
    } catch (e) {
      const response = await api.get('/stocks/list');
      return response.data;
    }
  },

  // Search any global stock or asset
  async searchStocks(query: string = '') {
    const response = await api.get(`/stocks/search?q=${encodeURIComponent(query)}`);
    return response.data;
  },

  // Fetch prediction details for a specific ticker
  async getPrediction(ticker: string) {
    try {
      const response = await api.get(`/predict/${ticker}`);
      return response.data;
    } catch (e) {
      const response = await api.get(`/stocks/predict/${ticker}`);
      return response.data;
    }
  },

  // Mock function to trigger celery ML training job via admin panel (Placeholder)
  async forceRetrainModel(ticker: string) {
    const response = await api.post(`/admin/retrain`, { ticker });
    return response.data;
  }
};
