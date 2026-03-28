// ═══════════════════════════════════════════════════════════════════════════════
// LOCAL SQLITE VAULT - Offline-First Data Storage
// ═══════════════════════════════════════════════════════════════════════════════
// IMPLEMENT_SYNCED_LOOKBOOK_SYSTEM
//
// Features:
//   - Local SQLite storage for offline edits
//   - Profile bio/data caching
//   - Lookbook/Portfolio local storage
//   - Sync queue for pending operations
// ═══════════════════════════════════════════════════════════════════════════════

import * as SQLite from 'expo-sqlite';
import { Platform } from 'react-native';

// Database instance
let db: SQLite.SQLiteDatabase | null = null;

// Initialize database
export const initDatabase = async (): Promise<void> => {
  if (Platform.OS === 'web') {
    console.log('[SQLite] Web platform - using memory fallback');
    return;
  }
  
  try {
    db = await SQLite.openDatabaseAsync('styleflow_vault.db');
    
    // Create tables
    await db.execAsync(`
      -- Profile cache table
      CREATE TABLE IF NOT EXISTS profile_cache (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        data TEXT NOT NULL,
        updated_at INTEGER NOT NULL
      );
      
      -- Lookbook/Portfolio items
      CREATE TABLE IF NOT EXISTS lookbook_items (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        image_data TEXT NOT NULL,
        caption TEXT,
        is_synced INTEGER DEFAULT 0,
        created_at INTEGER NOT NULL,
        synced_at INTEGER
      );
      
      -- Sync queue for pending operations
      CREATE TABLE IF NOT EXISTS sync_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        operation TEXT NOT NULL,
        endpoint TEXT NOT NULL,
        method TEXT NOT NULL,
        payload TEXT NOT NULL,
        created_at INTEGER NOT NULL,
        retry_count INTEGER DEFAULT 0,
        status TEXT DEFAULT 'pending'
      );
      
      -- Profile edits pending sync
      CREATE TABLE IF NOT EXISTS profile_edits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        field_name TEXT NOT NULL,
        field_value TEXT,
        is_synced INTEGER DEFAULT 0,
        created_at INTEGER NOT NULL
      );
    `);
    
    console.log('[SQLite] Database initialized successfully');
  } catch (error) {
    console.error('[SQLite] Database initialization failed:', error);
  }
};

// ==================== PROFILE CACHE ====================

export const cacheProfile = async (userId: string, profileData: any): Promise<void> => {
  if (!db || Platform.OS === 'web') return;
  
  try {
    const now = Date.now();
    await db.runAsync(
      `INSERT OR REPLACE INTO profile_cache (id, user_id, data, updated_at) 
       VALUES (?, ?, ?, ?)`,
      [`profile_${userId}`, userId, JSON.stringify(profileData), now]
    );
  } catch (error) {
    console.error('[SQLite] Cache profile failed:', error);
  }
};

export const getCachedProfile = async (userId: string): Promise<any | null> => {
  if (!db || Platform.OS === 'web') return null;
  
  try {
    const result = await db.getFirstAsync<{ data: string }>(
      `SELECT data FROM profile_cache WHERE user_id = ?`,
      [userId]
    );
    return result ? JSON.parse(result.data) : null;
  } catch (error) {
    console.error('[SQLite] Get cached profile failed:', error);
    return null;
  }
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
  
  if (!db || Platform.OS === 'web') {
    // Web fallback - return ID for immediate use
    return id;
  }
  
  try {
    const now = Date.now();
    await db.runAsync(
      `INSERT INTO lookbook_items (id, user_id, image_data, caption, is_synced, created_at)
       VALUES (?, ?, ?, ?, 0, ?)`,
      [id, userId, imageData, caption || '', now]
    );
    
    // Add to sync queue
    await addToSyncQueue('lookbook_upload', '/profiles/portfolio', 'POST', {
      localId: id,
      image_base64: imageData,
      caption: caption,
    });
    
    return id;
  } catch (error) {
    console.error('[SQLite] Save lookbook item failed:', error);
    return id;
  }
};

