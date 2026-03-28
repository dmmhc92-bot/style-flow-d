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
  is_tester?: boolean;  // App Store Review tester flag
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
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isTester: boolean;  // Quick access to tester status
  
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, full_name: string, business_name?: string) => Promise<void>;
  logout: () => Promise<void>;
  loadUser: () => Promise<void>;
  updateProfile: (data: Partial<User>) => Promise<void>;
  deleteAccount: () => Promise<void>;
  refreshAccessToken: () => Promise<boolean>;
  forgotPassword: (email: string) => Promise<void>;
  resetPassword: (token: string, newPassword: string) => Promise<void>;
  verifyResetToken: (token: string) => Promise<{ valid: boolean; email: string }>;
}

// Helper to check if user has premium access (either paid or tester)
export const hasPremiumAccess = (user: User | null, isTester: boolean): boolean => {
  if (!user) return false;
  if (isTester || user.is_tester) return true;
  return user.subscription_status === 'active' || user.subscription_status === 'premium';
};

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: null,
  refreshToken: null,
  isAuthenticated: false,
  isLoading: true,
  isTester: false,

  login: async (email: string, password: string) => {
    try {
      console.log('[Auth] Starting login API call...');
      const response = await api.post('/auth/login', { email, password });
      console.log('[Auth] Login API response received');
      const { token, refresh_token, user } = response.data;
      
      // Set token in memory cache FIRST for immediate use
      console.log('[Auth] Setting API token...');
      setApiToken(token);
      
      // Check if tester account
      const isTester = user.is_tester || false;
      console.log('[Auth] isTester:', isTester);
      
      // Then persist to storage
      console.log('[Auth] Persisting to storage...');
      await storage.setToken(token);
      if (refresh_token) {
        await storage.set('refreshToken', refresh_token);
      }
      await storage.setUserData(user);
      console.log('[Auth] Storage complete');
      
      // Set user ID for offline storage
      if (user.id) {
        offlineStorage.setUserId(user.id);
      }
      
      console.log('[Auth] Setting state...');
      set({ 
        token, 
        refreshToken: refresh_token,
        user, 
        isAuthenticated: true,
        isTester
      });
      console.log('[Auth] State set, isAuthenticated: true');
      
      // Initialize RevenueCat with user ID (skip subscription check for testers)
      // Wrap in try-catch to prevent RevenueCat errors from blocking login
      try {
        const subscriptionStore = useSubscriptionStore.getState();
        if (!isTester) {
          await subscriptionStore.identifyUser(user.id);
        } else {
          // Testers get automatic premium status
          set({ user: { ...user, subscription_status: 'active' } });
        }
      } catch (rcError) {
        console.warn('[Auth] RevenueCat initialization error (non-blocking):', rcError);
        // Don't throw - let login continue even if RevenueCat fails
      }
      console.log('[Auth] Login complete');
    } catch (error: any) {
      console.error('[Auth] Login error:', error);
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
      const { token, refresh_token, user } = response.data;
      
      // Set token in memory cache FIRST for immediate use
      setApiToken(token);
      
      // Check if tester account
      const isTester = user.is_tester || false;
      
      // Then persist to storage
      await storage.setToken(token);
      if (refresh_token) {
        await storage.set('refreshToken', refresh_token);
      }
      await storage.setUserData(user);
      
      // Set user ID for offline storage
      if (user.id) {
        offlineStorage.setUserId(user.id);
      }
      
      set({ 
        token, 
        refreshToken: refresh_token,
        user, 
        isAuthenticated: true,
        isTester
      });
      
      // Initialize RevenueCat with user ID (skip for testers)
      const subscriptionStore = useSubscriptionStore.getState();
      if (!isTester) {
        await subscriptionStore.identifyUser(user.id);
      }
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Signup failed');
    }
  },

  logout: async () => {
    try {
      // Call logout endpoint to invalidate refresh token
      await api.post('/auth/logout').catch(() => {});
    } catch (e) {
      // Continue with local logout even if API fails
    }
    
    // Clear token from memory cache first
    clearApiToken();
    
    // Log out from RevenueCat
    const subscriptionStore = useSubscriptionStore.getState();
    await subscriptionStore.logout();
    
    // Clear offline data for this user
    await offlineStorage.clearUserData();
    offlineStorage.clearUserId();
    
    await storage.clearAll();
    set({ 
      user: null, 
      token: null, 
      refreshToken: null,
      isAuthenticated: false,
      isTester: false
    });
  },

  loadUser: async () => {
    try {
      const token = await storage.getToken();
      const refreshToken = await storage.get('refreshToken');
      
      if (token) {
        // Set token in memory cache for API calls
        setApiToken(token);
        
        // Try to load from server
        try {
          const response = await api.get('/auth/me');
          const user = response.data;
          
          // Check if tester account
          const isTester = user.is_tester || false;
          
          // Set user ID for offline storage
          if (user.id) {
            offlineStorage.setUserId(user.id);
          }
          
          set({ 
            user, 
            token, 
            refreshToken,
            isAuthenticated: true, 
            isLoading: false,
            isTester
          });
          
          // Initialize subscription (skip check for testers)
          const subscriptionStore = useSubscriptionStore.getState();
          if (!isTester && user.id) {
            await subscriptionStore.identifyUser(user.id);
          }
        } catch (error: any) {
          // If 401, try to refresh token
          if (error.response?.status === 401 && refreshToken) {
            const refreshed = await get().refreshAccessToken();
            if (refreshed) {
              // Retry loading user
              const response = await api.get('/auth/me');
              const user = response.data;
              const isTester = user.is_tester || false;
              
              if (user.id) {
                offlineStorage.setUserId(user.id);
              }
              
              set({ 
                user, 
                isAuthenticated: true, 
                isLoading: false,
                isTester
              });
              return;
            }
          }
          
          // If server is unavailable, try loading from local storage
          const cachedUser = await storage.getUserData();
          if (cachedUser) {
            if (cachedUser.id) {
              offlineStorage.setUserId(cachedUser.id);
            }
            set({ 
              user: cachedUser, 
              token, 
              refreshToken,
              isAuthenticated: true, 
              isLoading: false,
              isTester: cachedUser.is_tester || false
            });
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
      set({ 
        user: null, 
        token: null, 
        refreshToken: null,
        isAuthenticated: false, 
        isLoading: false,
        isTester: false
      });
    }
  },

  refreshAccessToken: async () => {
    try {
      const refreshToken = get().refreshToken || await storage.get('refreshToken');
      if (!refreshToken) return false;
      
      const response = await api.post('/auth/refresh', {}, {
        headers: { 'X-Refresh-Token': refreshToken }
      });
      
      const { token, refresh_token } = response.data;
      
      // Update tokens
      setApiToken(token);
      await storage.setToken(token);
      if (refresh_token) {
        await storage.set('refreshToken', refresh_token);
      }
      
      set({ token, refreshToken: refresh_token });
      return true;
    } catch (error) {
      // Refresh failed - need to re-login
      return false;
    }
  },

  forgotPassword: async (email: string) => {
    try {
      await api.post('/auth/forgot-password', { email });
    } catch (error: any) {
      // Don't throw - we don't want to reveal if email exists
    }
  },

  resetPassword: async (token: string, newPassword: string) => {
    try {
      await api.post('/auth/reset-password', { 
        token, 
        new_password: newPassword 
      });
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Password reset failed');
    }
  },

  verifyResetToken: async (token: string) => {
    try {
      const response = await api.get(`/auth/verify-reset-token/${token}`);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Invalid or expired token');
    }
  },

  updateProfile: async (data: Partial<User>) => {
    try {
      const response = await api.put('/auth/profile', data);
      const updatedUser = response.data;
      
      await storage.setUserData(updatedUser);
      set({ user: updatedUser });
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Update failed');
    }
  },

  deleteAccount: async () => {
    try {
      await api.delete('/auth/account');
      await get().logout();
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Delete account failed');
    }
  },
}));

// Export a hook for checking premium access (combines tester + subscription)
export const usePremiumAccess = () => {
  const { user, isTester } = useAuthStore();
  const { isPremium } = useSubscriptionStore();
  
  // Testers always have premium access
  if (isTester || user?.is_tester) return true;
  
  // Otherwise check actual subscription
  return isPremium || user?.subscription_status === 'active';
};
