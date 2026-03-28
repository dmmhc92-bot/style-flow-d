// ═══════════════════════════════════════════════════════════════════════════════
// LOCAL VAULT - Offline-First Data Storage
// ═══════════════════════════════════════════════════════════════════════════════
// IMPLEMENT_SYNCED_LOOKBOOK_SYSTEM
//
// Features:
//   - In-memory storage with AsyncStorage persistence
//   - Profile bio/data caching
//   - Lookbook/Portfolio local storage
//   - Sync queue for pending operations
//
// Note: Uses AsyncStorage for persistence (works on both web and native)
// ═══════════════════════════════════════════════════════════════════════════════

import AsyncStorage from '@react-native-async-storage/async-storage';

// Storage keys
const KEYS = {
  PROFILES: '@vault_profiles',
  LOOKBOOK: '@vault_lookbook',
  SYNC_QUEUE: '@vault_sync_queue',
  PROFILE_EDITS: '@vault_profile_edits',
};

// In-memory cache for fast access
const memoryCache = {
  profiles: new Map<string, any>(),
  lookbook: new Map<string, any>(),
  syncQueue: [] as any[],
  profileEdits: [] as any[],
  initialized: false,
};

// ==================== INITIALIZE ====================

export const initDatabase = async (): Promise<void> => {
  if (memoryCache.initialized) return;
  
  try {
    // Load from AsyncStorage into memory
    const [profiles, lookbook, syncQueue, edits] = await Promise.all([
      AsyncStorage.getItem(KEYS.PROFILES),
      AsyncStorage.getItem(KEYS.LOOKBOOK),
      AsyncStorage.getItem(KEYS.SYNC_QUEUE),
      AsyncStorage.getItem(KEYS.PROFILE_EDITS),
    ]);
    
    if (profiles) {
      const parsed = JSON.parse(profiles);
      Object.entries(parsed).forEach(([k, v]) => memoryCache.profiles.set(k, v));
    }
    
    if (lookbook) {
      const parsed = JSON.parse(lookbook);
      Object.entries(parsed).forEach(([k, v]) => memoryCache.lookbook.set(k, v));
    }
    
    if (syncQueue) {
      memoryCache.syncQueue = JSON.parse(syncQueue);
    }
    
    if (edits) {
      memoryCache.profileEdits = JSON.parse(edits);
    }
    
    memoryCache.initialized = true;
    console.log('[Vault] Initialized from AsyncStorage');
  } catch (error) {
    console.warn('[Vault] Init failed:', error);
    memoryCache.initialized = true;
  }
};

// Persist to AsyncStorage
const persistProfiles = async () => {
  const obj: Record<string, any> = {};
  memoryCache.profiles.forEach((v, k) => obj[k] = v);
  await AsyncStorage.setItem(KEYS.PROFILES, JSON.stringify(obj));
};

const persistLookbook = async () => {
  const obj: Record<string, any> = {};
  memoryCache.lookbook.forEach((v, k) => obj[k] = v);
  await AsyncStorage.setItem(KEYS.LOOKBOOK, JSON.stringify(obj));
};

const persistSyncQueue = async () => {
  await AsyncStorage.setItem(KEYS.SYNC_QUEUE, JSON.stringify(memoryCache.syncQueue));
};

const persistProfileEdits = async () => {
  await AsyncStorage.setItem(KEYS.PROFILE_EDITS, JSON.stringify(memoryCache.profileEdits));
};

// ==================== PROFILE CACHE ====================

export const cacheProfile = async (userId: string, profileData: any): Promise<void> => {
  const key = `profile_${userId}`;
  memoryCache.profiles.set(key, { data: profileData, updated_at: Date.now() });
  await persistProfiles();
};

export const getCachedProfile = async (userId: string): Promise<any | null> => {
  const key = `profile_${userId}`;
  const cached = memoryCache.profiles.get(key);
  return cached?.data || null;
};

// ==================== LOOKBOOK ITEMS ====================

export interface LookbookItem {
  id: string;
  user_id: string;
  image_data: string;
  caption?: string;
  is_synced: boolean;
  created_at: number;
}

