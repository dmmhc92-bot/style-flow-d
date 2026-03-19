import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { Card } from '../../components/Card';
import Colors from '../../constants/Colors';
import Spacing from '../../constants/Spacing';
import Typography from '../../constants/Typography';
import { useAuthStore } from '../../store/authStore';
import api from '../../utils/api';

export default function DashboardScreen() {
  const router = useRouter();
  const user = useAuthStore((state) => state.user);
  
  const [stats, setStats] = useState<any>(null);
  const [refreshing, setRefreshing] = useState(false);
  
  const loadStats = async () => {
    try {
      const response = await api.get('/dashboard/stats');
      setStats(response.data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };
  
  useEffect(() => {
    loadStats();
  }, []);
  
  const onRefresh = async () => {
    setRefreshing(true);
    await loadStats();
    setRefreshing(false);
  };
  
  const QuickActionButton = ({ icon, title, onPress }: any) => (
    <TouchableOpacity style={styles.quickAction} onPress={onPress}>
      <View style={styles.quickActionIcon}>
        <Ionicons name={icon} size={24} color={Colors.accent} />
      </View>
      <Text style={styles.quickActionText}>{title}</Text>
    </TouchableOpacity>
  );
  
  const StatCard = ({ title, value, icon, color }: any) => (
    <Card style={styles.statCard}>
      <View style={[styles.statIconContainer, { backgroundColor: color + '15' }]}>
        <Ionicons name={icon} size={24} color={color} />
      </View>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statTitle}>{title}</Text>
    </Card>
  );
  
  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {/* Header */}
        <View style={styles.header}>
          <View>
            <Text style={styles.greeting}>Hello,</Text>
            <Text style={styles.name}>{user?.full_name || 'Stylist'}</Text>
          </View>
          <TouchableOpacity
            style={styles.aiButton}
            onPress={() => router.push('/ai/chat')}
          >
            <Ionicons name="sparkles" size={24} color={Colors.accent} />
          </TouchableOpacity>
        </View>
        
        {/* Quick Stats */}
        <View style={styles.statsGrid}>
          <StatCard
            title="Today's Income"
            value={`$${stats?.today_income?.toFixed(0) || 0}`}
            icon="cash-outline"
            color={Colors.success}
          />
          <StatCard
            title="Appointments"
            value={stats?.today_appointments || 0}
            icon="calendar-outline"
            color={Colors.info}
          />
          <StatCard
            title="Total Clients"
            value={stats?.total_clients || 0}
            icon="people-outline"
            color={Colors.accent}
          />
          <StatCard
            title="VIP Clients"
            value={stats?.vip_clients || 0}
            icon="star-outline"
            color={Colors.vip}
          />
        </View>
        
        {/* Monthly Overview */}
        <Card style={styles.overviewCard}>
          <Text style={styles.sectionTitle}>This Month</Text>
          <View style={styles.overviewRow}>
            <View style={styles.overviewItem}>
              <Text style={styles.overviewLabel}>Revenue</Text>
              <Text style={styles.overviewValue}>
                ${stats?.month_income?.toFixed(0) || 0}
              </Text>
            </View>
            <View style={styles.overviewDivider} />
            <View style={styles.overviewItem}>
              <Text style={styles.overviewLabel}>Appointments</Text>
              <Text style={styles.overviewValue}>
                {stats?.week_appointments || 0}
              </Text>
            </View>
          </View>
        </Card>
        
        {/* Rebooking Alert */}
        {stats?.clients_due_rebooking > 0 && (
          <Card style={styles.alertCard}>
            <View style={styles.alertContent}>
              <Ionicons name="alert-circle" size={24} color={Colors.warning} />
              <View style={styles.alertText}>
                <Text style={styles.alertTitle}>Rebooking Reminder</Text>
                <Text style={styles.alertMessage}>
                  {stats.clients_due_rebooking} client{stats.clients_due_rebooking > 1 ? 's' : ''} haven't visited in 60+ days
                </Text>
              </View>
            </View>
            <TouchableOpacity
              style={styles.alertButton}
              onPress={() => router.push('/tabs/clients')}
            >
              <Text style={styles.alertButtonText}>View Clients</Text>
            </TouchableOpacity>
          </Card>
        )}
        
        {/* Quick Actions */}
        <Text style={styles.sectionTitle}>Quick Actions</Text>
        <View style={styles.quickActionsGrid}>
          <QuickActionButton
            icon="person-add"
            title="New Client"
            onPress={() => router.push('/client/add')}
          />
          <QuickActionButton
            icon="calendar-outline"
            title="Book Appointment"
            onPress={() => router.push('/appointment/add')}
          />
          <QuickActionButton
            icon="camera"
            title="Add Photos"
            onPress={() => router.push('/tabs/gallery')}
          />
          <QuickActionButton
            icon="flask"
            title="Save Formula"
            onPress={() => router.push('/tabs/clients')}
          />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  scrollContent: {
    padding: Spacing.screenPadding,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.lg,
  },
  greeting: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
  },
  name: {
    fontSize: Typography.h2,
    fontWeight: Typography.bold,
    color: Colors.text,
  },
  aiButton: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: Colors.backgroundSecondary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginHorizontal: -Spacing.xs,
    marginBottom: Spacing.lg,
  },
  statCard: {
    width: '48%',
    marginHorizontal: '1%',
    marginBottom: Spacing.md,
    alignItems: 'center',
    paddingVertical: Spacing.lg,
  },
  statIconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.sm,
  },
  statValue: {
    fontSize: Typography.h2,
    fontWeight: Typography.bold,
    color: Colors.text,
    marginBottom: Spacing.xs,
  },
  statTitle: {
    fontSize: Typography.caption,
    color: Colors.textSecondary,
    textAlign: 'center',
  },
  overviewCard: {
    marginBottom: Spacing.lg,
  },
  sectionTitle: {
    fontSize: Typography.h4,
    fontWeight: Typography.semibold,
    color: Colors.text,
    marginBottom: Spacing.md,
  },
  overviewRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  overviewItem: {
    flex: 1,
    alignItems: 'center',
  },
  overviewDivider: {
    width: 1,
    height: 40,
    backgroundColor: Colors.border,
  },
  overviewLabel: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    marginBottom: Spacing.xs,
  },
  overviewValue: {
    fontSize: Typography.h3,
    fontWeight: Typography.bold,
    color: Colors.text,
  },
  alertCard: {
    marginBottom: Spacing.lg,
    backgroundColor: Colors.warning + '10',
    borderWidth: 1,
    borderColor: Colors.warning + '30',
  },
  alertContent: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: Spacing.md,
  },
  alertText: {
    flex: 1,
    marginLeft: Spacing.md,
  },
  alertTitle: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold,
    color: Colors.text,
    marginBottom: Spacing.xs,
  },
  alertMessage: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
  },
  alertButton: {
    backgroundColor: Colors.warning,
    paddingVertical: Spacing.sm,
    paddingHorizontal: Spacing.md,
    borderRadius: 8,
    alignSelf: 'flex-start',
  },
  alertButtonText: {
    fontSize: Typography.bodySmall,
    fontWeight: Typography.semibold,
    color: Colors.textInverse,
  },
  quickActionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginHorizontal: -Spacing.xs,
  },
  quickAction: {
    width: '48%',
    marginHorizontal: '1%',
    marginBottom: Spacing.md,
    backgroundColor: Colors.cardBackground,
    borderRadius: 16,
    padding: Spacing.md,
    alignItems: 'center',
    shadowColor: Colors.shadow,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  quickActionIcon: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: Colors.accent + '15',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.sm,
  },
  quickActionText: {
    fontSize: Typography.bodySmall,
    fontWeight: Typography.medium,
    color: Colors.text,
    textAlign: 'center',
  },
});