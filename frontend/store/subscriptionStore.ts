import { create } from 'zustand';
import { Platform } from 'react-native';
import Purchases, { 
  PurchasesPackage, 
  CustomerInfo,
  PurchasesOffering,
  PURCHASES_ERROR_CODE,
  LOG_LEVEL
} from 'react-native-purchases';
import { storage } from '../utils/storage';
import api from '../utils/api';
import { useAuthStore } from './authStore';

// RevenueCat API key from environment
const REVENUECAT_API_KEY = process.env.EXPO_PUBLIC_REVENUECAT_KEY || '';

// Entitlement identifier configured in RevenueCat dashboard
const PREMIUM_ENTITLEMENT = 'premium';

interface SubscriptionState {
  isConfigured: boolean;
  isLoading: boolean;
  isPremium: boolean;
  customerInfo: CustomerInfo | null;
  currentOffering: PurchasesOffering | null;
  packages: PurchasesPackage[];
  error: string | null;
  
  // Computed from real product data
  monthlyPrice: string | null;
  monthlyPriceValue: number | null;
  productTitle: string | null;
  billingPeriod: string | null;
  
  // Actions
  configure: (userId?: string) => Promise<void>;
  checkSubscriptionStatus: () => Promise<boolean>;
  purchasePackage: (pkg: PurchasesPackage) => Promise<boolean>;
  restorePurchases: () => Promise<boolean>;
  getOfferings: () => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
  identifyUser: (userId: string) => Promise<void>;
}

