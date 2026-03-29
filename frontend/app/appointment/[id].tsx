import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { Card } from '../../components/Card';
import Button from '../../components/Button';
import Colors from '../../constants/Colors';
import Spacing from '../../constants/Spacing';
import Typography from '../../constants/Typography';
import api from '../../utils/api';
import { format } from 'date-fns';

interface Appointment {
  id: string;
  client_id: string;
  client_name?: string;
  appointment_date: string;
  service: string;
  duration_minutes: number;
  notes?: string;
  status: string;
  created_at: string;
}

export default function AppointmentDetailScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams();
  
  const [appointment, setAppointment] = useState<Appointment | null>(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);
  
  useEffect(() => {
    loadAppointment();
  }, [id]);
  
  const loadAppointment = async () => {
    try {
      const response = await api.get(`/appointments/${id}`);
      setAppointment(response.data);
    } catch (error) {
      Alert.alert('Error', 'Failed to load appointment');
      router.back();
    } finally {
      setLoading(false);
    }
  };
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return Colors.success;
      case 'scheduled':
        return Colors.info || '#007AFF';
      case 'cancelled':
        return Colors.error;
      case 'no_show':
        return Colors.warning || '#FF9500';
      default:
        return Colors.textSecondary;
    }
  };
  
  const handleStatusChange = async (newStatus: string) => {
    try {
      await api.put(`/appointments/${id}`, { status: newStatus });
      setAppointment(prev => prev ? { ...prev, status: newStatus } : null);
      Alert.alert('Success', `Appointment marked as ${newStatus.replace('_', ' ')}`);
    } catch (error) {
      Alert.alert('Error', 'Failed to update appointment status');
    }
  };
  
  const handleDelete = () => {
    Alert.alert(
      'Delete Appointment',
      'Are you sure you want to delete this appointment? This action cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            setDeleting(true);
            try {
              await api.delete(`/appointments/${id}`);
              Alert.alert('Deleted', 'Appointment has been deleted', [
                { text: 'OK', onPress: () => router.replace('/tabs/appointments') }
              ]);
            } catch (error) {
              Alert.alert('Error', 'Failed to delete appointment');
              setDeleting(false);
            }
          },
        },
      ]
    );
  };
  
  if (loading) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={Colors.accent} />
        </View>
      </SafeAreaView>
    );
  }
  
  if (!appointment) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={styles.loadingContainer}>
          <Text style={styles.errorText}>Appointment not found</Text>
        </View>
      </SafeAreaView>
    );
  }
  
  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color={Colors.text} />
        </TouchableOpacity>
        <Text style={styles.title}>Appointment Details</Text>
        <TouchableOpacity 
          style={styles.deleteButton} 
          onPress={handleDelete}
          disabled={deleting}
        >
          {deleting ? (
            <ActivityIndicator size="small" color={Colors.error} />
          ) : (
            <Ionicons name="trash-outline" size={24} color={Colors.error} />
          )}
        </TouchableOpacity>
      </View>
      
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Date & Time Card */}
        <Card style={styles.card}>
          <View style={styles.dateTimeHeader}>
            <View style={styles.dateBox}>
              <Text style={styles.dateDay}>
                {format(new Date(appointment.appointment_date), 'dd')}
              </Text>
              <Text style={styles.dateMonth}>
                {format(new Date(appointment.appointment_date), 'MMM yyyy')}
              </Text>
            </View>
            <View style={styles.timeInfo}>
              <Text style={styles.timeText}>
                {format(new Date(appointment.appointment_date), 'h:mm a')}
              </Text>
              <Text style={styles.durationText}>
                {appointment.duration_minutes} minutes
              </Text>
            </View>
          </View>
        </Card>
        
        {/* Status Card */}
        <Card style={styles.card}>
          <Text style={styles.sectionTitle}>Status</Text>
          <View style={[styles.statusBadge, { backgroundColor: getStatusColor(appointment.status) + '20' }]}>
            <View style={[styles.statusDot, { backgroundColor: getStatusColor(appointment.status) }]} />
            <Text style={[styles.statusText, { color: getStatusColor(appointment.status) }]}>
              {appointment.status.replace('_', ' ').toUpperCase()}
            </Text>
          </View>
          
          {appointment.status === 'scheduled' && (
            <View style={styles.statusActions}>
              <TouchableOpacity 
                style={[styles.statusButton, { backgroundColor: Colors.success + '20' }]}
                onPress={() => handleStatusChange('completed')}
              >
                <Ionicons name="checkmark-circle" size={20} color={Colors.success} />
                <Text style={[styles.statusButtonText, { color: Colors.success }]}>Complete</Text>
              </TouchableOpacity>
              
              <TouchableOpacity 
                style={[styles.statusButton, { backgroundColor: Colors.warning + '20' }]}
                onPress={() => handleStatusChange('no_show')}
              >
                <Ionicons name="alert-circle" size={20} color={Colors.warning || '#FF9500'} />
                <Text style={[styles.statusButtonText, { color: Colors.warning || '#FF9500' }]}>No Show</Text>
              </TouchableOpacity>
              
              <TouchableOpacity 
                style={[styles.statusButton, { backgroundColor: Colors.error + '20' }]}
                onPress={() => handleStatusChange('cancelled')}
              >
                <Ionicons name="close-circle" size={20} color={Colors.error} />
                <Text style={[styles.statusButtonText, { color: Colors.error }]}>Cancel</Text>
              </TouchableOpacity>
            </View>
          )}
        </Card>
        
        {/* Service Info */}
        <Card style={styles.card}>
          <Text style={styles.sectionTitle}>Service</Text>
          <Text style={styles.serviceText}>{appointment.service}</Text>
          
          {appointment.client_name && (
            <>
              <Text style={[styles.sectionTitle, { marginTop: Spacing.md }]}>Client</Text>
              <TouchableOpacity 
                style={styles.clientRow}
                onPress={() => router.push(`/client/${appointment.client_id}`)}
              >
                <Ionicons name="person-circle" size={40} color={Colors.accent} />
                <Text style={styles.clientName}>{appointment.client_name}</Text>
                <Ionicons name="chevron-forward" size={20} color={Colors.textSecondary} />
              </TouchableOpacity>
            </>
          )}
        </Card>
        
        {/* Notes */}
        {appointment.notes && (
          <Card style={styles.card}>
            <Text style={styles.sectionTitle}>Notes</Text>
            <Text style={styles.notesText}>{appointment.notes}</Text>
          </Card>
        )}
        
        {/* Delete Button */}
        <Button
          title="Delete Appointment"
          onPress={handleDelete}
          variant="danger"
          style={styles.deleteFullButton}
          loading={deleting}
        />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorText: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
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
  backButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    fontSize: Typography.h3,
    fontWeight: Typography.semibold as any,
    color: Colors.text,
  },
  deleteButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  scrollContent: {
    padding: Spacing.screenPadding,
    paddingBottom: Spacing.xxl,
  },
  card: {
    marginBottom: Spacing.md,
  },
  dateTimeHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  dateBox: {
    backgroundColor: Colors.accent + '20',
    borderRadius: 12,
    padding: Spacing.md,
    alignItems: 'center',
    marginRight: Spacing.md,
  },
  dateDay: {
    fontSize: 28,
    fontWeight: Typography.bold as any,
    color: Colors.accent,
  },
  dateMonth: {
    fontSize: Typography.caption,
    color: Colors.accent,
  },
  timeInfo: {
    flex: 1,
  },
  timeText: {
    fontSize: Typography.h4,
    fontWeight: Typography.semibold as any,
    color: Colors.text,
  },
  durationText: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
    marginTop: 4,
  },
  sectionTitle: {
    fontSize: Typography.caption,
    fontWeight: Typography.semibold as any,
    color: Colors.textSecondary,
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: Spacing.sm,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    borderRadius: 20,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: Spacing.sm,
  },
  statusText: {
    fontSize: Typography.bodySmall,
    fontWeight: Typography.semibold as any,
  },
  statusActions: {
    flexDirection: 'row',
    marginTop: Spacing.md,
    gap: Spacing.sm,
  },
  statusButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: Spacing.sm,
    borderRadius: 8,
    gap: 4,
  },
  statusButtonText: {
    fontSize: Typography.caption,
    fontWeight: Typography.medium as any,
  },
  serviceText: {
    fontSize: Typography.body,
    color: Colors.text,
    fontWeight: Typography.medium as any,
  },
  clientRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.backgroundSecondary,
    borderRadius: 12,
    padding: Spacing.sm,
  },
  clientName: {
    flex: 1,
    fontSize: Typography.body,
    color: Colors.text,
    marginLeft: Spacing.sm,
    fontWeight: Typography.medium as any,
  },
  notesText: {
    fontSize: Typography.body,
    color: Colors.text,
    lineHeight: 22,
  },
  deleteFullButton: {
    marginTop: Spacing.lg,
  },
});
