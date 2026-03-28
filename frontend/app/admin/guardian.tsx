import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { Card } from '../../components/Card';
import Colors from '../../constants/Colors';
import Spacing from '../../constants/Spacing';
import Typography from '../../constants/Typography';
import api from '../../utils/api';
import { useAuthStore } from '../../store/authStore';

interface SystemAction {
  id: string;
  type: string;
  user_name: string;
  user_email: string;
  strike_number?: number;
  action: string;
  action_label: string;
  violation_type?: string;
  duration_hours?: number;
  suspended_until?: string;
  message: string;
  created_at: string;
  status: string;
}

interface GuardianSummary {
  system_health: string;
  actions_last_24h: number;
  actions_last_7d: number;
  currently_suspended: number;
  restored_last_24h: number;
  banned_users: number;
  pending_appeals: number;
  requires_attention: boolean;
  recent_actions: Array<{
    type: string;
    user_name: string;
    action_label: string;
    message: string;
    created_at: string;
  }>;
}

interface ActiveSuspension {
  user_id: string;
  user_name: string;
  user_email: string;
  strike_count: number;
  suspension_reason: string;
  suspended_until: string;
  hours_remaining: number;
  auto_restore: boolean;
  status: string;
}

const ACTION_ICONS: Record<string, string> = {
  'system_auto_action': 'flash',
  'system_auto_restore': 'refresh-circle',
  'warning': 'warning',
  'suspend': 'time',
  'ban': 'ban',
};

const ACTION_COLORS: Record<string, string> = {
  'warning': '#FF9500',
  'suspend': '#5856D6',
  'ban': '#FF3B30',
  'system_auto_restore': '#34C759',
};

