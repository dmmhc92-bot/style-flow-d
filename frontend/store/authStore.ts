import { create } from 'zustand';
import { storage } from '../utils/storage';
import api from '../utils/api';

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
      
      await storage.setToken(token);
      await storage.setUserData(user);
      
      set({ token, user, isAuthenticated: true });
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
      
      await storage.setToken(token);
      await storage.setUserData(user);
      
      set({ token, user, isAuthenticated: true });
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Signup failed');
    }
  },
  
  logout: async () => {
    await storage.clearAll();
    set({ user: null, token: null, isAuthenticated: false });
  },
  
  loadUser: async () => {
    try {
      const token = await storage.getToken();
      
      if (token) {
        const response = await api.get('/auth/me');
        set({ user: response.data, token, isAuthenticated: true, isLoading: false });
      } else {
        set({ isLoading: false });
      }
    } catch (error) {
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
      await storage.clearAll();
      set({ user: null, token: null, isAuthenticated: false });
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Delete account failed');
    }
  },
}));