export const getLocalLookbookItems = async (userId: string): Promise<LookbookItem[]> => {
  if (!db || Platform.OS === 'web') return [];
  
  try {
    const results = await db.getAllAsync<{
      id: string;
      user_id: string;
      image_data: string;
      caption: string;
      is_synced: number;
      created_at: number;
    }>(
      `SELECT * FROM lookbook_items WHERE user_id = ? ORDER BY created_at DESC`,
      [userId]
    );
    
    return results.map(row => ({
      id: row.id,
      user_id: row.user_id,
      image_data: row.image_data,
      caption: row.caption,
      is_synced: row.is_synced === 1,
      created_at: row.created_at,
    }));
  } catch (error) {
    console.error('[SQLite] Get lookbook items failed:', error);
    return [];
  }
};

export const markLookbookItemSynced = async (localId: string, serverId: string): Promise<void> => {
  if (!db || Platform.OS === 'web') return;
  
  try {
    await db.runAsync(
      `UPDATE lookbook_items SET is_synced = 1, id = ?, synced_at = ? WHERE id = ?`,
      [serverId, Date.now(), localId]
    );
  } catch (error) {
    console.error('[SQLite] Mark synced failed:', error);
  }
};

export const deleteLookbookItem = async (itemId: string): Promise<void> => {
  if (!db || Platform.OS === 'web') return;
  
  try {
    await db.runAsync(`DELETE FROM lookbook_items WHERE id = ?`, [itemId]);
  } catch (error) {
    console.error('[SQLite] Delete lookbook item failed:', error);
  }
};

// ==================== PROFILE EDITS ====================

export const saveProfileEdit = async (
  userId: string,
  fieldName: string,
  fieldValue: any
): Promise<void> => {
  if (!db || Platform.OS === 'web') return;
  
  try {
    const now = Date.now();
    const valueStr = typeof fieldValue === 'object' ? JSON.stringify(fieldValue) : String(fieldValue);
    
    await db.runAsync(
      `INSERT INTO profile_edits (user_id, field_name, field_value, is_synced, created_at)
       VALUES (?, ?, ?, 0, ?)`,
      [userId, fieldName, valueStr, now]
    );
  } catch (error) {
    console.error('[SQLite] Save profile edit failed:', error);
  }
};

export const getPendingProfileEdits = async (userId: string): Promise<Record<string, any>> => {
  if (!db || Platform.OS === 'web') return {};
  
  try {
    const results = await db.getAllAsync<{
      field_name: string;
      field_value: string;
    }>(
      `SELECT field_name, field_value FROM profile_edits 
       WHERE user_id = ? AND is_synced = 0 
       ORDER BY created_at DESC`,
      [userId]
    );
    
    const edits: Record<string, any> = {};
    results.forEach(row => {
      try {
        edits[row.field_name] = JSON.parse(row.field_value);
      } catch {
        edits[row.field_name] = row.field_value;
      }
    });
    
    return edits;
  } catch (error) {
    console.error('[SQLite] Get pending edits failed:', error);
    return {};
  }
};

