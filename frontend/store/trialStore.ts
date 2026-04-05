import { create } from 'zustand';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Trial Configuration
const TRIAL_CONFIG = {
  MAX_FREE_USES: 3,  // Users get 3 free uses
  STORAGE_KEY: 'styleflow_trial_usage',
};

interface TrialUsage {
  clientsCreated: number;
  formulasCreated: number;
  appointmentsCreated: number;
  postsCreated: number;
  aiChatsUsed: number;
  lastResetDate: string;
}

interface TrialState {
  usage: TrialUsage;
  isLoading: boolean;
  
  // Actions
  loadUsage: () => Promise<void>;
  incrementUsage: (feature: keyof Omit<TrialUsage, 'lastResetDate'>) => Promise<boolean>;
  canUseFeature: (feature: keyof Omit<TrialUsage, 'lastResetDate'>) => boolean;
  getRemainingUses: (feature: keyof Omit<TrialUsage, 'lastResetDate'>) => number;
  getTotalUsage: () => number;
  resetUsage: () => Promise<void>;
  getTrialStatus: () => { totalUsed: number; maxFree: number; isTrialExpired: boolean };
}

const defaultUsage: TrialUsage = {
  clientsCreated: 0,
  formulasCreated: 0,
  appointmentsCreated: 0,
  postsCreated: 0,
  aiChatsUsed: 0,
  lastResetDate: new Date().toISOString(),
};

export const useTrialStore = create<TrialState>((set, get) => ({
  usage: defaultUsage,
  isLoading: false,

  loadUsage: async () => {
    try {
      set({ isLoading: true });
      const stored = await AsyncStorage.getItem(TRIAL_CONFIG.STORAGE_KEY);
      if (stored) {
        const usage = JSON.parse(stored) as TrialUsage;
        set({ usage, isLoading: false });
      } else {
        // Initialize with default usage
        await AsyncStorage.setItem(TRIAL_CONFIG.STORAGE_KEY, JSON.stringify(defaultUsage));
        set({ usage: defaultUsage, isLoading: false });
      }
    } catch (error) {
      console.error('Failed to load trial usage:', error);
      set({ isLoading: false });
    }
  },

  incrementUsage: async (feature) => {
    const { usage, canUseFeature } = get();
    
    // Check if user can still use this feature
    if (!canUseFeature(feature)) {
      return false; // Trial expired for this feature
    }
    
    const newUsage = {
      ...usage,
      [feature]: usage[feature] + 1,
    };
    
    try {
      await AsyncStorage.setItem(TRIAL_CONFIG.STORAGE_KEY, JSON.stringify(newUsage));
      set({ usage: newUsage });
      return true;
    } catch (error) {
      console.error('Failed to increment usage:', error);
      return false;
    }
  },

  canUseFeature: (feature) => {
    const { usage } = get();
    // Each feature gets 3 free uses
    return usage[feature] < TRIAL_CONFIG.MAX_FREE_USES;
  },

  getRemainingUses: (feature) => {
    const { usage } = get();
    return Math.max(0, TRIAL_CONFIG.MAX_FREE_USES - usage[feature]);
  },

  getTotalUsage: () => {
    const { usage } = get();
    return (
      usage.clientsCreated +
      usage.formulasCreated +
      usage.appointmentsCreated +
      usage.postsCreated +
      usage.aiChatsUsed
    );
  },

  resetUsage: async () => {
    try {
      await AsyncStorage.setItem(TRIAL_CONFIG.STORAGE_KEY, JSON.stringify(defaultUsage));
      set({ usage: defaultUsage });
    } catch (error) {
      console.error('Failed to reset usage:', error);
    }
  },

  getTrialStatus: () => {
    const { getTotalUsage } = get();
    const totalUsed = getTotalUsage();
    // Total free uses across ALL features (3 per feature * 5 features = 15 total)
    // But we use a simpler model: 3 total premium actions before paywall
    const maxFreeActions = TRIAL_CONFIG.MAX_FREE_USES;
    
    return {
      totalUsed,
      maxFree: maxFreeActions,
      isTrialExpired: totalUsed >= maxFreeActions,
    };
  },
}));

// Export config for external use
export const TRIAL_LIMITS = TRIAL_CONFIG;
