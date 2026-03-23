import AsyncStorage from '@react-native-async-storage/async-storage';

// Keys for user-scoped data
const getKey = (userId: string, type: string) => `user_${userId}_${type}`;
const SYNC_QUEUE_KEY = 'sync_queue';

export interface SyncQueueItem {
  id: string;
  type: 'clients' | 'appointments' | 'formulas';
  action: 'create' | 'update' | 'delete';
  data: any;
  localId?: string; // For creates before server assigns ID
  timestamp: number;
  userId: string;
}

export interface LocalClient {
  id: string;
  localId?: string; // Temporary ID for offline creates
  name: string;
  email?: string;
  phone?: string;
  photo?: string;
  notes?: string;
  preferences?: string;
  hair_goals?: string;
  is_vip?: boolean;
  visit_count?: number;
  last_visit?: string;
  created_at?: string;
  _pendingSync?: boolean;
  _isDeleted?: boolean;
}

export interface LocalAppointment {
  id: string;
  localId?: string;
  client_id: string;
  client_name?: string;
  appointment_date: string;
  service: string;
  duration_minutes: number;
  notes?: string;
  status: string;
  _pendingSync?: boolean;
  _isDeleted?: boolean;
}

export interface LocalFormula {
  id: string;
  localId?: string;
  client_id: string;
  client_name?: string;
  formula_name: string;
  formula_details: string;
  date_created: string;
  _pendingSync?: boolean;
  _isDeleted?: boolean;
}

class OfflineStorage {
  private userId: string | null = null;

  setUserId(userId: string) {
    this.userId = userId;
  }

  clearUserId() {
    this.userId = null;
  }

