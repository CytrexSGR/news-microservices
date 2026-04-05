import axios from 'axios';
import { useAuthStore } from '@/store/authStore';

const authApi = axios.create({
  baseURL: import.meta.env.VITE_AUTH_API_URL,
});

const analyticsApi = axios.create({
  baseURL: import.meta.env.VITE_ANALYTICS_API_URL,
});

const feedApi = axios.create({
  baseURL: import.meta.env.VITE_FEED_API_URL,
});

const analysisApi = axios.create({
  baseURL: import.meta.env.VITE_ANALYSIS_API_URL,
});

const searchApi = axios.create({
  baseURL: import.meta.env.VITE_SEARCH_API_URL,
});

const predictionApi = axios.create({
  baseURL: import.meta.env.VITE_PREDICTION_API_URL,
});

const strategyLabApi = axios.create({
  baseURL: import.meta.env.VITE_PREDICTION_API_URL || 'http://localhost:8116/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
const addAuthInterceptor = (api: ReturnType<typeof axios.create>) => {
  api.interceptors.request.use(
    (config) => {
      const token = useAuthStore.getState().accessToken;
      if (token) {
        // Use bracket notation for axios 1.x compatibility
        config.headers['Authorization'] = `Bearer ${token}`;
      }
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );
};

// Add interceptors to all API instances
addAuthInterceptor(authApi);
addAuthInterceptor(analyticsApi);
addAuthInterceptor(feedApi);
addAuthInterceptor(analysisApi);
addAuthInterceptor(searchApi);
addAuthInterceptor(predictionApi);
addAuthInterceptor(strategyLabApi);

export { authApi, analyticsApi, feedApi, analysisApi, searchApi, predictionApi, strategyLabApi };
