import { useState, useEffect, useCallback } from 'react';
import { useFocusEffect } from '@react-navigation/native';
import { useNetwork } from '../contexts/NetworkContext';
import { offlineStorage, LocalClient, LocalAppointment, LocalFormula } from '../utils/offlineStorage';
import api from '../utils/api';

// Hook for offline-first clients management
export function useOfflineClients() {
  const [clients, setClients] = useState<LocalClient[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const { isOnline, syncNow } = useNetwork();

  const loadClients = useCallback(async () => {
    try {
      // Always load from local first
      const localClients = await offlineStorage.getClients();
      setClients(localClients);

      // If online, fetch from server and merge
      if (isOnline) {
        try {
          const response = await api.get('/clients');
          await offlineStorage.mergeClientsFromServer(response.data);
          const updatedClients = await offlineStorage.getClients();
          setClients(updatedClients);
        } catch (error) {
          console.error('Failed to fetch clients from server:', error);
          // Keep using local data
        }
      }
    } catch (error) {
      console.error('Failed to load clients:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [isOnline]);

  useFocusEffect(
    useCallback(() => {
      loadClients();
    }, [loadClients])
  );

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadClients();
  }, [loadClients]);

  const addClient = useCallback(async (clientData: Omit<LocalClient, 'id'>) => {
    const localId = offlineStorage.generateLocalId();
    const newClient: LocalClient = {
      ...clientData,
      id: localId,
      localId,
      _pendingSync: true,
    };

    // Save locally immediately
    await offlineStorage.addClient(newClient);
    setClients(prev => [...prev, newClient]);

    // Queue for sync
    await offlineStorage.addToSyncQueue({
      type: 'clients',
      action: 'create',
      data: clientData,
      localId,
    });

    // Attempt immediate sync if online
    if (isOnline) {
      try {
        const response = await api.post('/clients', clientData);
        await offlineStorage.updateLocalIdToServerId('clients', localId, response.data.id);
        await offlineStorage.removeFromSyncQueue(localId);
        
        // Update local state with server response
        setClients(prev => prev.map(c => 
          c.localId === localId ? { ...response.data, _pendingSync: false } : c
        ));
      } catch (error) {
        console.error('Failed to sync client to server:', error);
        // Data is saved locally and queued, will sync later
      }
    }

    return newClient;
  }, [isOnline]);

  const updateClient = useCallback(async (id: string, updates: Partial<LocalClient>) => {
    // Update locally immediately
    const updatedClient = await offlineStorage.updateClient(id, updates);
    if (updatedClient) {
      setClients(prev => prev.map(c => c.id === id || c.localId === id ? updatedClient : c));
    }

    // Queue for sync (only if it's a server ID, not a local-only item)
    if (!id.startsWith('local_')) {
      await offlineStorage.addToSyncQueue({
        type: 'clients',
        action: 'update',
        data: { id, ...updates },
      });

      // Attempt immediate sync if online
      if (isOnline) {
        try {
          const response = await api.put(`/clients/${id}`, updates);
          setClients(prev => prev.map(c => 
            c.id === id ? { ...response.data, _pendingSync: false } : c
          ));
        } catch (error) {
          console.error('Failed to sync client update:', error);
        }
      }
    }

    return updatedClient;
  }, [isOnline]);

  const deleteClient = useCallback(async (id: string) => {
    // Mark as deleted locally immediately
    await offlineStorage.deleteClient(id);
    setClients(prev => prev.filter(c => c.id !== id && c.localId !== id));

    // Queue for sync (only if it's a server ID)
    if (!id.startsWith('local_')) {
      await offlineStorage.addToSyncQueue({
        type: 'clients',
        action: 'delete',
        data: { id },
      });

      // Attempt immediate sync if online
      if (isOnline) {
        try {
          await api.delete(`/clients/${id}`);
        } catch (error) {
          console.error('Failed to sync client deletion:', error);
        }
      }
    }
  }, [isOnline]);

  return {
    clients,
    loading,
    refreshing,
    onRefresh,
    addClient,
    updateClient,
    deleteClient,
  };
}

// Hook for offline-first appointments management
export function useOfflineAppointments() {
  const [appointments, setAppointments] = useState<LocalAppointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const { isOnline } = useNetwork();

  const loadAppointments = useCallback(async () => {
    try {
      const localAppointments = await offlineStorage.getAppointments();
      setAppointments(localAppointments);

      if (isOnline) {
        try {
          const response = await api.get('/appointments');
          await offlineStorage.mergeAppointmentsFromServer(response.data);
          const updated = await offlineStorage.getAppointments();
          setAppointments(updated);
        } catch (error) {
          console.error('Failed to fetch appointments from server:', error);
        }
      }
    } catch (error) {
      console.error('Failed to load appointments:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [isOnline]);

  useFocusEffect(
    useCallback(() => {
      loadAppointments();
    }, [loadAppointments])
  );

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadAppointments();
  }, [loadAppointments]);

  const addAppointment = useCallback(async (appointmentData: Omit<LocalAppointment, 'id'>) => {
    const localId = offlineStorage.generateLocalId();
    const newAppointment: LocalAppointment = {
      ...appointmentData,
      id: localId,
      localId,
      _pendingSync: true,
    };

    await offlineStorage.addAppointment(newAppointment);
    setAppointments(prev => [...prev, newAppointment]);

    await offlineStorage.addToSyncQueue({
      type: 'appointments',
      action: 'create',
      data: appointmentData,
      localId,
    });

    if (isOnline) {
      try {
        const response = await api.post('/appointments', appointmentData);
        await offlineStorage.updateLocalIdToServerId('appointments', localId, response.data.id);
        setAppointments(prev => prev.map(a => 
          a.localId === localId ? { ...response.data, _pendingSync: false } : a
        ));
      } catch (error) {
        console.error('Failed to sync appointment to server:', error);
      }
    }

    return newAppointment;
  }, [isOnline]);

  const updateAppointment = useCallback(async (id: string, updates: Partial<LocalAppointment>) => {
    const updated = await offlineStorage.updateAppointment(id, updates);
    if (updated) {
      setAppointments(prev => prev.map(a => a.id === id || a.localId === id ? updated : a));
    }

    if (!id.startsWith('local_')) {
      await offlineStorage.addToSyncQueue({
        type: 'appointments',
        action: 'update',
        data: { id, ...updates },
      });

      if (isOnline) {
        try {
          const response = await api.put(`/appointments/${id}`, updates);
          setAppointments(prev => prev.map(a => 
            a.id === id ? { ...response.data, _pendingSync: false } : a
          ));
        } catch (error) {
          console.error('Failed to sync appointment update:', error);
        }
      }
    }

    return updated;
  }, [isOnline]);

  const deleteAppointment = useCallback(async (id: string) => {
    await offlineStorage.deleteAppointment(id);
    setAppointments(prev => prev.filter(a => a.id !== id && a.localId !== id));

    if (!id.startsWith('local_')) {
      await offlineStorage.addToSyncQueue({
        type: 'appointments',
        action: 'delete',
        data: { id },
      });

      if (isOnline) {
        try {
          await api.delete(`/appointments/${id}`);
        } catch (error) {
          console.error('Failed to sync appointment deletion:', error);
        }
      }
    }
  }, [isOnline]);

  return {
    appointments,
    loading,
    refreshing,
    onRefresh,
    addAppointment,
    updateAppointment,
    deleteAppointment,
  };
}

// Hook for offline-first formulas management
export function useOfflineFormulas(clientId?: string) {
  const [formulas, setFormulas] = useState<LocalFormula[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const { isOnline } = useNetwork();

  const loadFormulas = useCallback(async () => {
    try {
      let localFormulas = await offlineStorage.getFormulas();
      
      // Filter by clientId if provided
      if (clientId) {
        localFormulas = localFormulas.filter(f => f.client_id === clientId);
      }
      
      setFormulas(localFormulas);

      if (isOnline) {
        try {
          const url = clientId ? `/formulas?client_id=${clientId}` : '/formulas';
          const response = await api.get(url);
          await offlineStorage.mergeFormulasFromServer(response.data);
          let updated = await offlineStorage.getFormulas();
          if (clientId) {
            updated = updated.filter(f => f.client_id === clientId);
          }
          setFormulas(updated);
        } catch (error) {
          console.error('Failed to fetch formulas from server:', error);
        }
      }
    } catch (error) {
      console.error('Failed to load formulas:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [isOnline, clientId]);

  useFocusEffect(
    useCallback(() => {
      loadFormulas();
    }, [loadFormulas])
  );

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadFormulas();
  }, [loadFormulas]);

  const addFormula = useCallback(async (formulaData: Omit<LocalFormula, 'id'>) => {
    const localId = offlineStorage.generateLocalId();
    const newFormula: LocalFormula = {
      ...formulaData,
      id: localId,
      localId,
      date_created: new Date().toISOString(),
      _pendingSync: true,
    };

    await offlineStorage.addFormula(newFormula);
    setFormulas(prev => [newFormula, ...prev]);

    await offlineStorage.addToSyncQueue({
      type: 'formulas',
      action: 'create',
      data: formulaData,
      localId,
    });

    if (isOnline) {
      try {
        const response = await api.post('/formulas', formulaData);
        await offlineStorage.updateLocalIdToServerId('formulas', localId, response.data.id);
        setFormulas(prev => prev.map(f => 
          f.localId === localId ? { ...response.data, _pendingSync: false } : f
        ));
      } catch (error) {
        console.error('Failed to sync formula to server:', error);
      }
    }

    return newFormula;
  }, [isOnline]);

  const updateFormula = useCallback(async (id: string, updates: Partial<LocalFormula>) => {
    const updated = await offlineStorage.updateFormula(id, updates);
    if (updated) {
      setFormulas(prev => prev.map(f => f.id === id || f.localId === id ? updated : f));
    }

    if (!id.startsWith('local_')) {
      await offlineStorage.addToSyncQueue({
        type: 'formulas',
        action: 'update',
        data: { id, ...updates },
      });

      if (isOnline) {
        try {
          const response = await api.put(`/formulas/${id}`, updates);
          setFormulas(prev => prev.map(f => 
            f.id === id ? { ...response.data, _pendingSync: false } : f
          ));
        } catch (error) {
          console.error('Failed to sync formula update:', error);
        }
      }
    }

    return updated;
  }, [isOnline]);

  const deleteFormula = useCallback(async (id: string) => {
    await offlineStorage.deleteFormula(id);
    setFormulas(prev => prev.filter(f => f.id !== id && f.localId !== id));

    if (!id.startsWith('local_')) {
      await offlineStorage.addToSyncQueue({
        type: 'formulas',
        action: 'delete',
        data: { id },
      });

      if (isOnline) {
        try {
          await api.delete(`/formulas/${id}`);
        } catch (error) {
          console.error('Failed to sync formula deletion:', error);
        }
      }
    }
  }, [isOnline]);

  return {
    formulas,
    loading,
    refreshing,
    onRefresh,
    addFormula,
    updateFormula,
    deleteFormula,
  };
}

// Hook for cached dashboard stats
export function useOfflineDashboardStats() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const { isOnline } = useNetwork();

  const loadStats = useCallback(async () => {
    try {
      // Load cached stats first
      const cached = await offlineStorage.getDashboardStats();
      if (cached) {
        setStats(cached);
      }

      // Fetch fresh if online
      if (isOnline) {
        try {
          const response = await api.get('/dashboard/stats');
          await offlineStorage.saveDashboardStats(response.data);
          setStats(response.data);
        } catch (error) {
          console.error('Failed to fetch dashboard stats:', error);
        }
      }
    } catch (error) {
      console.error('Failed to load dashboard stats:', error);
    } finally {
      setLoading(false);
    }
  }, [isOnline]);

  useFocusEffect(
    useCallback(() => {
      loadStats();
    }, [loadStats])
  );

  return { stats, loading, refresh: loadStats };
}