export const markProfileEditsSynced = async (userId: string): Promise<void> => {
  if (!db || Platform.OS === 'web') return;
  
  try {
    await db.runAsync(
      `UPDATE profile_edits SET is_synced = 1 WHERE user_id = ? AND is_synced = 0`,
      [userId]
    );
  } catch (error) {
    console.error('[SQLite] Mark edits synced failed:', error);
  }
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

export const addToSyncQueue = async (
  operation: string,
  endpoint: string,
  method: string,
  payload: any
): Promise<void> => {
  if (!db || Platform.OS === 'web') return;
  
  try {
    const now = Date.now();
    await db.runAsync(
      `INSERT INTO sync_queue (operation, endpoint, method, payload, created_at, status)
       VALUES (?, ?, ?, ?, ?, 'pending')`,
      [operation, endpoint, method, JSON.stringify(payload), now]
    );
  } catch (error) {
    console.error('[SQLite] Add to sync queue failed:', error);
  }
};

export const getPendingSyncItems = async (): Promise<SyncQueueItem[]> => {
  if (!db || Platform.OS === 'web') return [];
  
  try {
    const results = await db.getAllAsync<{
      id: number;
      operation: string;
      endpoint: string;
      method: string;
      payload: string;
      created_at: number;
      retry_count: number;
      status: string;
    }>(
      `SELECT * FROM sync_queue WHERE status = 'pending' ORDER BY created_at ASC`
    );
    
    return results.map(row => ({
      ...row,
      payload: JSON.parse(row.payload),
    }));
  } catch (error) {
    console.error('[SQLite] Get pending sync items failed:', error);
    return [];
  }
};

export const markSyncItemComplete = async (id: number): Promise<void> => {
  if (!db || Platform.OS === 'web') return;
  
  try {
    await db.runAsync(`DELETE FROM sync_queue WHERE id = ?`, [id]);
  } catch (error) {
    console.error('[SQLite] Mark sync complete failed:', error);
  }
};

export const incrementSyncRetry = async (id: number): Promise<void> => {
  if (!db || Platform.OS === 'web') return;
  
  try {
    await db.runAsync(
      `UPDATE sync_queue SET retry_count = retry_count + 1 WHERE id = ?`,
      [id]
    );
  } catch (error) {
    console.error('[SQLite] Increment retry failed:', error);
  }
};

export const markSyncItemFailed = async (id: number): Promise<void> => {
  if (!db || Platform.OS === 'web') return;
  
  try {
    await db.runAsync(
      `UPDATE sync_queue SET status = 'failed' WHERE id = ?`,
      [id]
    );
  } catch (error) {
    console.error('[SQLite] Mark sync failed:', error);
  }
};

// ==================== UTILITY ====================

export const clearAllLocalData = async (): Promise<void> => {
  if (!db || Platform.OS === 'web') return;
  
  try {
    await db.execAsync(`
      DELETE FROM profile_cache;
      DELETE FROM lookbook_items;
      DELETE FROM sync_queue;
      DELETE FROM profile_edits;
    `);
  } catch (error) {
    console.error('[SQLite] Clear all data failed:', error);
  }
};

export const getLocalDataStats = async (): Promise<{
  cachedProfiles: number;
  lookbookItems: number;
  pendingSync: number;
  pendingEdits: number;
}> => {
  if (!db || Platform.OS === 'web') {
    return { cachedProfiles: 0, lookbookItems: 0, pendingSync: 0, pendingEdits: 0 };
  }
  
  try {
    const [profiles, lookbook, sync, edits] = await Promise.all([
      db.getFirstAsync<{ count: number }>(`SELECT COUNT(*) as count FROM profile_cache`),
      db.getFirstAsync<{ count: number }>(`SELECT COUNT(*) as count FROM lookbook_items WHERE is_synced = 0`),
      db.getFirstAsync<{ count: number }>(`SELECT COUNT(*) as count FROM sync_queue WHERE status = 'pending'`),
      db.getFirstAsync<{ count: number }>(`SELECT COUNT(*) as count FROM profile_edits WHERE is_synced = 0`),
    ]);
    
    return {
      cachedProfiles: profiles?.count || 0,
      lookbookItems: lookbook?.count || 0,
      pendingSync: sync?.count || 0,
      pendingEdits: edits?.count || 0,
    };
  } catch (error) {
    console.error('[SQLite] Get stats failed:', error);
    return { cachedProfiles: 0, lookbookItems: 0, pendingSync: 0, pendingEdits: 0 };
  }
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
