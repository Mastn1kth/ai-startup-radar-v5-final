import axios, { AxiosInstance, AxiosError } from 'axios';

declare module 'axios' {
  interface AxiosError {
    userMessage?: string;
  }
}

const API_URL = import.meta.env.VITE_API_URL || '';

export const api: AxiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

api.interceptors.request.use(
  (config) => config,
  (error: AxiosError) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const msg = (error.response?.data as { detail?: string })?.detail || error.message || 'API request failed';
    console.error(`API Error [${error.response?.status || 0}]: ${msg}`);
    error.userMessage = msg;
    return Promise.reject(error);
  }
);