export const useSubscriptionStore = create<SubscriptionState>((set, get) => ({
  isConfigured: false,
  isLoading: false,
  isPremium: false,
  customerInfo: null,
  currentOffering: null,
  packages: [],
  error: null,
  monthlyPrice: null,
  monthlyPriceValue: null,
  productTitle: null,
  billingPeriod: null,

  configure: async (userId?: string) => {
    try {
      if (!REVENUECAT_API_KEY) {
        console.error('RevenueCat API key not configured');
        set({ error: 'Subscription service not configured' });
        return;
      }

      set({ isLoading: true, error: null });

      // Enable debug logging in development
      if (__DEV__) {
        Purchases.setLogLevel(LOG_LEVEL.DEBUG);
      }

      // Configure RevenueCat with the API key
      await Purchases.configure({ 
        apiKey: REVENUECAT_API_KEY,
        appUserID: userId || null
      });

      set({ isConfigured: true });

      // Check initial subscription status
      await get().checkSubscriptionStatus();
      
      // Fetch available offerings/products
      await get().getOfferings();

      set({ isLoading: false });
    } catch (error: any) {
      console.error('RevenueCat configure error:', error);
      set({ 
        isLoading: false, 
        error: error.message || 'Failed to initialize subscription service'
      });
    }
  },

  identifyUser: async (userId: string) => {
    try {
      if (!get().isConfigured) {
        await get().configure(userId);
        return;
      }
      
      // Log in the user to RevenueCat
      const { customerInfo } = await Purchases.logIn(userId);
      const isPremium = customerInfo.entitlements.active[PREMIUM_ENTITLEMENT]?.isActive ?? false;
      
      set({ customerInfo, isPremium });
    } catch (error: any) {
      console.error('RevenueCat identify error:', error);
    }
  },

  checkSubscriptionStatus: async () => {
    try {
      // TESTER BYPASS: Check if user is a tester - bypass paywall
      const authStore = useAuthStore.getState();
      if (authStore.user?.is_tester || authStore.user?.subscription_status === 'active') {
        console.log('Tester/Active subscription bypass - granting premium access');
        set({ isPremium: true });
        return true;
      }
      
      const customerInfo = await Purchases.getCustomerInfo();
      
      // Check if user has active premium entitlement
      const premiumEntitlement = customerInfo.entitlements.active[PREMIUM_ENTITLEMENT];
      const isPremium = premiumEntitlement?.isActive ?? false;
      
      set({ customerInfo, isPremium });

      // Sync status with backend
      try {
        await api.post('/subscription/sync', {
          is_premium: isPremium,
          entitlements: Object.keys(customerInfo.entitlements.active),
          expires_at: premiumEntitlement?.expirationDate || null,
          product_id: premiumEntitlement?.productIdentifier || null
        });
      } catch (e) {
        // Non-critical - continue if backend sync fails
        console.warn('Backend subscription sync failed:', e);
      }

      return isPremium;
    } catch (error: any) {
      // If RevenueCat fails, check if user is tester/has active status from backend
      const authStore = useAuthStore.getState();
      if (authStore.user?.is_tester || authStore.user?.subscription_status === 'active') {
        console.log('RevenueCat error but tester/active - granting premium access');
        set({ isPremium: true });
        return true;
      }
      
      console.error('Check subscription status error:', error);
      set({ error: error.message || 'Failed to check subscription status' });
      return false;
    }
  },

  getOfferings: async () => {
    try {
      const offerings = await Purchases.getOfferings();
      
      if (offerings.current) {
        const packages = offerings.current.availablePackages;
        
        // Find monthly package
        const monthlyPackage = packages.find(p => 
          p.packageType === 'MONTHLY' || 
          p.identifier.toLowerCase().includes('monthly') ||
          p.identifier === '$rc_monthly'
        ) || packages[0];
        
        let monthlyPrice = null;
        let monthlyPriceValue = null;
        let productTitle = null;
        let billingPeriod = null;
        
        if (monthlyPackage) {
          monthlyPrice = monthlyPackage.product.priceString;
          monthlyPriceValue = monthlyPackage.product.price;
          productTitle = monthlyPackage.product.title;
          
          // Determine billing period from package type
          switch (monthlyPackage.packageType) {
            case 'MONTHLY':
              billingPeriod = 'month';
              break;
            case 'ANNUAL':
              billingPeriod = 'year';
              break;
            case 'WEEKLY':
              billingPeriod = 'week';
              break;
            case 'THREE_MONTH':
              billingPeriod = '3 months';
              break;
            case 'SIX_MONTH':
              billingPeriod = '6 months';
              break;
            default:
              billingPeriod = 'month';
          }
        }
        
        set({ 
          currentOffering: offerings.current,
          packages,
          monthlyPrice,
          monthlyPriceValue,
          productTitle,
          billingPeriod
        });
      } else {
        console.warn('No current offering available from RevenueCat');
        set({ 
          packages: [],
          error: 'No subscription products available'
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

      // Initiate the real App Store purchase
      const { customerInfo } = await Purchases.purchasePackage(pkg);
      
      // Check if premium entitlement is now active
      const isPremium = customerInfo.entitlements.active[PREMIUM_ENTITLEMENT]?.isActive ?? false;

      set({ 
        customerInfo, 
        isPremium,
        isLoading: false 
      });

      // Notify backend of successful purchase
      if (isPremium) {
        try {
          await api.post('/subscription/verify', {
            action: 'purchase',
            product_id: pkg.product.identifier,
            is_premium: true,
            price: pkg.product.price,
            currency: pkg.product.currencyCode
          });
        } catch (e) {
          console.warn('Backend purchase notification failed:', e);
        }
      }

      return isPremium;
    } catch (error: any) {
      set({ isLoading: false });

      // Handle user cancellation - not an error
      if (error.code === PURCHASES_ERROR_CODE.PURCHASE_CANCELLED_ERROR) {
        return false;
      }

      // Handle specific purchase errors
      let errorMessage = 'Purchase failed';
      
      switch (error.code) {
        case PURCHASES_ERROR_CODE.PRODUCT_NOT_AVAILABLE_FOR_PURCHASE_ERROR:
          errorMessage = 'This subscription is not available in your region';
          break;
        case PURCHASES_ERROR_CODE.PURCHASE_NOT_ALLOWED_ERROR:
          errorMessage = 'Purchases are not allowed on this device. Please check your device settings.';
          break;
        case PURCHASES_ERROR_CODE.PAYMENT_PENDING_ERROR:
          errorMessage = 'Payment is pending. Please check your payment method and try again.';
          break;
        case PURCHASES_ERROR_CODE.NETWORK_ERROR:
          errorMessage = 'Network error. Please check your internet connection and try again.';
          break;
        case PURCHASES_ERROR_CODE.PRODUCT_ALREADY_PURCHASED_ERROR:
          errorMessage = 'You already have an active subscription. Try restoring purchases.';
          break;
        case PURCHASES_ERROR_CODE.RECEIPT_ALREADY_IN_USE_ERROR:
          errorMessage = 'This purchase is associated with another account.';
          break;
        case PURCHASES_ERROR_CODE.INVALID_CREDENTIALS_ERROR:
          errorMessage = 'Invalid App Store credentials. Please sign in to the App Store.';
          break;
        case PURCHASES_ERROR_CODE.UNEXPECTED_BACKEND_RESPONSE_ERROR:
          errorMessage = 'Server error. Please try again later.';
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

      // Restore purchases from App Store
      const customerInfo = await Purchases.restorePurchases();
      
      // Check if premium entitlement was restored
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
          is_premium: isPremium,
          entitlements: Object.keys(customerInfo.entitlements.active)
        });
      } catch (e) {
        console.warn('Backend restore notification failed:', e);
      }

      return isPremium;
    } catch (error: any) {
      console.error('Restore purchases error:', error);
      set({ 
        isLoading: false,
        error: error.message || 'Failed to restore purchases. Please try again.'
      });
      return false;
    }
  },

  logout: async () => {
    try {
      // Log out from RevenueCat
      await Purchases.logOut();
      
      set({ 
        customerInfo: null, 
        isPremium: false,
        isConfigured: false,
        packages: [],
        currentOffering: null,
        monthlyPrice: null,
        monthlyPriceValue: null,
        productTitle: null,
        billingPeriod: null
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

// Hook for getting subscription display info
export const useSubscriptionInfo = () => {
  const { 
    monthlyPrice, 
    monthlyPriceValue,
    productTitle,
    billingPeriod,
    isPremium,
    customerInfo,
    isLoading
  } = useSubscriptionStore();
  
  // Get expiration date if premium
  const expirationDate = isPremium && customerInfo?.entitlements.active[PREMIUM_ENTITLEMENT]?.expirationDate
    ? new Date(customerInfo.entitlements.active[PREMIUM_ENTITLEMENT].expirationDate)
    : null;
  
  return {
    price: monthlyPrice,
    priceValue: monthlyPriceValue,
    title: productTitle,
    period: billingPeriod,
    isPremium,
    expirationDate,
    isLoading
  };
};