export default function GuardianDashboardScreen() {
  const router = useRouter();
  const { user } = useAuthStore();
  
  const [summary, setSummary] = useState<GuardianSummary | null>(null);
  const [actions, setActions] = useState<SystemAction[]>([]);
  const [suspensions, setSuspensions] = useState<ActiveSuspension[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState<'summary' | 'history' | 'active'>('summary');
  
  const loadData = useCallback(async () => {
    try {
      const [summaryRes, actionsRes, suspensionsRes] = await Promise.all([
        api.get('/admin/guardian/summary'),
        api.get('/admin/guardian/actions?limit=20'),
        api.get('/admin/guardian/active-suspensions'),
      ]);
      
      setSummary(summaryRes.data);
      setActions(actionsRes.data);
      setSuspensions(suspensionsRes.data.suspensions || []);
    } catch (error: any) {
      if (error.response?.status === 403) {
        router.back();
      }
    } finally {
      setLoading(false);
    }
  }, [router]);
  
  useEffect(() => {
    loadData();
  }, [loadData]);
  
  const handleRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };
  
  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };
  
  const renderSummaryCard = (title: string, value: number, icon: string, color: string, subtitle?: string) => (
    <View style={[styles.summaryCard, { borderLeftColor: color }]}>
      <Ionicons name={icon as any} size={28} color={color} />
      <Text style={styles.summaryValue}>{value}</Text>
      <Text style={styles.summaryTitle}>{title}</Text>
      {subtitle && <Text style={styles.summarySubtitle}>{subtitle}</Text>}
    </View>
  );
  
  const renderActionItem = (action: SystemAction) => {
    const iconName = ACTION_ICONS[action.type] || ACTION_ICONS[action.action] || 'flash';
    const color = ACTION_COLORS[action.action] || Colors.accent;
    
    return (
      <Card key={action.id} style={styles.actionCard}>
        <View style={styles.actionHeader}>
          <View style={[styles.actionIcon, { backgroundColor: color + '20' }]}>
            <Ionicons name={iconName as any} size={20} color={color} />
          </View>
          <View style={styles.actionInfo}>
            <Text style={styles.actionLabel}>{action.action_label}</Text>
            <Text style={styles.actionTime}>{formatTimeAgo(action.created_at)}</Text>
          </View>
        </View>
        
        <View style={styles.actionBody}>
          <Text style={styles.actionUser}>{action.user_name}</Text>
          <Text style={styles.actionMessage}>{action.message}</Text>
          
          {action.violation_type && (
            <View style={styles.violationTag}>
              <Text style={styles.violationText}>{action.violation_type}</Text>
            </View>
          )}
          
          {action.strike_number && (
            <Text style={styles.strikeText}>Strike #{action.strike_number}</Text>
          )}
        </View>
        
        <View style={styles.actionFooter}>
          <View style={[styles.statusBadge, { backgroundColor: Colors.success + '20' }]}>
            <Ionicons name="checkmark-circle" size={14} color={Colors.success} />
            <Text style={[styles.statusText, { color: Colors.success }]}>Completed</Text>
          </View>
          <Text style={styles.noActionText}>No action required</Text>
        </View>
      </Card>
    );
  };
  
  const renderSuspensionItem = (suspension: ActiveSuspension) => (
    <Card key={suspension.user_id} style={styles.suspensionCard}>
      <View style={styles.suspensionHeader}>
        <View style={styles.suspensionUser}>
          <Ionicons name="person-circle" size={40} color={Colors.textSecondary} />
          <View>
            <Text style={styles.suspensionName}>{suspension.user_name}</Text>
            <Text style={styles.suspensionEmail}>{suspension.user_email}</Text>
          </View>
        </View>
        <View style={styles.countdownBadge}>
          <Text style={styles.countdownValue}>{suspension.hours_remaining.toFixed(0)}h</Text>
          <Text style={styles.countdownLabel}>remaining</Text>
        </View>
      </View>
      
      <View style={styles.suspensionDetails}>
        <Text style={styles.suspensionReason}>{suspension.suspension_reason}</Text>
        <Text style={styles.strikeCount}>Strike #{suspension.strike_count}</Text>
      </View>
      
      <View style={styles.autoRestoreBanner}>
        <Ionicons name="refresh-circle" size={18} color={Colors.success} />
        <Text style={styles.autoRestoreText}>Will auto-restore when timer expires</Text>
      </View>
    </Card>
  );
  
  if (loading) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={Colors.accent} />
          <Text style={styles.loadingText}>Loading Guardian Dashboard...</Text>
        </View>
      </SafeAreaView>
    );
  }
  
  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color={Colors.text} />
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <Text style={styles.headerTitle}>Guardian Dashboard</Text>
          <View style={styles.systemStatus}>
            <View style={[styles.statusDot, { backgroundColor: Colors.success }]} />
            <Text style={styles.systemStatusText}>System Active</Text>
          </View>
        </View>
        <View style={{ width: 40 }} />
      </View>
      
      {/* Tabs */}
      <View style={styles.tabs}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'summary' && styles.tabActive]}
          onPress={() => setActiveTab('summary')}
        >
          <Ionicons 
            name="analytics" 
            size={18} 
            color={activeTab === 'summary' ? Colors.accent : Colors.textSecondary} 
          />
          <Text style={[styles.tabText, activeTab === 'summary' && styles.tabTextActive]}>
            Summary
          </Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={[styles.tab, activeTab === 'history' && styles.tabActive]}
          onPress={() => setActiveTab('history')}
        >
          <Ionicons 
            name="time" 
            size={18} 
            color={activeTab === 'history' ? Colors.accent : Colors.textSecondary} 
          />
          <Text style={[styles.tabText, activeTab === 'history' && styles.tabTextActive]}>
            Action Log
          </Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={[styles.tab, activeTab === 'active' && styles.tabActive]}
          onPress={() => setActiveTab('active')}
        >
          <Ionicons 
            name="hourglass" 
            size={18} 
            color={activeTab === 'active' ? Colors.accent : Colors.textSecondary} 
          />
          <Text style={[styles.tabText, activeTab === 'active' && styles.tabTextActive]}>
            Active
          </Text>
          {suspensions.length > 0 && (
            <View style={styles.tabBadge}>
              <Text style={styles.tabBadgeText}>{suspensions.length}</Text>
            </View>
          )}
        </TouchableOpacity>
      </View>
      
      <ScrollView
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
            tintColor={Colors.accent}
          />
        }
        contentContainerStyle={styles.scrollContent}
      >
        {activeTab === 'summary' && summary && (
          <>
            {/* System Health Banner */}
            <Card style={styles.healthBanner}>
              <View style={styles.healthContent}>
                <Ionicons name="shield-checkmark" size={32} color={Colors.success} />
                <View style={styles.healthText}>
                  <Text style={styles.healthTitle}>System Operating Normally</Text>
                  <Text style={styles.healthSubtitle}>
                    Automated moderation is active. No manual intervention needed.
                  </Text>
                </View>
              </View>
            </Card>
            
            {/* Summary Stats */}
            <Text style={styles.sectionTitle}>Last 24 Hours</Text>
            <View style={styles.summaryGrid}>
              {renderSummaryCard('Actions Taken', summary.actions_last_24h, 'flash', Colors.accent)}
              {renderSummaryCard('Auto-Restored', summary.restored_last_24h, 'refresh-circle', Colors.success)}
              {renderSummaryCard('Suspended', summary.currently_suspended, 'time', '#5856D6', 'Currently')}
              {renderSummaryCard('Banned', summary.banned_users, 'ban', '#FF3B30', 'Total')}
            </View>
            
            {/* Pending Appeals Alert */}
            {summary.pending_appeals > 0 && (
              <TouchableOpacity 
                style={styles.appealAlert}
                onPress={() => router.push('/admin/moderation')}
              >
                <Ionicons name="hand-left" size={24} color="#FF9500" />
                <View style={styles.appealAlertText}>
                  <Text style={styles.appealAlertTitle}>
                    {summary.pending_appeals} Appeal{summary.pending_appeals > 1 ? 's' : ''} Pending
                  </Text>
                  <Text style={styles.appealAlertSubtitle}>
                    Appeals require manual review
                  </Text>
                </View>
                <Ionicons name="chevron-forward" size={20} color={Colors.textSecondary} />
              </TouchableOpacity>
            )}
            
            {/* Recent Actions */}
            <Text style={styles.sectionTitle}>Recent System Actions</Text>
            {summary.recent_actions.length === 0 ? (
              <Card style={styles.emptyCard}>
                <Ionicons name="checkmark-circle" size={48} color={Colors.success} />
                <Text style={styles.emptyTitle}>All Clear</Text>
                <Text style={styles.emptyText}>No violations detected</Text>
              </Card>
            ) : (
              summary.recent_actions.map((action, idx) => (
                <Card key={idx} style={styles.recentActionCard}>
                  <View style={styles.recentActionRow}>
                    <Ionicons 
                      name={action.type === 'system_auto_restore' ? 'refresh-circle' : 'flash'} 
                      size={20} 
                      color={action.type === 'system_auto_restore' ? Colors.success : Colors.accent} 
                    />
                    <View style={styles.recentActionInfo}>
                      <Text style={styles.recentActionLabel}>{action.action_label}</Text>
                      <Text style={styles.recentActionMessage}>{action.message}</Text>
                    </View>
                    <Text style={styles.recentActionTime}>
                      {formatTimeAgo(action.created_at)}
                    </Text>
                  </View>
                </Card>
              ))
            )}
          </>
        )}
        
        {activeTab === 'history' && (
          <>
            <Text style={styles.sectionTitle}>System Action History</Text>
            <Text style={styles.sectionSubtitle}>
              All actions are automated. This is a read-only log.
            </Text>
            
            {actions.length === 0 ? (
              <Card style={styles.emptyCard}>
                <Ionicons name="document-text-outline" size={48} color={Colors.textSecondary} />
                <Text style={styles.emptyTitle}>No Actions Yet</Text>
                <Text style={styles.emptyText}>
                  System actions will appear here when violations are detected
                </Text>
              </Card>
            ) : (
              actions.map(renderActionItem)
            )}
          </>
        )}
        
        {activeTab === 'active' && (
          <>
            <Text style={styles.sectionTitle}>Active Suspensions</Text>
            <Text style={styles.sectionSubtitle}>
              These will automatically expire. No manual unblocking needed.
            </Text>
            
            {suspensions.length === 0 ? (
              <Card style={styles.emptyCard}>
                <Ionicons name="checkmark-done-circle" size={48} color={Colors.success} />
                <Text style={styles.emptyTitle}>No Active Suspensions</Text>
                <Text style={styles.emptyText}>
                  All users are currently in good standing
                </Text>
              </Card>
            ) : (
              suspensions.map(renderSuspensionItem)
            )}
          </>
        )}
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
    gap: Spacing.md,
  },
  loadingText: {
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
  headerCenter: {
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: Typography.h3,
    fontWeight: Typography.bold as any,
    color: Colors.text,
  },
  systemStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 4,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  systemStatusText: {
    fontSize: Typography.caption,
    color: Colors.success,
  },
  tabs: {
    flexDirection: 'row',
    paddingHorizontal: Spacing.screenPadding,
    paddingVertical: Spacing.sm,
    gap: Spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  tab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: Spacing.sm,
    borderRadius: 8,
    backgroundColor: Colors.backgroundSecondary,
  },
  tabActive: {
    backgroundColor: Colors.accent + '20',
  },
  tabText: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    fontWeight: Typography.medium as any,
  },
  tabTextActive: {
    color: Colors.accent,
  },
  tabBadge: {
    backgroundColor: Colors.accent,
    borderRadius: 10,
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  tabBadgeText: {
    fontSize: 10,
    color: Colors.background,
    fontWeight: Typography.bold as any,
  },
  scrollContent: {
    padding: Spacing.screenPadding,
    paddingBottom: Spacing.xxl,
  },
  healthBanner: {
    backgroundColor: Colors.success + '15',
    borderWidth: 1,
    borderColor: Colors.success + '30',
    marginBottom: Spacing.lg,
  },
  healthContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.md,
  },
  healthText: {
    flex: 1,
  },
  healthTitle: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold as any,
    color: Colors.success,
  },
  healthSubtitle: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  sectionTitle: {
    fontSize: Typography.h4,
    fontWeight: Typography.semibold as any,
    color: Colors.text,
    marginBottom: Spacing.sm,
  },
  sectionSubtitle: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    marginBottom: Spacing.md,
  },
  summaryGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.sm,
    marginBottom: Spacing.lg,
  },
  summaryCard: {
    width: '48%',
    backgroundColor: Colors.backgroundSecondary,
    borderRadius: 12,
    padding: Spacing.md,
    borderLeftWidth: 3,
    alignItems: 'center',
  },
  summaryValue: {
    fontSize: 28,
    fontWeight: Typography.bold as any,
    color: Colors.text,
    marginTop: Spacing.sm,
  },
  summaryTitle: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  summarySubtitle: {
    fontSize: Typography.caption,
    color: Colors.textSecondary,
  },
  appealAlert: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FF9500' + '20',
    borderRadius: 12,
    padding: Spacing.md,
    marginBottom: Spacing.lg,
    gap: Spacing.md,
    borderWidth: 1,
    borderColor: '#FF9500' + '30',
  },
  appealAlertText: {
    flex: 1,
  },
  appealAlertTitle: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold as any,
    color: '#FF9500',
  },
  appealAlertSubtitle: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
  },
  emptyCard: {
    alignItems: 'center',
    padding: Spacing.xl,
  },
  emptyTitle: {
    fontSize: Typography.h4,
    fontWeight: Typography.semibold as any,
    color: Colors.text,
    marginTop: Spacing.md,
  },
  emptyText: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
    marginTop: Spacing.xs,
    textAlign: 'center',
  },
  recentActionCard: {
    marginBottom: Spacing.sm,
  },
  recentActionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.md,
  },
  recentActionInfo: {
    flex: 1,
  },
  recentActionLabel: {
    fontSize: Typography.body,
    fontWeight: Typography.medium as any,
    color: Colors.text,
  },
  recentActionMessage: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
  },
  recentActionTime: {
    fontSize: Typography.caption,
    color: Colors.textSecondary,
  },
  actionCard: {
    marginBottom: Spacing.md,
  },
  actionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.md,
    marginBottom: Spacing.sm,
  },
  actionIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  actionInfo: {
    flex: 1,
  },
  actionLabel: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold as any,
    color: Colors.text,
  },
  actionTime: {
    fontSize: Typography.caption,
    color: Colors.textSecondary,
  },
  actionBody: {
    paddingLeft: 52,
    marginBottom: Spacing.sm,
  },
  actionUser: {
    fontSize: Typography.body,
    fontWeight: Typography.medium as any,
    color: Colors.text,
  },
  actionMessage: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  violationTag: {
    backgroundColor: Colors.error + '20',
    borderRadius: 4,
    paddingHorizontal: 8,
    paddingVertical: 2,
    alignSelf: 'flex-start',
    marginTop: Spacing.xs,
  },
  violationText: {
    fontSize: Typography.caption,
    color: Colors.error,
    textTransform: 'capitalize',
  },
  strikeText: {
    fontSize: Typography.caption,
    color: Colors.textSecondary,
    marginTop: 4,
  },
  actionFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingLeft: 52,
    paddingTop: Spacing.sm,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    fontSize: Typography.caption,
    fontWeight: Typography.medium as any,
  },
  noActionText: {
    fontSize: Typography.caption,
    color: Colors.textSecondary,
    fontStyle: 'italic',
  },
  suspensionCard: {
    marginBottom: Spacing.md,
  },
  suspensionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.sm,
  },
  suspensionUser: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
  },
  suspensionName: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold as any,
    color: Colors.text,
  },
  suspensionEmail: {
    fontSize: Typography.caption,
    color: Colors.textSecondary,
  },
  countdownBadge: {
    backgroundColor: '#5856D6' + '20',
    borderRadius: 8,
    padding: Spacing.sm,
    alignItems: 'center',
  },
  countdownValue: {
    fontSize: Typography.h4,
    fontWeight: Typography.bold as any,
    color: '#5856D6',
  },
  countdownLabel: {
    fontSize: Typography.caption,
    color: Colors.textSecondary,
  },
  suspensionDetails: {
    backgroundColor: Colors.backgroundSecondary,
    borderRadius: 8,
    padding: Spacing.sm,
    marginBottom: Spacing.sm,
  },
  suspensionReason: {
    fontSize: Typography.bodySmall,
    color: Colors.text,
  },
  strikeCount: {
    fontSize: Typography.caption,
    color: Colors.textSecondary,
    marginTop: 4,
  },
  autoRestoreBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.xs,
    backgroundColor: Colors.success + '15',
    borderRadius: 6,
    padding: Spacing.sm,
  },
  autoRestoreText: {
    fontSize: Typography.caption,
    color: Colors.success,
    fontWeight: Typography.medium as any,
  },
});
