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
import { useRouter, useLocalSearchParams } from 'expo-router';
import { useFocusEffect } from '@react-navigation/native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { Card } from '../../../components/Card';
import Colors from '../../../constants/Colors';
import Spacing from '../../../constants/Spacing';
import Typography from '../../../constants/Typography';
import api from '../../../utils/api';

interface Formula {
  id: string;
  formula_name: string;
  formula_details: string;
  date_created: string;
}

export default function ClientFormulaScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id: string }>();
  
  const [client, setClient] = useState<any>(null);
  const [formulas, setFormulas] = useState<Formula[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [editingFormula, setEditingFormula] = useState<Formula | null>(null);
  const [formulaName, setFormulaName] = useState('');
  const [formulaDetails, setFormulaDetails] = useState('');
  const [saving, setSaving] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [clientRes, formulasRes] = await Promise.all([
        api.get(`/clients/${id}`),
        api.get(`/formulas?client_id=${id}`),
      ]);
      setClient(clientRes.data);
      setFormulas(formulasRes.data);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [id]);

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
    setFormulaName('');
    setFormulaDetails('');
    setShowModal(true);
  };

  const openEditModal = (formula: Formula) => {
    setEditingFormula(formula);
    setFormulaName(formula.formula_name);
    setFormulaDetails(formula.formula_details);
    setShowModal(true);
  };

  const handleSave = async () => {
    if (!formulaName.trim() || !formulaDetails.trim()) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }

    setSaving(true);
    try {
      if (editingFormula) {
        // Update existing formula - use returned data for instant UI sync
        const response = await api.put(`/formulas/${editingFormula.id}`, {
          formula_name: formulaName.trim(),
          formula_details: formulaDetails.trim(),
        });
        
        // Immediately update local state with returned data
        setFormulas(prev => prev.map(f => 
          f.id === editingFormula.id ? response.data : f
        ));
      } else {
        // Create new formula - use returned data for instant UI sync
        const response = await api.post('/formulas', {
          client_id: id,
          formula_name: formulaName.trim(),
          formula_details: formulaDetails.trim(),
        });
        
        // Immediately add to local state with returned data
        setFormulas(prev => [response.data, ...prev]);
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
      `Delete "${formula.formula_name}"?`,
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

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const renderFormula = ({ item }: { item: Formula }) => (
    <Card style={styles.formulaCard}>
      <TouchableOpacity onPress={() => openEditModal(item)}>
        <View style={styles.formulaHeader}>
          <View style={styles.formulaIcon}>
            <Ionicons name="flask" size={20} color={Colors.accent} />
          </View>
          <View style={styles.formulaInfo}>
            <Text style={styles.formulaName}>{item.formula_name}</Text>
            <Text style={styles.formulaDate}>{formatDate(item.date_created)}</Text>
          </View>
          <TouchableOpacity onPress={() => handleDelete(item)}>
            <Ionicons name="trash-outline" size={18} color={Colors.error} />
          </TouchableOpacity>
        </View>
        <Text style={styles.formulaDetails}>{item.formula_details}</Text>
      </TouchableOpacity>
    </Card>
  );

  if (loading) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={Colors.accent} />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color={Colors.text} />
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <Text style={styles.title}>Formulas</Text>
          {client && <Text style={styles.subtitle}>{client.name}</Text>}
        </View>
        <TouchableOpacity onPress={openCreateModal}>
          <Ionicons name="add-circle" size={28} color={Colors.accent} />
        </TouchableOpacity>
      </View>

      <FlatList
        data={formulas}
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
            <Text style={styles.emptyTitle}>No Formulas</Text>
            <Text style={styles.emptyText}>Save color formulas and treatment mixes for {client?.name}</Text>
            <TouchableOpacity style={styles.createButton} onPress={openCreateModal}>
              <Ionicons name="add" size={20} color={Colors.buttonText} />
              <Text style={styles.createButtonText}>Add Formula</Text>
            </TouchableOpacity>
          </View>
        }
      />

      <Modal visible={showModal} animationType="slide" transparent>
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
              <Text style={styles.inputLabel}>Formula Name *</Text>
              <TextInput
                style={styles.input}
                placeholder="e.g., Balayage Formula"
                placeholderTextColor={Colors.textLight}
                value={formulaName}
                onChangeText={setFormulaName}
              />

              <Text style={styles.inputLabel}>Details *</Text>
              <TextInput
                style={[styles.input, styles.textArea]}
                placeholder="Enter color codes, ratios, processing times..."
                placeholderTextColor={Colors.textLight}
                value={formulaDetails}
                onChangeText={setFormulaDetails}
                multiline
                numberOfLines={6}
                textAlignVertical="top"
              />
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
                  <Text style={styles.saveButtonText}>Save</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: Spacing.screenPadding,
    paddingVertical: Spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  headerCenter: { alignItems: 'center' },
  title: { fontSize: Typography.h3, fontWeight: Typography.semibold, color: Colors.text },
  subtitle: { fontSize: Typography.caption, color: Colors.textSecondary },
  listContent: { padding: Spacing.screenPadding },
  formulaCard: { marginBottom: Spacing.md },
  formulaHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: Spacing.sm },
  formulaIcon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: Colors.accent + '20',
    alignItems: 'center',
    justifyContent: 'center',
  },
  formulaInfo: { flex: 1, marginLeft: Spacing.sm },
  formulaName: { fontSize: Typography.body, fontWeight: Typography.semibold, color: Colors.text },
  formulaDate: { fontSize: Typography.caption, color: Colors.textSecondary },
  formulaDetails: { fontSize: Typography.bodySmall, color: Colors.textSecondary, lineHeight: 20 },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: Spacing.xxl * 2,
    gap: Spacing.md,
  },
  emptyTitle: { fontSize: Typography.h3, fontWeight: Typography.semibold, color: Colors.text },
  emptyText: { fontSize: Typography.body, color: Colors.textSecondary, textAlign: 'center' },
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
  createButtonText: { fontSize: Typography.body, fontWeight: Typography.semibold, color: Colors.buttonText },
  modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'flex-end' },
  modalContent: { backgroundColor: Colors.background, borderTopLeftRadius: 20, borderTopRightRadius: 20, maxHeight: '80%' },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: Spacing.screenPadding,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  modalTitle: { fontSize: Typography.h3, fontWeight: Typography.semibold, color: Colors.text },
  modalBody: { padding: Spacing.screenPadding },
  inputLabel: { fontSize: Typography.bodySmall, fontWeight: Typography.semibold, color: Colors.textSecondary, marginBottom: Spacing.xs, marginTop: Spacing.md },
  input: { backgroundColor: Colors.backgroundSecondary, borderRadius: 12, padding: Spacing.md, fontSize: Typography.body, color: Colors.text, borderWidth: 1, borderColor: Colors.border },
  textArea: { minHeight: 120, textAlignVertical: 'top' },
  modalFooter: { flexDirection: 'row', padding: Spacing.screenPadding, gap: Spacing.md, borderTopWidth: 1, borderTopColor: Colors.border },
  cancelButton: { flex: 1, paddingVertical: Spacing.md, borderRadius: 12, backgroundColor: Colors.backgroundSecondary, alignItems: 'center' },
  cancelButtonText: { fontSize: Typography.body, fontWeight: Typography.semibold, color: Colors.textSecondary },
  saveButton: { flex: 1, paddingVertical: Spacing.md, borderRadius: 12, backgroundColor: Colors.accent, alignItems: 'center' },
  saveButtonDisabled: { opacity: 0.6 },
  saveButtonText: { fontSize: Typography.body, fontWeight: Typography.semibold, color: Colors.buttonText },
});
