import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { Card } from '../../components/Card';
import { SyncIndicatorCompact } from '../../components/SyncIndicator';
import Colors from '../../constants/Colors';
import Spacing from '../../constants/Spacing';
import Typography from '../../constants/Typography';
import { useOfflineAppointments } from '../../hooks/useOfflineData';
import { format } from 'date-fns';

export default function AppointmentsScreen() {
  const router = useRouter();
  
  const { appointments, loading, refreshing, onRefresh } = useOfflineAppointments();
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return Colors.success;
      case 'scheduled':
        return Colors.info;
      case 'cancelled':
        return Colors.error;
      case 'no_show':
        return Colors.warning;
      default:
        return Colors.textSecondary;
    }
  };
  
  const renderAppointment = ({ item }: any) => (
    <Card
      style={styles.appointmentCard}
      onPress={() => router.push(`/appointment/${item.id}`)}
    >
      <View style={styles.appointmentHeader}>
        <View style={styles.dateContainer}>
          <Text style={styles.dateDay}>
            {format(new Date(item.appointment_date), 'dd')}
          </Text>
          <Text style={styles.dateMonth}>
            {format(new Date(item.appointment_date), 'MMM')}
          </Text>
        </View>
        
        <View style={styles.appointmentInfo}>
          <View style={styles.clientRow}>
            <Text style={styles.clientName}>{item.client_name || 'Unknown Client'}</Text>
            {item._pendingSync && (
              <Ionicons name="cloud-upload-outline" size={14} color={Colors.accent} style={styles.syncIcon} />
            )}
          </View>
          <Text style={styles.service}>{item.service}</Text>
          <View style={styles.appointmentMeta}>
            <Ionicons name="time-outline" size={14} color={Colors.textSecondary} />
            <Text style={styles.time}>
              {format(new Date(item.appointment_date), 'h:mm a')} • {item.duration_minutes} min
            </Text>
          </View>
        </View>
        
        <View style={[styles.statusBadge, { backgroundColor: getStatusColor(item.status) + '20' }]}>
          <Text style={[styles.statusText, { color: getStatusColor(item.status) }]}>
            {item.status}
          </Text>
        </View>
      </View>
    </Card>
  );
  
  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <Text style={styles.title}>Appointments</Text>
        <View style={styles.headerRight}>
          <SyncIndicatorCompact />
          <TouchableOpacity
            style={styles.addButton}
            onPress={() => router.push('/appointment/add')}
          >
            <Ionicons name="add" size={24} color={Colors.textInverse} />
          </TouchableOpacity>
        </View>
      </View>
      
      <FlatList
        data={appointments}
        renderItem={renderAppointment}
        keyExtractor={(item: any) => item.id || item.localId}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={Colors.accent} />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Ionicons name="calendar-outline" size={64} color={Colors.textLight} />
            <Text style={styles.emptyText}>No appointments</Text>
            <Text style={styles.emptySubtext}>Schedule your first appointment</Text>
          </View>
        }
      />
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
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  title: {
    fontSize: Typography.h2,
    fontWeight: Typography.bold,
    color: Colors.text,
  },
  addButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: Colors.accent,
    alignItems: 'center',
    justifyContent: 'center',
  },
  list: {
    padding: Spacing.screenPadding,
  },
  appointmentCard: {
    marginBottom: Spacing.md,
  },
  appointmentHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  dateContainer: {
    width: 56,
    height: 56,
    borderRadius: 12,
    backgroundColor: Colors.accent + '15',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: Spacing.md,
  },
  dateDay: {
    fontSize: Typography.h3,
    fontWeight: Typography.bold,
    color: Colors.accent,
  },
  dateMonth: {
    fontSize: Typography.caption,
    color: Colors.accent,
    textTransform: 'uppercase',
  },
  appointmentInfo: {
    flex: 1,
  },
  clientRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  clientName: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold,
    color: Colors.text,
    marginBottom: 2,
  },
  syncIcon: {
    marginLeft: Spacing.xs,
  },
  service: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    marginBottom: Spacing.xs,
  },
  appointmentMeta: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  time: {
    fontSize: Typography.caption,
    color: Colors.textSecondary,
    marginLeft: Spacing.xs,
  },
  statusBadge: {
    paddingHorizontal: Spacing.sm,
    paddingVertical: Spacing.xs,
    borderRadius: 8,
  },
  statusText: {
    fontSize: Typography.caption,
    fontWeight: Typography.medium,
    textTransform: 'capitalize',
  },
  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: Spacing.xxl,
  },
  emptyText: {
    fontSize: Typography.h4,
    fontWeight: Typography.semibold,
    color: Colors.textSecondary,
    marginTop: Spacing.md,
  },
  emptySubtext: {
    fontSize: Typography.body,
    color: Colors.textLight,
    marginTop: Spacing.xs,
  },
});
