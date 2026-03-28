// ═══════════════════════════════════════════════════════════════════════════════
// SYNC SERVICE - The "Waiting Room" for Offline Changes
// ═══════════════════════════════════════════════════════════════════════════════
// IMPLEMENT_SYNCED_LOOKBOOK_SYSTEM
//
// Features:
//   - Network connectivity monitoring
//   - Automatic sync when service returns
//   - Retry logic with exponential backoff
//   - Backend is the final authority after sync
// ═══════════════════════════════════════════════════════════════════════════════

import { create } from 'zustand';
import NetInfo, { NetInfoState } from '@react-native-community/netinfo';
import { Platform } from 'react-native';
import api from './api';
import {
  initDatabase,
  getPendingSyncItems,
  markSyncItemComplete,
  incrementSyncRetry,
  markSyncItemFailed,
  markLookbookItemSynced,
  markProfileEditsSynced,
  getLocalDataStats,
  SyncQueueItem,
} from './localVault';

// ==================== SYNC STORE ====================

interface SyncState {
  isOnline: boolean;
  isSyncing: boolean;
  lastSyncAt: number | null;
  pendingCount: number;
  syncError: string | null;
  
  // Actions
  setOnline: (online: boolean) => void;
  setSyncing: (syncing: boolean) => void;
  setLastSync: (timestamp: number) => void;
  setPendingCount: (count: number) => void;
  setSyncError: (error: string | null) => void;
}

export const useSyncStore = create<SyncState>((set) => ({
  isOnline: true,
  isSyncing: false,
  lastSyncAt: null,
  pendingCount: 0,
  syncError: null,
  
  setOnline: (online) => set({ isOnline: online }),
  setSyncing: (syncing) => set({ isSyncing: syncing }),
  setLastSync: (timestamp) => set({ lastSyncAt: timestamp }),
  setPendingCount: (count) => set({ pendingCount: count }),
  setSyncError: (error) => set({ syncError: error }),
}));

// ==================== SYNC SERVICE CLASS ====================

class SyncService {
  private static instance: SyncService;
  private isInitialized = false;
  private syncInProgress = false;
  private unsubscribeNetInfo: (() => void) | null = null;
  
  private constructor() {}
  
  static getInstance(): SyncService {
    if (!SyncService.instance) {
      SyncService.instance = new SyncService();
    }
    return SyncService.instance;
  }
  
  async initialize(): Promise<void> {
    if (this.isInitialized) return;
    
    console.log('[SyncService] Initializing...');
    
    // Initialize local database
    await initDatabase();
    
    // Start network monitoring
    this.startNetworkMonitoring();
    
    // Check initial connectivity and sync if online
    const state = await NetInfo.fetch();
    const isConnected = this.checkConnectivity(state);
    useSyncStore.getState().setOnline(isConnected);
    
    if (isConnected) {
      // Delay initial sync slightly to let app settle
      setTimeout(() => this.syncPendingChanges(), 2000);
    }
    
    // Update pending count
    await this.updatePendingCount();
    
    this.isInitialized = true;
    console.log('[SyncService] Initialized successfully');
  }
  
  private checkConnectivity(state: NetInfoState): boolean {
    if (Platform.OS === 'web') {
      return navigator.onLine;
    }
    return state.isConnected === true && state.isInternetReachable !== false;
  }
  
  private startNetworkMonitoring(): void {
    if (Platform.OS === 'web') {
      // Web fallback
      window.addEventListener('online', () => this.handleConnectivityChange(true));
      window.addEventListener('offline', () => this.handleConnectivityChange(false));
      return;
    }
    
    this.unsubscribeNetInfo = NetInfo.addEventListener((state) => {
      const isConnected = this.checkConnectivity(state);
      this.handleConnectivityChange(isConnected);
    });
  }
  
  private async handleConnectivityChange(isOnline: boolean): Promise<void> {
    const store = useSyncStore.getState();
    const wasOffline = !store.isOnline;
    
    store.setOnline(isOnline);
    
    console.log(`[SyncService] Connectivity changed: ${isOnline ? 'ONLINE' : 'OFFLINE'}`);
    
    // If we just came online, trigger sync
    if (isOnline && wasOffline) {
      console.log('[SyncService] Connection restored - starting sync...');
      await this.syncPendingChanges();
    }
  }
  