export const saveLookbookItem = async (
  userId: string,
  imageData: string,
  caption?: string
): Promise<string> => {
  const id = `local_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  const now = Date.now();
  
  const item: LookbookItem = {
    id,
    user_id: userId,
    image_data: imageData,
    caption,
    is_synced: false,
    created_at: now,
  };
  
  memoryCache.lookbook.set(id, item);
  await persistLookbook();
  
  // Add to sync queue
  await addToSyncQueue('lookbook_upload', '/profiles/portfolio', 'POST', {
    localId: id,
    image_base64: imageData,
    caption,
  });
  
  return id;
};

export const getLocalLookbookItems = async (userId: string): Promise<LookbookItem[]> => {
  const items: LookbookItem[] = [];
  
  memoryCache.lookbook.forEach((item) => {
    if (item.user_id === userId) {
      items.push(item);
    }
  });
  
  return items.sort((a, b) => b.created_at - a.created_at);
};

export const markLookbookItemSynced = async (localId: string, serverId: string): Promise<void> => {
  const item = memoryCache.lookbook.get(localId);
  if (item) {
    item.is_synced = true;
    item.id = serverId;
    memoryCache.lookbook.delete(localId);
    memoryCache.lookbook.set(serverId, item);
    await persistLookbook();
  }
};

export const deleteLookbookItem = async (itemId: string): Promise<void> => {
  memoryCache.lookbook.delete(itemId);
  await persistLookbook();
};

// ==================== PROFILE EDITS ====================

export const saveProfileEdit = async (
  userId: string,
  fieldName: string,
  fieldValue: any
): Promise<void> => {
  const now = Date.now();
  const valueStr = typeof fieldValue === 'object' ? JSON.stringify(fieldValue) : String(fieldValue);
  
  memoryCache.profileEdits.push({
    user_id: userId,
    field_name: fieldName,
    field_value: valueStr,
    is_synced: false,
    created_at: now,
  });
  
  await persistProfileEdits();
};

export const getPendingProfileEdits = async (userId: string): Promise<Record<string, any>> => {
  const edits: Record<string, any> = {};
  
  memoryCache.profileEdits
    .filter(e => e.user_id === userId && !e.is_synced)
    .forEach(e => {
      try {
        edits[e.field_name] = JSON.parse(e.field_value);
      } catch {
        edits[e.field_name] = e.field_value;
      }
    });
  
  return edits;
};

export const markProfileEditsSynced = async (userId: string): Promise<void> => {
  memoryCache.profileEdits
    .filter(e => e.user_id === userId)
    .forEach(e => e.is_synced = true);
  
  await persistProfileEdits();
};

// ==================== SYNC QUEUE ====================

export interface SyncQueueItem {
  id: number;
  operation: string;
  endpoint: string;
  method: string;
  payload: any;
  created_at: number;
  retry_count: number;
  status: string;
}

let syncQueueId = Date.now();

export const addToSyncQueue = async (
  operation: string,
  endpoint: string,
  method: string,
  payload: any
): Promise<void> => {
  const item: SyncQueueItem = {
    id: ++syncQueueId,
    operation,
    endpoint,
    method,
    payload,
    created_at: Date.now(),
    retry_count: 0,
    status: 'pending',
  };
  
  memoryCache.syncQueue.push(item);
  await persistSyncQueue();
};

export const getPendingSyncItems = async (): Promise<SyncQueueItem[]> => {
  return memoryCache.syncQueue.filter(i => i.status === 'pending');
};

export const markSyncItemComplete = async (id: number): Promise<void> => {
  const idx = memoryCache.syncQueue.findIndex(i => i.id === id);
  if (idx >= 0) {
    memoryCache.syncQueue.splice(idx, 1);
    await persistSyncQueue();
  }
};

export const incrementSyncRetry = async (id: number): Promise<void> => {
  const item = memoryCache.syncQueue.find(i => i.id === id);
  if (item) {
    item.retry_count++;
    await persistSyncQueue();
  }
};

export const markSyncItemFailed = async (id: number): Promise<void> => {
  const item = memoryCache.syncQueue.find(i => i.id === id);
  if (item) {
    item.status = 'failed';
    await persistSyncQueue();
  }
};

// ==================== UTILITY ====================

export const clearAllLocalData = async (): Promise<void> => {
  memoryCache.profiles.clear();
  memoryCache.lookbook.clear();
  memoryCache.syncQueue.length = 0;
  memoryCache.profileEdits.length = 0;
  
  await Promise.all([
    AsyncStorage.removeItem(KEYS.PROFILES),
    AsyncStorage.removeItem(KEYS.LOOKBOOK),
    AsyncStorage.removeItem(KEYS.SYNC_QUEUE),
    AsyncStorage.removeItem(KEYS.PROFILE_EDITS),
  ]);
};

export const getLocalDataStats = async (): Promise<{
  cachedProfiles: number;
  lookbookItems: number;
  pendingSync: number;
  pendingEdits: number;
}> => {
  return {
    cachedProfiles: memoryCache.profiles.size,
    lookbookItems: Array.from(memoryCache.lookbook.values()).filter(i => !i.is_synced).length,
    pendingSync: memoryCache.syncQueue.filter(i => i.status === 'pending').length,
    pendingEdits: memoryCache.profileEdits.filter(e => !e.is_synced).length,
  };
};

export default {
  initDatabase,
  cacheProfile,
  getCachedProfile,
  saveLookbookItem,
  getLocalLookbookItems,
  markLookbookItemSynced,
  deleteLookbookItem,
  saveProfileEdit,
  getPendingProfileEdits,
  markProfileEditsSynced,
  addToSyncQueue,
  getPendingSyncItems,
  markSyncItemComplete,
  incrementSyncRetry,
  markSyncItemFailed,
  clearAllLocalData,
  getLocalDataStats,
};
