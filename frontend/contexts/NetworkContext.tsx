import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import NetInfo, { NetInfoState } from '@react-native-community/netinfo';
import { offlineStorage, SyncQueueItem } from '../utils/offlineStorage';
import api from '../utils/api';
import { useAuthStore } from '../store/authStore';

interface NetworkContextType {
  isOnline: boolean;
  isSyncing: boolean;
  pendingChanges: number;
  syncNow: () => Promise<void>;
  lastSyncTime: Date | null;
}

const NetworkContext = createContext<NetworkContextType>({
  isOnline: true,
  isSyncing: false,
  pendingChanges: 0,
  syncNow: async () => {},
  lastSyncTime: null,
});

export const useNetwork = () => useContext(NetworkContext);

export const NetworkProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isOnline, setIsOnline] = useState(true);
  const [isSyncing, setIsSyncing] = useState(false);
  const [pendingChanges, setPendingChanges] = useState(0);
  const [lastSyncTime, setLastSyncTime] = useState<Date | null>(null);
  const syncInProgress = useRef(false);
  const user = useAuthStore((state) => state.user);

  // Check pending changes count
  const updatePendingChanges = useCallback(async () => {
    const queue = await offlineStorage.getSyncQueue();
    setPendingChanges(queue.length);
  }, []);

  // Process a single sync queue item
  const processSyncItem = async (item: SyncQueueItem): Promise<boolean> => {
    try {
      switch (item.type) {
        case 'clients':
          if (item.action === 'create') {
            const response = await api.post('/clients', item.data);
            // Update local ID to server ID
            if (item.localId) {
              await offlineStorage.updateLocalIdToServerId('clients', item.localId, response.data.id);
            }
          } else if (item.action === 'update') {
            await api.put(`/clients/${item.data.id}`, item.data);
          } else if (item.action === 'delete') {
            await api.delete(`/clients/${item.data.id}`);
          }
          break;

        case 'appointments':
          if (item.action === 'create') {
            const response = await api.post('/appointments', item.data);
            if (item.localId) {
              await offlineStorage.updateLocalIdToServerId('appointments', item.localId, response.data.id);
            }
          } else if (item.action === 'update') {
            await api.put(`/appointments/${item.data.id}`, item.data);
          } else if (item.action === 'delete') {
            await api.delete(`/appointments/${item.data.id}`);
          }
          break;

        case 'formulas':
          if (item.action === 'create') {
            const response = await api.post('/formulas', item.data);
            if (item.localId) {
              await offlineStorage.updateLocalIdToServerId('formulas', item.localId, response.data.id);
            }
          } else if (item.action === 'update') {
            await api.put(`/formulas/${item.data.id}`, item.data);
          } else if (item.action === 'delete') {
            await api.delete(`/formulas/${item.data.id}`);
          }
          break;
      }
      return true;
    } catch (error) {
      console.error(`Sync failed for ${item.type} ${item.action}:`, error);
      return false;
    }
  };

  // Sync all pending changes
  const syncNow = useCallback(async () => {
    if (syncInProgress.current || !isOnline) return;
    
    syncInProgress.current = true;
    setIsSyncing(true);

    try {
      const queue = await offlineStorage.getSyncQueue();
      
      // Sort by timestamp (oldest first)
      const sortedQueue = queue.sort((a, b) => a.timestamp - b.timestamp);

      for (const item of sortedQueue) {
        const success = await processSyncItem(item);
        if (success) {
          await offlineStorage.removeFromSyncQueue(item.id);
        }
      }

      // After syncing queue, pull fresh data from server
      await refreshFromServer();
      
      setLastSyncTime(new Date());
    } catch (error) {
      console.error('Sync error:', error);
    } finally {
      setIsSyncing(false);
      syncInProgress.current = false;
      await updatePendingChanges();
    }
  }, [isOnline]);

  // Pull fresh data from server and merge
  const refreshFromServer = async () => {
    try {
      const [clientsRes, appointmentsRes, formulasRes] = await Promise.all([
        api.get('/clients').catch(() => ({ data: null })),
        api.get('/appointments').catch(() => ({ data: null })),
        api.get('/formulas').catch(() => ({ data: null })),
      ]);

      if (clientsRes.data) {
        await offlineStorage.mergeClientsFromServer(clientsRes.data);
      }
      if (appointmentsRes.data) {
        await offlineStorage.mergeAppointmentsFromServer(appointmentsRes.data);
      }
      if (formulasRes.data) {
        await offlineStorage.mergeFormulasFromServer(formulasRes.data);
      }
    } catch (error) {
      console.error('Error refreshing from server:', error);
    }
  };

  // Handle network state changes
  useEffect(() => {
    const unsubscribe = NetInfo.addEventListener((state: NetInfoState) => {
      const online = state.isConnected ?? false;
      setIsOnline(online);
      
      // Auto-sync when coming back online
      if (online && !syncInProgress.current) {
        syncNow();
      }
    });

    // Initial check
    NetInfo.fetch().then((state) => {
      setIsOnline(state.isConnected ?? false);
    });

    return () => unsubscribe();
  }, [syncNow]);

  // Update pending changes count periodically
  useEffect(() => {
    updatePendingChanges();
    const interval = setInterval(updatePendingChanges, 5000);
    return () => clearInterval(interval);
  }, [updatePendingChanges]);

  // Set user ID when user changes
  useEffect(() => {
    if (user?.id) {
      offlineStorage.setUserId(user.id);
      // Initial sync when user logs in
      if (isOnline) {
        syncNow();
      }
    } else {
      offlineStorage.clearUserId();
    }
  }, [user?.id, isOnline, syncNow]);

  return (
    <NetworkContext.Provider
      value={{
        isOnline,
        isSyncing,
        pendingChanges,
        syncNow,
        lastSyncTime,
      }}
    >
      {children}
    </NetworkContext.Provider>
  );
};
