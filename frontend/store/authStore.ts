import { create } from 'zustand';
import { storage } from '../utils/storage';
import { offlineStorage } from '../utils/offlineStorage';
import api, { setApiToken, clearApiToken } from '../utils/api';
import { useSubscriptionStore } from './subscriptionStore';

interface User {
  id?: string;
  email: string;
  full_name: string;
  business_name?: string;
  bio?: string;
  specialties?: string;
  salon_name?: string;
  city?: string;
  profile_photo?: string;
  instagram_handle?: string;
  tiktok_handle?: string;
  website_url?: string;
  profile_visibility?: string;
  subscription_status?: string;
  is_admin?: boolean;
  // Moderation fields
  moderation_status?: string;
  warnings_count?: number;
  last_warning_reason?: string;
  suspended_until?: string;
  suspension_reason?: string;
  ban_reason?: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, full_name: string, business_name?: string) => Promise<void>;
  logout: () => Promise<void>;
  loadUser: () => Promise<void>;
  updateProfile: (data: Partial<User>) => Promise<void>;
  deleteAccount: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: true,
  
  login: async (email: string, password: string) => {
    try {
      const response = await api.post('/auth/login', { email, password });
      const { token, user } = response.data;
      
      // Set token in memory cache FIRST for immediate use
      setApiToken(token);
      
      // Then persist to storage
      await storage.setToken(token);
      await storage.setUserData(user);
      
      // Set user ID for offline storage
      if (user.id) {
        offlineStorage.setUserId(user.id);
      }
      
      set({ token, user, isAuthenticated: true });
      
      // Initialize RevenueCat with user ID
      const subscriptionStore = useSubscriptionStore.getState();
      await subscriptionStore.identifyUser(user.id);
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Login failed');
    }
  },
  
  signup: async (email: string, password: string, full_name: string, business_name?: string) => {
    try {
      const response = await api.post('/auth/signup', {
        email,
        password,
        full_name,
        business_name,
      });
      const { token, user } = response.data;
      
      // Set token in memory cache FIRST for immediate use
      setApiToken(token);
      
      // Then persist to storage
      await storage.setToken(token);
      await storage.setUserData(user);
      
      // Set user ID for offline storage
      if (user.id) {
        offlineStorage.setUserId(user.id);
      }
      
      set({ token, user, isAuthenticated: true });
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Signup failed');
    }
  },
  
  logout: async () => {
    // Clear token from memory cache first
    clearApiToken();
    
    // Log out from RevenueCat
    const subscriptionStore = useSubscriptionStore.getState();
    await subscriptionStore.logout();
    
    // Clear offline data for this user
    await offlineStorage.clearUserData();
    offlineStorage.clearUserId();
    
    await storage.clearAll();
    set({ user: null, token: null, isAuthenticated: false });
  },
  
  loadUser: async () => {
    try {
      const token = await storage.getToken();
      
      if (token) {
        // Set token in memory cache for API calls
        setApiToken(token);
        
        // Try to load from server
        try {
          const response = await api.get('/auth/me');
          const user = response.data;
          
          // Set user ID for offline storage
          if (user.id) {
            offlineStorage.setUserId(user.id);
          }
          
          set({ user, token, isAuthenticated: true, isLoading: false });
        } catch (error) {
          // If server is unavailable, try loading from local storage
          const cachedUser = await storage.getUserData();
          if (cachedUser) {
            if (cachedUser.id) {
              offlineStorage.setUserId(cachedUser.id);
            }
            set({ user: cachedUser, token, isAuthenticated: true, isLoading: false });
          } else {
            throw error;
          }
        }
      } else {
        set({ isLoading: false });
      }
    } catch (error) {
      // Clear token from memory on auth failure
      clearApiToken();
      await storage.clearAll();
      set({ user: null, token: null, isAuthenticated: false, isLoading: false });
    }
  },
  
  updateProfile: async (data: Partial<User>) => {
    try {
      await api.put('/auth/profile', data);
      // Fetch updated user data from server to ensure consistency
      const response = await api.get('/auth/me');
      const updatedUser = response.data;
      await storage.setUserData(updatedUser);
      set({ user: updatedUser });
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Update failed');
    }
  },
  
  deleteAccount: async () => {
    try {
      await api.delete('/auth/delete-account');
      
      // Clear offline data
      await offlineStorage.clearUserData();
      offlineStorage.clearUserId();
      
      await storage.clearAll();
      set({ user: null, token: null, isAuthenticated: false });
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Delete account failed');
    }
  },
}));