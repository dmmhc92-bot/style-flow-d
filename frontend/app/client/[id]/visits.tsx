import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { Card } from '../../../components/Card';
import Colors from '../../../constants/Colors';
import Spacing from '../../../constants/Spacing';
import Typography from '../../../constants/Typography';
import api from '../../../utils/api';

interface Appointment {
  id: string;
  service: string;
  date: string;
  time: string;
  status: string;
  notes?: string;
  price?: number;
}

export default function ClientVisitsScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id: string }>();
  
  const [client, setClient] = useState<any>(null);
  const [visits, setVisits] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [clientRes, appointmentsRes] = await Promise.all([
        api.get(`/clients/${id}`),
        api.get(`/appointments?client_id=${id}`),
      ]);
      setClient(clientRes.data);
      // Filter to past appointments (visits)
      const now = new Date();
      const pastVisits = appointmentsRes.data.filter((a: Appointment) => {
        const appointmentDate = new Date(a.date);
        return appointmentDate < now || a.status === 'completed';
      }).sort((a: Appointment, b: Appointment) => 
        new Date(b.date).getTime() - new Date(a.date).getTime()
      );
      setVisits(pastVisits);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return Colors.success;
      case 'cancelled': return Colors.error;
      case 'no_show': return Colors.warning;
      default: return Colors.textSecondary;
    }
  };

  const renderVisit = ({ item }: { item: Appointment }) => (
    <Card style={styles.visitCard}>
      <View style={styles.visitHeader}>
        <View style={styles.visitIcon}>
          <Ionicons name="cut" size={20} color={Colors.accent} />
        </View>
        <View style={styles.visitInfo}>
          <Text style={styles.visitService}>{item.service}</Text>
          <Text style={styles.visitDate}>{formatDate(item.date)} at {item.time}</Text>
        </View>
        <View style={[styles.statusBadge, { backgroundColor: getStatusColor(item.status) + '20' }]}>
          <Text style={[styles.statusText, { color: getStatusColor(item.status) }]}>
            {item.status.replace('_', ' ')}
          </Text>
        </View>
      </View>
      {item.notes && (
        <Text style={styles.visitNotes}>{item.notes}</Text>
      )}
      {item.price && (
        <Text style={styles.visitPrice}>${item.price}</Text>
      )}
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
          <Text style={styles.title}>Visit History</Text>
          {client && <Text style={styles.subtitle}>{client.name}</Text>}
        </View>
        <TouchableOpacity onPress={() => router.push(`/appointment/add?clientId=${id}`)}>
          <Ionicons name="add-circle" size={28} color={Colors.accent} />
        </TouchableOpacity>
      </View>

      {/* Stats */}
      <View style={styles.statsRow}>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>{visits.length}</Text>
          <Text style={styles.statLabel}>Total Visits</Text>
        </View>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>
            ${visits.reduce((sum, v) => sum + (v.price || 0), 0).toFixed(0)}
          </Text>
          <Text style={styles.statLabel}>Total Spent</Text>
        </View>
      </View>

      <FlatList
        data={visits}
        renderItem={renderVisit}
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
            <Ionicons name="time-outline" size={64} color={Colors.textSecondary} />
            <Text style={styles.emptyTitle}>No Visits Yet</Text>
            <Text style={styles.emptyText}>{client?.name}'s appointment history will appear here</Text>
            <TouchableOpacity 
              style={styles.bookButton} 
              onPress={() => router.push(`/appointment/add?clientId=${id}`)}
            >
              <Ionicons name="calendar" size={20} color={Colors.buttonText} />
              <Text style={styles.bookButtonText}>Book Appointment</Text>
            </TouchableOpacity>
          </View>
        }
      />
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
  statsRow: {
    flexDirection: 'row',
    padding: Spacing.screenPadding,
    gap: Spacing.md,
  },
  statItem: {
    flex: 1,
    backgroundColor: Colors.backgroundSecondary,
    padding: Spacing.md,
    borderRadius: 12,
    alignItems: 'center',
  },
  statValue: { fontSize: Typography.h2, fontWeight: Typography.bold, color: Colors.accent },
  statLabel: { fontSize: Typography.caption, color: Colors.textSecondary, marginTop: 2 },
  listContent: { padding: Spacing.screenPadding, paddingTop: 0 },
  visitCard: { marginBottom: Spacing.md },
  visitHeader: { flexDirection: 'row', alignItems: 'center' },
  visitIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: Colors.accent + '20',
    alignItems: 'center',
    justifyContent: 'center',
  },
  visitInfo: { flex: 1, marginLeft: Spacing.sm },
  visitService: { fontSize: Typography.body, fontWeight: Typography.semibold, color: Colors.text },
  visitDate: { fontSize: Typography.caption, color: Colors.textSecondary },
  statusBadge: { paddingHorizontal: Spacing.sm, paddingVertical: 4, borderRadius: 12 },
  statusText: { fontSize: Typography.caption, fontWeight: Typography.semibold, textTransform: 'capitalize' },
  visitNotes: { fontSize: Typography.bodySmall, color: Colors.textSecondary, marginTop: Spacing.sm },
  visitPrice: { fontSize: Typography.body, fontWeight: Typography.semibold, color: Colors.accent, marginTop: Spacing.sm },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: Spacing.xxl * 2,
    gap: Spacing.md,
  },
  emptyTitle: { fontSize: Typography.h3, fontWeight: Typography.semibold, color: Colors.text },
  emptyText: { fontSize: Typography.body, color: Colors.textSecondary, textAlign: 'center' },
  bookButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.accent,
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.md,
    borderRadius: 24,
    gap: Spacing.xs,
    marginTop: Spacing.md,
  },
  bookButtonText: { fontSize: Typography.body, fontWeight: Typography.semibold, color: Colors.buttonText },
});
