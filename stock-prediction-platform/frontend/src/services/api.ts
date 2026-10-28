import axios from 'axios';

// ----------------------------------------------------
// Core Axios Client Configuration & Interceptors
// ----------------------------------------------------
const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

apiClient.interceptors.request.use(
  (config) => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== 'undefined') {
      localStorage.removeItem('token');
      // Redirect handled at UI level or Router level to avoid hard reload cycles
    }
    return Promise.reject(error);
  }
);

export default apiClient;

// ----------------------------------------------------
// Standardized API Payload Interfaces (TypeScript)
// ----------------------------------------------------
export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: any;
}

// ----------------------------------------------------
// Service Modules
// ----------------------------------------------------

export const AuthService = {
  login: async (credentials: any) => {
    const formData = new URLSearchParams();
    formData.append('username', credentials.email);
    formData.append('password', credentials.password);
    
    // OAuth2PasswordRequestForm requires content-type urlencoded
    const response = await apiClient.post<AuthResponse>('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
    
    if (response.data.access_token && typeof window !== 'undefined') {
      localStorage.setItem('token', response.data.access_token);
      if (response.data.user) {
        localStorage.setItem('user', JSON.stringify(response.data.user));
      }
    }
    return response.data;
  },

  signup: async (userData: any) => {
    const response = await apiClient.post('/auth/register', userData);
    return response.data;
  },

  loginAsGuest: async () => {
    const response = await apiClient.post<AuthResponse>('/auth/guest');
    if (response.data.access_token && typeof window !== 'undefined') {
      localStorage.setItem('token', response.data.access_token);
      if (response.data.user) {
        localStorage.setItem('user', JSON.stringify(response.data.user));
      }
    }
    return response.data;
  },

  logout: () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    }
  },

  fetchProfile: async () => {
    const response = await apiClient.get('/auth/me');
    return response.data;
  }
};

export const TradingService = {
  buy: async (symbol: string, shares: number) => {
    const response = await apiClient.post('/trade/buy', { symbol, shares });
    return response.data;
  },

  sell: async (symbol: string, shares: number) => {
    const response = await apiClient.post('/trade/sell', { symbol, shares });
    return response.data;
  },

  deposit: async (amount: number) => {
    const response = await apiClient.post('/trade/deposit', { amount });
    return response.data;
  },

  fetchPortfolio: async () => {
    const response = await apiClient.get('/trade/portfolio');
    return response.data;
  }
};

export const MarketService = {
  // Fetch global tracked stocks
  fetchStockList: async () => {
    try {
      const response = await apiClient.get('/stocks');
      return response.data;
    } catch (e) {
      const response = await apiClient.get('/stocks/list');
      return response.data;
    }
  },

  // Search any global stock, crypto, ETF by symbol or company name
  searchStocks: async (query: string = '') => {
    const response = await apiClient.get(`/stocks/search?q=${encodeURIComponent(query)}`);
    return response.data;
  },

  // Fetch OHLCV timeline data for the interactive chart
  fetchHistoricalData: async (ticker: string, timeframe: string = '1y') => {
    try {
      const response = await apiClient.get(`/stocks/history/${ticker}?timeframe=${timeframe}`);
      return response.data;
    } catch (e) {
      const response = await apiClient.get(`/stocks/${ticker}/history?timeframe=${timeframe}`);
      return response.data;
    }
  },

  // Fetch technical indicators (RSI, MACD, SMA)
  fetchIndicators: async (ticker: string) => {
    try {
      const response = await apiClient.get(`/stocks/indicators/${ticker}`);
      return response.data;
    } catch (e) {
      const response = await apiClient.get(`/stocks/${ticker}/technical-indicators`);
      return response.data;
    }
  },

  // Fetch News scraped globally mapped via NLP Polarity score
  fetchSentimentAnalysis: async (ticker?: string) => {
    const url = ticker ? `/news/sentiment?ticker=${ticker}` : '/news/global-sentiment';
    const response = await apiClient.get(url);
    return response.data;
  },

  // Fetch Dashboard Watchlist Summary
  fetchDashboardSummary: async () => {
    const response = await apiClient.get('/stocks/dashboard/summary');
    return response.data;
  }
};

export const AIService = {
  // Fetch detailed future forecast matrix
  fetchPredictionResult: async (ticker: string) => {
    try {
      const response = await apiClient.get(`/predict/${ticker}`);
      return response.data;
    } catch (e) {
      // Fallback endpoint check
      const response = await apiClient.get(`/stocks/predict/${ticker}`);
      return response.data;
    }
  },

  // Fetch absolute recommendation matrices (BUY/SELL/HOLD + Confidence %)
  fetchRecommendations: async () => {
    const response = await apiClient.get('/predictions/recommendations');
    return response.data;
  }
};

export const AdminService = {
  // Fetch paginated user list
  fetchUsers: async (page = 1, limit = 50) => {
    const response = await apiClient.get(`/admin/users?page=${page}&limit=${limit}`);
    return response.data;
  },

  // Role manipulation and access revoking
  updateUserRole: async (userId: string, targetRole: string) => {
    const response = await apiClient.patch(`/admin/users/${userId}/role`, { role: targetRole });
    return response.data;
  },
  
  // Force Celery Worker to Retrain a specific model
  forceRetrainModel: async (ticker: string) => {
    const response = await apiClient.post(`/admin/ml/force-retrain`, { ticker });
    return response.data;
  }
};