  async updatePendingCount(): Promise<void> {
    const stats = await getLocalDataStats();
    const total = stats.pendingSync + stats.lookbookItems + stats.pendingEdits;
    useSyncStore.getState().setPendingCount(total);
  }
  
  // ==================== MAIN SYNC LOGIC ====================
  
  async syncPendingChanges(): Promise<void> {
    const store = useSyncStore.getState();
    
    if (!store.isOnline) {
      console.log('[SyncService] Offline - skipping sync');
      return;
    }
    
    if (this.syncInProgress) {
      console.log('[SyncService] Sync already in progress');
      return;
    }
    
    this.syncInProgress = true;
    store.setSyncing(true);
    store.setSyncError(null);
    
    console.log('[SyncService] Starting sync...');
    
    try {
      // Get all pending items from sync queue
      const pendingItems = await getPendingSyncItems();
      console.log(`[SyncService] Found ${pendingItems.length} pending items`);
      
      let successCount = 0;
      let failCount = 0;
      
      for (const item of pendingItems) {
        const success = await this.processSyncItem(item);
        if (success) {
          successCount++;
        } else {
          failCount++;
        }
      }
      
      // Update pending count
      await this.updatePendingCount();
      
      // Set last sync time
      store.setLastSync(Date.now());
      
      console.log(`[SyncService] Sync complete: ${successCount} success, ${failCount} failed`);
      
    } catch (error: any) {
      console.error('[SyncService] Sync error:', error);
      store.setSyncError(error.message || 'Sync failed');
    } finally {
      this.syncInProgress = false;
      store.setSyncing(false);
    }
  }
  
  private async processSyncItem(item: SyncQueueItem): Promise<boolean> {
    const MAX_RETRIES = 3;
    
    try {
      console.log(`[SyncService] Processing: ${item.operation} -> ${item.endpoint}`);
      
      let response;
      
      switch (item.method.toUpperCase()) {
        case 'POST':
          response = await api.post(item.endpoint, item.payload);
          break;
        case 'PUT':
          response = await api.put(item.endpoint, item.payload);
          break;
        case 'PATCH':
          response = await api.patch(item.endpoint, item.payload);
          break;
        case 'DELETE':
          response = await api.delete(item.endpoint);
          break;
        default:
          response = await api.get(item.endpoint);
      }
      
      // Handle special cases for lookbook uploads
      if (item.operation === 'lookbook_upload' && response.data.success) {
        const localId = item.payload.localId;
        const serverId = response.data.portfolio_id;
        await markLookbookItemSynced(localId, serverId);
      }
      
      // Mark as complete
      await markSyncItemComplete(item.id);
      return true;
      
    } catch (error: any) {
      console.error(`[SyncService] Failed to sync item ${item.id}:`, error.message);
      
      // Increment retry count
      await incrementSyncRetry(item.id);
      
      // Mark as failed if max retries exceeded
      if (item.retry_count >= MAX_RETRIES) {
        await markSyncItemFailed(item.id);
        console.log(`[SyncService] Item ${item.id} marked as failed after ${MAX_RETRIES} retries`);
      }
      
      return false;
    }
  }
  
  // ==================== MANUAL SYNC TRIGGER ====================
  
  async forceSyncNow(): Promise<boolean> {
    const store = useSyncStore.getState();
    
    if (!store.isOnline) {
      store.setSyncError('No internet connection');
      return false;
    }
    
    await this.syncPendingChanges();
    return true;
  }
  
  // ==================== CLEANUP ====================
  
  destroy(): void {
    if (this.unsubscribeNetInfo) {
      this.unsubscribeNetInfo();
      this.unsubscribeNetInfo = null;
    }
    
    if (Platform.OS === 'web') {
      window.removeEventListener('online', () => {});
      window.removeEventListener('offline', () => {});
    }
    
    this.isInitialized = false;
    console.log('[SyncService] Destroyed');
  }
}

// ==================== EXPORTS ====================

export const syncService = SyncService.getInstance();

// Hook for components to use sync status
export const useSyncStatus = () => {
  const { isOnline, isSyncing, lastSyncAt, pendingCount, syncError } = useSyncStore();
  
  return {
    isOnline,
    isSyncing,
    lastSyncAt,
    pendingCount,
    syncError,
    hasPendingChanges: pendingCount > 0,
    forceSyncNow: () => syncService.forceSyncNow(),
  };
};

export default syncService;
