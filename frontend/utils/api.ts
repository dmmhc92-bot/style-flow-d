import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';

// PRODUCTION LOCK: Backend URL must be explicitly set - no fallbacks allowed
if (!process.env.EXPO_PUBLIC_BACKEND_URL) {
  throw new Error('CRITICAL: Missing EXPO_PUBLIC_BACKEND_URL. Cannot run without production backend.');
}

const BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

// In-memory token cache for faster access and web compatibility
let cachedToken: string | null = null;

// Function to set token in memory (called from authStore)
export const setApiToken = (token: string | null) => {
  cachedToken = token;
};

// Function to get token (memory first, then storage)
export const getApiToken = async (): Promise<string | null> => {
  if (cachedToken) {
    return cachedToken;
  }
  try {
    const token = await AsyncStorage.getItem('authToken');
    if (token) {
      cachedToken = token;
    }
    return token;
  } catch (error) {
    console.warn('Error reading token from storage:', error);
    return null;
  }
};

// Function to clear token
export const clearApiToken = () => {
  cachedToken = null;
};

const api = axios.create({
  baseURL: `${BACKEND_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  async (config) => {
    // Try memory cache first (faster), then fall back to AsyncStorage
    let token = cachedToken;
    
    if (!token) {
      try {
        token = await AsyncStorage.getItem('authToken');
        if (token) {
          cachedToken = token; // Cache it for next request
        }
      } catch (error) {
        console.warn('Error reading token:', error);
      }
    }
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Clear auth data
      cachedToken = null;
      try {
        await AsyncStorage.removeItem('authToken');
        await AsyncStorage.removeItem('userData');
      } catch (e) {
        console.warn('Error clearing auth data:', e);
      }
      // Redirect to login handled by auth context
    }
    return Promise.reject(error);
  }
);

export default api;