  // Generate temporary local ID for offline creates
  generateLocalId(): string {
    return `local_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  // ==================== CLIENTS ====================
  async getClients(): Promise<LocalClient[]> {
    if (!this.userId) return [];
    try {
      const data = await AsyncStorage.getItem(getKey(this.userId, 'clients'));
      const clients = data ? JSON.parse(data) : [];
      // Filter out deleted items
      return clients.filter((c: LocalClient) => !c._isDeleted);
    } catch (error) {
      console.error('Error getting clients:', error);
      return [];
    }
  }

  async saveClients(clients: LocalClient[]): Promise<void> {
    if (!this.userId) return;
    try {
      await AsyncStorage.setItem(getKey(this.userId, 'clients'), JSON.stringify(clients));
    } catch (error) {
      console.error('Error saving clients:', error);
    }
  }

  async addClient(client: LocalClient): Promise<LocalClient> {
    const clients = await this.getClients();
    // Check if already exists (by id or localId)
    const existingIndex = clients.findIndex(c => 
      c.id === client.id || (client.localId && c.localId === client.localId)
    );
    if (existingIndex >= 0) {
      clients[existingIndex] = { ...clients[existingIndex], ...client };
    } else {
      clients.push(client);
    }
    await this.saveClients(clients);
    return client;
  }

  async updateClient(id: string, updates: Partial<LocalClient>): Promise<LocalClient | null> {
    const clients = await this.getClients();
    const index = clients.findIndex(c => c.id === id || c.localId === id);
    if (index >= 0) {
      clients[index] = { ...clients[index], ...updates, _pendingSync: true };
      await this.saveClients(clients);
      return clients[index];
    }
    return null;
  }

  async deleteClient(id: string): Promise<void> {
    const allClients = await AsyncStorage.getItem(getKey(this.userId!, 'clients'));
    const clients: LocalClient[] = allClients ? JSON.parse(allClients) : [];
    const index = clients.findIndex(c => c.id === id || c.localId === id);
    if (index >= 0) {
      // Mark as deleted instead of removing (for sync)
      clients[index]._isDeleted = true;
      clients[index]._pendingSync = true;
      await AsyncStorage.setItem(getKey(this.userId!, 'clients'), JSON.stringify(clients));
    }
  }

  // ==================== APPOINTMENTS ====================
  async getAppointments(): Promise<LocalAppointment[]> {
    if (!this.userId) return [];
    try {
      const data = await AsyncStorage.getItem(getKey(this.userId, 'appointments'));
      const appointments = data ? JSON.parse(data) : [];
      return appointments.filter((a: LocalAppointment) => !a._isDeleted);
    } catch (error) {
      console.error('Error getting appointments:', error);
      return [];
    }
  }

  async saveAppointments(appointments: LocalAppointment[]): Promise<void> {
    if (!this.userId) return;
    try {
      await AsyncStorage.setItem(getKey(this.userId, 'appointments'), JSON.stringify(appointments));
    } catch (error) {
      console.error('Error saving appointments:', error);
    }
  }

  async addAppointment(appointment: LocalAppointment): Promise<LocalAppointment> {
    const appointments = await this.getAppointments();
    const existingIndex = appointments.findIndex(a => 
      a.id === appointment.id || (appointment.localId && a.localId === appointment.localId)
    );
    if (existingIndex >= 0) {
      appointments[existingIndex] = { ...appointments[existingIndex], ...appointment };
    } else {
      appointments.push(appointment);
    }
    await this.saveAppointments(appointments);
    return appointment;
  }

  async updateAppointment(id: string, updates: Partial<LocalAppointment>): Promise<LocalAppointment | null> {
    const appointments = await this.getAppointments();
    const index = appointments.findIndex(a => a.id === id || a.localId === id);
    if (index >= 0) {
      appointments[index] = { ...appointments[index], ...updates, _pendingSync: true };
      await this.saveAppointments(appointments);
      return appointments[index];
    }
    return null;
  }

  async deleteAppointment(id: string): Promise<void> {
    const allAppointments = await AsyncStorage.getItem(getKey(this.userId!, 'appointments'));
    const appointments: LocalAppointment[] = allAppointments ? JSON.parse(allAppointments) : [];
    const index = appointments.findIndex(a => a.id === id || a.localId === id);
    if (index >= 0) {
      appointments[index]._isDeleted = true;
      appointments[index]._pendingSync = true;
      await AsyncStorage.setItem(getKey(this.userId!, 'appointments'), JSON.stringify(appointments));
    }
  }

  // ==================== FORMULAS ====================
  async getFormulas(): Promise<LocalFormula[]> {
    if (!this.userId) return [];
    try {
      const data = await AsyncStorage.getItem(getKey(this.userId, 'formulas'));
      const formulas = data ? JSON.parse(data) : [];
      return formulas.filter((f: LocalFormula) => !f._isDeleted);
    } catch (error) {
      console.error('Error getting formulas:', error);
      return [];
    }
  }

  async saveFormulas(formulas: LocalFormula[]): Promise<void> {
    if (!this.userId) return;
    try {
      await AsyncStorage.setItem(getKey(this.userId, 'formulas'), JSON.stringify(formulas));
    } catch (error) {
      console.error('Error saving formulas:', error);
    }
  }

  async addFormula(formula: LocalFormula): Promise<LocalFormula> {
    const formulas = await this.getFormulas();
    const existingIndex = formulas.findIndex(f => 
      f.id === formula.id || (formula.localId && f.localId === formula.localId)
    );
    if (existingIndex >= 0) {
      formulas[existingIndex] = { ...formulas[existingIndex], ...formula };
    } else {
      formulas.push(formula);
    }
    await this.saveFormulas(formulas);
    return formula;
  }

  async updateFormula(id: string, updates: Partial<LocalFormula>): Promise<LocalFormula | null> {
    const formulas = await this.getFormulas();
    const index = formulas.findIndex(f => f.id === id || f.localId === id);
    if (index >= 0) {
      formulas[index] = { ...formulas[index], ...updates, _pendingSync: true };
      await this.saveFormulas(formulas);
      return formulas[index];
    }
    return null;
  }

  async deleteFormula(id: string): Promise<void> {
    const allFormulas = await AsyncStorage.getItem(getKey(this.userId!, 'formulas'));
    const formulas: LocalFormula[] = allFormulas ? JSON.parse(allFormulas) : [];
    const index = formulas.findIndex(f => f.id === id || f.localId === id);
    if (index >= 0) {
      formulas[index]._isDeleted = true;
      formulas[index]._pendingSync = true;
      await AsyncStorage.setItem(getKey(this.userId!, 'formulas'), JSON.stringify(formulas));
    }
  }

  // ==================== DASHBOARD STATS ====================
  async getDashboardStats(): Promise<any | null> {
    if (!this.userId) return null;
    try {
      const data = await AsyncStorage.getItem(getKey(this.userId, 'dashboard_stats'));
      return data ? JSON.parse(data) : null;
    } catch (error) {
      console.error('Error getting dashboard stats:', error);
      return null;
    }
  }

  async saveDashboardStats(stats: any): Promise<void> {
    if (!this.userId) return;
    try {
      await AsyncStorage.setItem(getKey(this.userId, 'dashboard_stats'), JSON.stringify(stats));
    } catch (error) {
      console.error('Error saving dashboard stats:', error);
    }
  }

  // ==================== SYNC QUEUE ====================
  async getSyncQueue(): Promise<SyncQueueItem[]> {
    try {
      const data = await AsyncStorage.getItem(SYNC_QUEUE_KEY);
      const queue = data ? JSON.parse(data) : [];
      // Filter by current user
      return this.userId ? queue.filter((item: SyncQueueItem) => item.userId === this.userId) : [];
    } catch (error) {
      console.error('Error getting sync queue:', error);
      return [];
    }
  }

  async addToSyncQueue(item: Omit<SyncQueueItem, 'id' | 'timestamp' | 'userId'>): Promise<void> {
    if (!this.userId) return;
    try {
      const data = await AsyncStorage.getItem(SYNC_QUEUE_KEY);
      const queue: SyncQueueItem[] = data ? JSON.parse(data) : [];
      
      const newItem: SyncQueueItem = {
        ...item,
        id: this.generateLocalId(),
        timestamp: Date.now(),
        userId: this.userId,
      };
      
      queue.push(newItem);
      await AsyncStorage.setItem(SYNC_QUEUE_KEY, JSON.stringify(queue));
    } catch (error) {
      console.error('Error adding to sync queue:', error);
    }
  }

  async removeFromSyncQueue(id: string): Promise<void> {
    try {
      const data = await AsyncStorage.getItem(SYNC_QUEUE_KEY);
      const queue: SyncQueueItem[] = data ? JSON.parse(data) : [];
      const filtered = queue.filter(item => item.id !== id);
      await AsyncStorage.setItem(SYNC_QUEUE_KEY, JSON.stringify(filtered));
    } catch (error) {
      console.error('Error removing from sync queue:', error);
    }
  }

  async clearSyncQueue(): Promise<void> {
    if (!this.userId) return;
    try {
      const data = await AsyncStorage.getItem(SYNC_QUEUE_KEY);
      const queue: SyncQueueItem[] = data ? JSON.parse(data) : [];
      const filtered = queue.filter(item => item.userId !== this.userId);
      await AsyncStorage.setItem(SYNC_QUEUE_KEY, JSON.stringify(filtered));
    } catch (error) {
      console.error('Error clearing sync queue:', error);
    }
  }

  // ==================== CLEAR USER DATA ====================
  async clearUserData(): Promise<void> {
    if (!this.userId) return;
    try {
      await AsyncStorage.multiRemove([
        getKey(this.userId, 'clients'),
        getKey(this.userId, 'appointments'),
        getKey(this.userId, 'formulas'),
        getKey(this.userId, 'dashboard_stats'),
      ]);
      await this.clearSyncQueue();
    } catch (error) {
      console.error('Error clearing user data:', error);
    }
  }

  // ==================== MERGE SERVER DATA ====================
  // Server wins strategy - replace local with server data, keeping unsynced local changes
  async mergeClientsFromServer(serverClients: any[]): Promise<void> {
    if (!this.userId) return;
    const allClientsData = await AsyncStorage.getItem(getKey(this.userId, 'clients'));
    const localClients: LocalClient[] = allClientsData ? JSON.parse(allClientsData) : [];
    
    // Find local-only items (not yet synced to server)
    const localOnlyClients = localClients.filter(c => c.localId && !c.id.startsWith('local_') === false);
    
    // Map server clients
    const mergedClients: LocalClient[] = serverClients.map(sc => ({
      ...sc,
      _pendingSync: false,
      _isDeleted: false,
    }));
    
    // Add local-only items back
    localOnlyClients.forEach(lc => {
      if (!mergedClients.find(mc => mc.localId === lc.localId)) {
        mergedClients.push(lc);
      }
    });
    
    await this.saveClients(mergedClients);
  }

  async mergeAppointmentsFromServer(serverAppointments: any[]): Promise<void> {
    if (!this.userId) return;
    const allData = await AsyncStorage.getItem(getKey(this.userId, 'appointments'));
    const localAppointments: LocalAppointment[] = allData ? JSON.parse(allData) : [];
    
    const localOnlyAppointments = localAppointments.filter(a => a.localId && a.id.startsWith('local_'));
    
    const mergedAppointments: LocalAppointment[] = serverAppointments.map(sa => ({
      ...sa,
      _pendingSync: false,
      _isDeleted: false,
    }));
    
    localOnlyAppointments.forEach(la => {
      if (!mergedAppointments.find(ma => ma.localId === la.localId)) {
        mergedAppointments.push(la);
      }
    });
    
    await this.saveAppointments(mergedAppointments);
  }

  async mergeFormulasFromServer(serverFormulas: any[]): Promise<void> {
    if (!this.userId) return;
    const allData = await AsyncStorage.getItem(getKey(this.userId, 'formulas'));
    const localFormulas: LocalFormula[] = allData ? JSON.parse(allData) : [];
    
    const localOnlyFormulas = localFormulas.filter(f => f.localId && f.id.startsWith('local_'));
    
    const mergedFormulas: LocalFormula[] = serverFormulas.map(sf => ({
      ...sf,
      _pendingSync: false,
      _isDeleted: false,
    }));
    
    localOnlyFormulas.forEach(lf => {
      if (!mergedFormulas.find(mf => mf.localId === lf.localId)) {
        mergedFormulas.push(lf);
      }
    });
    
    await this.saveFormulas(mergedFormulas);
  }

  // Update local ID to server ID after successful sync
  async updateLocalIdToServerId(type: 'clients' | 'appointments' | 'formulas', localId: string, serverId: string): Promise<void> {
    if (!this.userId) return;
    const key = getKey(this.userId, type);
    const data = await AsyncStorage.getItem(key);
    const items = data ? JSON.parse(data) : [];
    
    const index = items.findIndex((item: any) => item.localId === localId || item.id === localId);
    if (index >= 0) {
      items[index].id = serverId;
      items[index].localId = undefined;
      items[index]._pendingSync = false;
      await AsyncStorage.setItem(key, JSON.stringify(items));
    }
  }
}

export const offlineStorage = new OfflineStorage();
