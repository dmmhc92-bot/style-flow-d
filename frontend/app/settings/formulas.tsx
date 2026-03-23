import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  TextInput,
  Alert,
  ActivityIndicator,
  Modal,
  ScrollView,
  RefreshControl,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useFocusEffect } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { Card } from '../../components/Card';
import Colors from '../../constants/Colors';
import Spacing from '../../constants/Spacing';
import Typography from '../../constants/Typography';
import api from '../../utils/api';

interface Formula {
  id: string;
  client_id: string;
  formula_name: string;
  formula_details: string;
  date_created: string;
  client_name?: string;
}

interface Client {
  id: string;
  name: string;
}

export default function FormulaVaultScreen() {
  const router = useRouter();
  const [formulas, setFormulas] = useState<Formula[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedClientFilter, setSelectedClientFilter] = useState<string | null>(null);
  
  // Modal states
  const [showModal, setShowModal] = useState(false);
  const [editingFormula, setEditingFormula] = useState<Formula | null>(null);
  const [showClientPicker, setShowClientPicker] = useState(false);
  
  // Form states
  const [selectedClient, setSelectedClient] = useState<Client | null>(null);
  const [formulaName, setFormulaName] = useState('');
  const [formulaDetails, setFormulaDetails] = useState('');
  const [saving, setSaving] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [formulasRes, clientsRes] = await Promise.all([
        api.get('/formulas'),
        api.get('/clients'),
      ]);
      
      // Map client names to formulas
      const clientMap: { [key: string]: string } = {};
      clientsRes.data.forEach((c: any) => {
        clientMap[c.id] = c.name;
      });
      
      const enrichedFormulas = formulasRes.data.map((f: Formula) => ({
        ...f,
        client_name: clientMap[f.client_id] || 'Unknown Client',
      }));
      
      setFormulas(enrichedFormulas);
      setClients(clientsRes.data);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  // Refresh data when screen comes into focus
  useFocusEffect(
    useCallback(() => {
      loadData();
    }, [loadData])
  );

  const handleRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const openCreateModal = () => {
    setEditingFormula(null);
    setSelectedClient(null);
    setFormulaName('');
    setFormulaDetails('');
    setShowModal(true);
  };

  const openEditModal = (formula: Formula) => {
    setEditingFormula(formula);
    const client = clients.find(c => c.id === formula.client_id);
    setSelectedClient(client || null);
    setFormulaName(formula.formula_name);
    setFormulaDetails(formula.formula_details);
    setShowModal(true);
  };

  const handleSave = async () => {
    if (!selectedClient) {
      Alert.alert('Error', 'Please select a client');
      return;
    }
    if (!formulaName.trim()) {
      Alert.alert('Error', 'Please enter a formula name');
      return;
    }
    if (!formulaDetails.trim()) {
      Alert.alert('Error', 'Please enter formula details');
      return;
    }

    setSaving(true);
    try {
      if (editingFormula) {
        // Update existing formula - use returned data for instant UI sync
        const response = await api.put(`/formulas/${editingFormula.id}`, {
          client_id: selectedClient.id,
          formula_name: formulaName.trim(),
          formula_details: formulaDetails.trim(),
        });
        
        // Immediately update local state with returned data
        const updatedFormula = {
          ...response.data,
          client_name: selectedClient.name,
        };
        setFormulas(prev => prev.map(f => 
          f.id === editingFormula.id ? updatedFormula : f
        ));
        
        Alert.alert('Success', 'Formula updated!');
      } else {
        // Create new formula - use returned data for instant UI sync
        const response = await api.post('/formulas', {
          client_id: selectedClient.id,
          formula_name: formulaName.trim(),
          formula_details: formulaDetails.trim(),
        });
        
        // Immediately add to local state with returned data
        const newFormula = {
          ...response.data,
          client_name: selectedClient.name,
        };
        setFormulas(prev => [newFormula, ...prev]);
        
        Alert.alert('Success', 'Formula saved!');
      }
      setShowModal(false);
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.detail || 'Failed to save formula');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = (formula: Formula) => {
    Alert.alert(
      'Delete Formula',
      `Are you sure you want to delete "${formula.formula_name}"?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await api.delete(`/formulas/${formula.id}`);
              loadData();
            } catch (error) {
              Alert.alert('Error', 'Failed to delete formula');
            }
          },
        },
      ]
    );
  };

  const filteredFormulas = formulas.filter(f => {
    const matchesSearch = searchQuery
      ? f.formula_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        f.formula_details.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (f.client_name && f.client_name.toLowerCase().includes(searchQuery.toLowerCase()))
      : true;
    
    const matchesClient = selectedClientFilter
      ? f.client_id === selectedClientFilter
      : true;
    
    return matchesSearch && matchesClient;
  });

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const renderFormula = ({ item }: { item: Formula }) => (
    <Card style={styles.formulaCard}>
      <TouchableOpacity
        style={styles.formulaContent}
        onPress={() => openEditModal(item)}
      >
        <View style={styles.formulaHeader}>
          <View style={styles.formulaIcon}>
            <Ionicons name="flask" size={20} color={Colors.accent} />
          </View>
          <View style={styles.formulaInfo}>
            <Text style={styles.formulaName}>{item.formula_name}</Text>
            <TouchableOpacity
              onPress={() => router.push(`/clients/${item.client_id}`)}
            >
              <Text style={styles.clientName}>{item.client_name}</Text>
            </TouchableOpacity>
          </View>
          <TouchableOpacity
            style={styles.deleteButton}
            onPress={() => handleDelete(item)}
          >
            <Ionicons name="trash-outline" size={18} color={Colors.error} />
          </TouchableOpacity>
        </View>
        
        <Text style={styles.formulaDetails} numberOfLines={3}>
          {item.formula_details}
        </Text>
        
        <Text style={styles.formulaDate}>
          Created: {formatDate(item.date_created)}
        </Text>
      </TouchableOpacity>
    </Card>
  );

  const renderClientPicker = () => (
    <Modal
      visible={showClientPicker}
      animationType="slide"
      transparent
      onRequestClose={() => setShowClientPicker(false)}
    >
      <View style={styles.pickerOverlay}>
        <View style={styles.pickerModal}>
          <View style={styles.pickerHeader}>
            <Text style={styles.pickerTitle}>Select Client</Text>
            <TouchableOpacity onPress={() => setShowClientPicker(false)}>
              <Ionicons name="close" size={24} color={Colors.text} />
            </TouchableOpacity>
          </View>
          <FlatList
            data={clients}
            keyExtractor={item => item.id}
            renderItem={({ item }) => (
              <TouchableOpacity
                style={styles.pickerItem}
                onPress={() => {
                  setSelectedClient(item);
                  setShowClientPicker(false);
                }}
              >
                <View style={styles.pickerItemIcon}>
                  <Ionicons name="person" size={20} color={Colors.accent} />
                </View>
                <Text style={styles.pickerItemText}>{item.name}</Text>
                {selectedClient?.id === item.id && (
                  <Ionicons name="checkmark" size={20} color={Colors.accent} />
                )}
              </TouchableOpacity>
            )}
            ListEmptyComponent={
              <View style={styles.emptyPicker}>
                <Text style={styles.emptyPickerText}>No clients found</Text>
                <TouchableOpacity
                  style={styles.addClientButton}
                  onPress={() => {
                    setShowClientPicker(false);
                    setShowModal(false);
                    router.push('/clients/add');
                  }}
                >
                  <Text style={styles.addClientButtonText}>Add Client</Text>
                </TouchableOpacity>
              </View>
            }
          />
        </View>
      </View>
    </Modal>
  );

  if (loading && formulas.length === 0) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => router.back()}>
            <Ionicons name="arrow-back" size={24} color={Colors.text} />
          </TouchableOpacity>
          <Text style={styles.title}>Formula Vault</Text>
          <View style={{ width: 40 }} />
        </View>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={Colors.accent} />
          <Text style={styles.loadingText}>Loading formulas...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color={Colors.text} />
        </TouchableOpacity>
        <Text style={styles.title}>Formula Vault</Text>
        <TouchableOpacity onPress={openCreateModal}>
          <Ionicons name="add-circle" size={28} color={Colors.accent} />
        </TouchableOpacity>
      </View>

      {/* Search */}
      <View style={styles.searchContainer}>
        <Ionicons name="search" size={20} color={Colors.textSecondary} />
        <TextInput
          style={styles.searchInput}
          placeholder="Search formulas..."
          placeholderTextColor={Colors.textLight}
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
        {searchQuery.length > 0 && (
          <TouchableOpacity onPress={() => setSearchQuery('')}>
            <Ionicons name="close-circle" size={20} color={Colors.textSecondary} />
          </TouchableOpacity>
        )}
      </View>

      {/* Client Filter */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.filterContainer}
        contentContainerStyle={styles.filterContent}
      >
        <TouchableOpacity
          style={[styles.filterChip, !selectedClientFilter && styles.filterChipActive]}
          onPress={() => setSelectedClientFilter(null)}
        >
          <Text style={[styles.filterChipText, !selectedClientFilter && styles.filterChipTextActive]}>
            All Clients
          </Text>
        </TouchableOpacity>
        {clients.slice(0, 10).map(client => (
          <TouchableOpacity
            key={client.id}
            style={[styles.filterChip, selectedClientFilter === client.id && styles.filterChipActive]}
            onPress={() => setSelectedClientFilter(selectedClientFilter === client.id ? null : client.id)}
          >
            <Text style={[styles.filterChipText, selectedClientFilter === client.id && styles.filterChipTextActive]}>
              {client.name}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Stats */}
      <View style={styles.statsRow}>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>{formulas.length}</Text>
          <Text style={styles.statLabel}>Total Formulas</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>{new Set(formulas.map(f => f.client_id)).size}</Text>
          <Text style={styles.statLabel}>Clients with Formulas</Text>
        </View>
      </View>

      {/* Formulas List */}
      <FlatList
        data={filteredFormulas}
        renderItem={renderFormula}
        keyExtractor={item => item.id}
        contentContainerStyle={styles.listContent}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
            tintColor={Colors.accent}
          />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Ionicons name="flask-outline" size={64} color={Colors.textSecondary} />
            <Text style={styles.emptyTitle}>
              {searchQuery || selectedClientFilter ? 'No Formulas Found' : 'No Formulas Yet'}
            </Text>
            <Text style={styles.emptyText}>
              {searchQuery || selectedClientFilter
                ? 'Try adjusting your search or filter'
                : 'Save your color formulas, treatments, and recipes here for quick access during appointments.'}
            </Text>
            {!searchQuery && !selectedClientFilter && (
              <TouchableOpacity style={styles.createButton} onPress={openCreateModal}>
                <Ionicons name="add" size={20} color={Colors.buttonText} />
                <Text style={styles.createButtonText}>Create Formula</Text>
              </TouchableOpacity>
            )}
          </View>
        }
      />

      {/* Create/Edit Modal */}
      <Modal
        visible={showModal}
        animationType="slide"
        transparent
        onRequestClose={() => setShowModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>
                {editingFormula ? 'Edit Formula' : 'New Formula'}
              </Text>
              <TouchableOpacity onPress={() => setShowModal(false)}>
                <Ionicons name="close" size={24} color={Colors.text} />
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.modalBody}>
              {/* Client Selector */}
              <Text style={styles.inputLabel}>Client *</Text>
              <TouchableOpacity
                style={styles.clientSelector}
                onPress={() => setShowClientPicker(true)}
              >
                {selectedClient ? (
                  <View style={styles.selectedClient}>
                    <Ionicons name="person" size={18} color={Colors.accent} />
                    <Text style={styles.selectedClientText}>{selectedClient.name}</Text>
                  </View>
                ) : (
                  <Text style={styles.placeholderText}>Select a client...</Text>
                )}
                <Ionicons name="chevron-down" size={20} color={Colors.textSecondary} />
              </TouchableOpacity>

              {/* Formula Name */}
              <Text style={styles.inputLabel}>Formula Name *</Text>
              <TextInput
                style={styles.input}
                placeholder="e.g., Balayage Formula, Treatment Mix"
                placeholderTextColor={Colors.textLight}
                value={formulaName}
                onChangeText={setFormulaName}
                maxLength={100}
              />

              {/* Formula Details */}
              <Text style={styles.inputLabel}>Formula Details *</Text>
              <TextInput
                style={[styles.input, styles.textArea]}
                placeholder="Enter color codes, mixing ratios, processing times, developer volumes, etc."
                placeholderTextColor={Colors.textLight}
                value={formulaDetails}
                onChangeText={setFormulaDetails}
                multiline
                numberOfLines={6}
                textAlignVertical="top"
                maxLength={1000}
              />
              <Text style={styles.charCount}>{formulaDetails.length}/1000</Text>

              {/* Tips */}
              <View style={styles.tipBox}>
                <Ionicons name="bulb-outline" size={18} color={Colors.accent} />
                <Text style={styles.tipText}>
                  Include brand names, shade numbers, developer strength, and any special notes for consistent results.
                </Text>
              </View>
            </ScrollView>

            <View style={styles.modalFooter}>
              <TouchableOpacity
                style={styles.cancelButton}
                onPress={() => setShowModal(false)}
              >
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.saveButton, saving && styles.saveButtonDisabled]}
                onPress={handleSave}
                disabled={saving}
              >
                {saving ? (
                  <ActivityIndicator size="small" color={Colors.buttonText} />
                ) : (
                  <Text style={styles.saveButtonText}>
                    {editingFormula ? 'Update' : 'Save'}
                  </Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {renderClientPicker()}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: Spacing.screenPadding,
    paddingVertical: Spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  title: {
    fontSize: Typography.h3,
    fontWeight: Typography.semibold,
    color: Colors.text,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.backgroundSecondary,
    borderRadius: Spacing.radiusMedium,
    marginHorizontal: Spacing.screenPadding,
    marginTop: Spacing.md,
    paddingHorizontal: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  searchInput: {
    flex: 1,
    paddingVertical: Spacing.md,
    paddingHorizontal: Spacing.sm,
    fontSize: Typography.body,
    color: Colors.text,
  },
  filterContainer: {
    maxHeight: 50,
    marginTop: Spacing.sm,
  },
  filterContent: {
    paddingHorizontal: Spacing.screenPadding,
    paddingVertical: Spacing.xs,
    gap: Spacing.sm,
  },
  filterChip: {
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.xs,
    borderRadius: 16,
    backgroundColor: Colors.backgroundSecondary,
    marginRight: Spacing.sm,
  },
  filterChipActive: {
    backgroundColor: Colors.accent,
  },
  filterChipText: {
    fontSize: Typography.caption,
    color: Colors.textSecondary,
  },
  filterChipTextActive: {
    color: Colors.buttonText,
    fontWeight: Typography.semibold,
  },
  statsRow: {
    flexDirection: 'row',
    paddingHorizontal: Spacing.screenPadding,
    paddingVertical: Spacing.md,
    gap: Spacing.md,
  },
  statItem: {
    flex: 1,
    backgroundColor: Colors.backgroundSecondary,
    padding: Spacing.md,
    borderRadius: 12,
    alignItems: 'center',
  },
  statValue: {
    fontSize: Typography.h2,
    fontWeight: Typography.bold,
    color: Colors.accent,
  },
  statLabel: {
    fontSize: Typography.caption,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  listContent: {
    padding: Spacing.screenPadding,
    paddingTop: 0,
  },
  formulaCard: {
    marginBottom: Spacing.md,
  },
  formulaContent: {
    padding: 0,
  },
  formulaHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  formulaIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: Colors.accent + '20',
    alignItems: 'center',
    justifyContent: 'center',
  },
  formulaInfo: {
    flex: 1,
    marginLeft: Spacing.sm,
  },
  formulaName: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold,
    color: Colors.text,
  },
  clientName: {
    fontSize: Typography.caption,
    color: Colors.accent,
    marginTop: 2,
  },
  deleteButton: {
    padding: Spacing.sm,
  },
  formulaDetails: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    marginTop: Spacing.sm,
    lineHeight: 20,
  },
  formulaDate: {
    fontSize: Typography.caption,
    color: Colors.textLight,
    marginTop: Spacing.sm,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: Spacing.md,
  },
  loadingText: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: Spacing.xxl * 2,
    paddingHorizontal: Spacing.screenPadding,
    gap: Spacing.md,
  },
  emptyTitle: {
    fontSize: Typography.h3,
    fontWeight: Typography.semibold,
    color: Colors.text,
  },
  emptyText: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 22,
  },
  createButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.accent,
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.md,
    borderRadius: 24,
    gap: Spacing.xs,
    marginTop: Spacing.md,
  },
  createButtonText: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold,
    color: Colors.buttonText,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: Colors.background,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '90%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: Spacing.screenPadding,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  modalTitle: {
    fontSize: Typography.h3,
    fontWeight: Typography.semibold,
    color: Colors.text,
  },
  modalBody: {
    padding: Spacing.screenPadding,
  },
  inputLabel: {
    fontSize: Typography.bodySmall,
    fontWeight: Typography.semibold,
    color: Colors.textSecondary,
    marginBottom: Spacing.xs,
    marginTop: Spacing.md,
  },
  input: {
    backgroundColor: Colors.backgroundSecondary,
    borderRadius: 12,
    padding: Spacing.md,
    fontSize: Typography.body,
    color: Colors.text,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  textArea: {
    minHeight: 120,
    textAlignVertical: 'top',
  },
  charCount: {
    fontSize: Typography.caption,
    color: Colors.textLight,
    textAlign: 'right',
    marginTop: Spacing.xs,
  },
  clientSelector: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: Colors.backgroundSecondary,
    borderRadius: 12,
    padding: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  selectedClient: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
  },
  selectedClientText: {
    fontSize: Typography.body,
    color: Colors.text,
  },
  placeholderText: {
    fontSize: Typography.body,
    color: Colors.textLight,
  },
  tipBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: Colors.accent + '10',
    padding: Spacing.md,
    borderRadius: 12,
    marginTop: Spacing.lg,
    gap: Spacing.sm,
  },
  tipText: {
    flex: 1,
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    lineHeight: 18,
  },
  modalFooter: {
    flexDirection: 'row',
    padding: Spacing.screenPadding,
    gap: Spacing.md,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  cancelButton: {
    flex: 1,
    paddingVertical: Spacing.md,
    borderRadius: 12,
    backgroundColor: Colors.backgroundSecondary,
    alignItems: 'center',
  },
  cancelButtonText: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold,
    color: Colors.textSecondary,
  },
  saveButton: {
    flex: 1,
    paddingVertical: Spacing.md,
    borderRadius: 12,
    backgroundColor: Colors.accent,
    alignItems: 'center',
  },
  saveButtonDisabled: {
    opacity: 0.6,
  },
  saveButtonText: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold,
    color: Colors.buttonText,
  },
  pickerOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  pickerModal: {
    backgroundColor: Colors.background,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '70%',
  },
  pickerHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: Spacing.screenPadding,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  pickerTitle: {
    fontSize: Typography.h3,
    fontWeight: Typography.semibold,
    color: Colors.text,
  },
  pickerItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: Spacing.md,
    paddingHorizontal: Spacing.screenPadding,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  pickerItemIcon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: Colors.accent + '20',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: Spacing.md,
  },
  pickerItemText: {
    flex: 1,
    fontSize: Typography.body,
    color: Colors.text,
  },
  emptyPicker: {
    padding: Spacing.xl,
    alignItems: 'center',
    gap: Spacing.md,
  },
  emptyPickerText: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
  },
  addClientButton: {
    backgroundColor: Colors.accent,
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.sm,
    borderRadius: 20,
  },
  addClientButtonText: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold,
    color: Colors.buttonText,
  },
});
