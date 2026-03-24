import { create } from 'zustand';
import { Platform } from 'react-native';
import Purchases, { 
  PurchasesPackage, 
  CustomerInfo,
  PurchasesOffering,
  PURCHASES_ERROR_CODE
} from 'react-native-purchases';
import { storage } from '../utils/storage';
import api from '../utils/api';

// RevenueCat API key - will be set from env
const REVENUECAT_API_KEY = process.env.EXPO_PUBLIC_REVENUECAT_KEY || '';

// Entitlement identifier configured in RevenueCat
const PREMIUM_ENTITLEMENT = 'premium';

interface SubscriptionState {
  isConfigured: boolean;
  isLoading: boolean;
  isPremium: boolean;
  customerInfo: CustomerInfo | null;
  currentOffering: PurchasesOffering | null;
  packages: PurchasesPackage[];
  error: string | null;
  
  // Actions
  configure: (userId?: string) => Promise<void>;
  checkSubscriptionStatus: () => Promise<boolean>;
  purchasePackage: (pkg: PurchasesPackage) => Promise<boolean>;
  restorePurchases: () => Promise<boolean>;
  getOfferings: () => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
}

export const useSubscriptionStore = create<SubscriptionState>((set, get) => ({
  isConfigured: false,
  isLoading: false,
  isPremium: false,
  customerInfo: null,
  currentOffering: null,
  packages: [],
  error: null,

  configure: async (userId?: string) => {
    try {
      // Skip if no API key (development mode)
      if (!REVENUECAT_API_KEY) {
        console.warn('RevenueCat API key not configured - running in demo mode');
        set({ isConfigured: true, isLoading: false });
        return;
      }

      set({ isLoading: true, error: null });

      // Configure RevenueCat
      await Purchases.configure({ 
        apiKey: REVENUECAT_API_KEY,
        appUserID: userId || null
      });

      set({ isConfigured: true });

      // Check initial status
      await get().checkSubscriptionStatus();
      await get().getOfferings();

      set({ isLoading: false });
    } catch (error: any) {
      console.error('RevenueCat configure error:', error);
      set({ 
        isLoading: false, 
        error: error.message || 'Failed to initialize subscriptions',
        isConfigured: true // Mark as configured to allow app to continue
      });
    }
  },

  checkSubscriptionStatus: async () => {
    try {
      // Demo mode - check local storage
      if (!REVENUECAT_API_KEY) {
        const localPremium = await storage.getToken();
        // In demo mode, premium status can be mocked
        return false;
      }

      const customerInfo = await Purchases.getCustomerInfo();
      const isPremium = customerInfo.entitlements.active[PREMIUM_ENTITLEMENT]?.isActive ?? false;
      
      set({ customerInfo, isPremium });

      // Sync with backend
      try {
        await api.post('/subscription/sync', {
          is_premium: isPremium,
          entitlements: Object.keys(customerInfo.entitlements.active)
        });
      } catch (e) {
        // Non-critical - continue if backend sync fails
        console.warn('Backend subscription sync failed:', e);
      }

      return isPremium;
    } catch (error: any) {
      console.error('Check subscription status error:', error);
      set({ error: error.message || 'Failed to check subscription status' });
      return false;
    }
  },

  getOfferings: async () => {
    try {
      // Demo mode - create mock offerings
      if (!REVENUECAT_API_KEY) {
        set({ 
          packages: [],
          currentOffering: null
        });
        return;
      }

      const offerings = await Purchases.getOfferings();
      
      if (offerings.current) {
        set({ 
          currentOffering: offerings.current,
          packages: offerings.current.availablePackages
        });
      }
    } catch (error: any) {
      console.error('Get offerings error:', error);
      set({ error: error.message || 'Failed to load subscription options' });
    }
  },

  purchasePackage: async (pkg: PurchasesPackage) => {
    try {
      set({ isLoading: true, error: null });

      const { customerInfo } = await Purchases.purchasePackage(pkg);
      const isPremium = customerInfo.entitlements.active[PREMIUM_ENTITLEMENT]?.isActive ?? false;

      set({ 
        customerInfo, 
        isPremium,
        isLoading: false 
      });

      // Notify backend of purchase
      try {
        await api.post('/subscription/verify', {
          action: 'purchase',
          product_id: pkg.product.identifier,
          is_premium: isPremium
        });
      } catch (e) {
        console.warn('Backend purchase notification failed:', e);
      }

      return isPremium;
    } catch (error: any) {
      set({ isLoading: false });

      // Handle user cancellation silently
      if (error.code === PURCHASES_ERROR_CODE.PURCHASE_CANCELLED_ERROR) {
        return false;
      }

      // Handle other errors
      let errorMessage = 'Purchase failed';
      
      switch (error.code) {
        case PURCHASES_ERROR_CODE.PRODUCT_NOT_AVAILABLE_FOR_PURCHASE_ERROR:
          errorMessage = 'This subscription is not available in your region';
          break;
        case PURCHASES_ERROR_CODE.PURCHASE_NOT_ALLOWED_ERROR:
          errorMessage = 'Purchases are not allowed on this device';
          break;
        case PURCHASES_ERROR_CODE.PAYMENT_PENDING_ERROR:
          errorMessage = 'Payment is pending. Please check your payment method.';
          break;
        case PURCHASES_ERROR_CODE.NETWORK_ERROR:
          errorMessage = 'Network error. Please check your connection.';
          break;
        default:
          errorMessage = error.message || 'Purchase failed. Please try again.';
      }

      set({ error: errorMessage });
      return false;
    }
  },

  restorePurchases: async () => {
    try {
      set({ isLoading: true, error: null });

      const customerInfo = await Purchases.restorePurchases();
      const isPremium = customerInfo.entitlements.active[PREMIUM_ENTITLEMENT]?.isActive ?? false;

      set({ 
        customerInfo, 
        isPremium,
        isLoading: false 
      });

      // Notify backend of restore
      try {
        await api.post('/subscription/restore', {
          action: 'restore',
          is_premium: isPremium
        });
      } catch (e) {
        console.warn('Backend restore notification failed:', e);
      }

      return isPremium;
    } catch (error: any) {
      console.error('Restore purchases error:', error);
      set({ 
        isLoading: false,
        error: error.message || 'Failed to restore purchases'
      });
      return false;
    }
  },

  logout: async () => {
    try {
      if (REVENUECAT_API_KEY) {
        await Purchases.logOut();
      }
      set({ 
        customerInfo: null, 
        isPremium: false,
        isConfigured: false 
      });
    } catch (error: any) {
      console.error('RevenueCat logout error:', error);
    }
  },

  clearError: () => set({ error: null })
}));

// Hook for checking premium feature access
export const usePremiumFeature = (featureName: string) => {
  const { isPremium } = useSubscriptionStore();
  
  // Define which features require premium
  const premiumFeatures = [
    'unlimited_clients',
    'advanced_analytics',
    'ai_unlimited',
    'priority_support',
    'custom_branding',
    'export_data'
  ];
  
  const requiresPremium = premiumFeatures.includes(featureName);
  const hasAccess = !requiresPremium || isPremium;
  
  return { hasAccess, requiresPremium, isPremium };
};
