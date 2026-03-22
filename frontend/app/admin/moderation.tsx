import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  RefreshControl,
  Animated,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { Card } from '../../components/Card';
import Button from '../../components/Button';
import Colors from '../../constants/Colors';
import Spacing from '../../constants/Spacing';
import Typography from '../../constants/Typography';
import api from '../../utils/api';
import { useAuthStore } from '../../store/authStore';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface ReportedUser {
  user_id: string;
  user: {
    id: string;
    full_name: string;
    email: string;
    moderation_status: string;
    warnings_count: number;
    flagged: boolean;
  };
  report_count: number;
  priority: string;
  reasons: string[];
  reports: Array<{
    id: string;
    reporter_name: string;
    reason: string;
    details: string;
    content_type: string;
    created_at: string;
  }>;
  latest_report_at: string;
}

interface ModerationStats {
  pending_reports: number;
  flagged_users: number;
  high_priority_cases: number;
  warned_users: number;
  suspended_users: number;
  banned_users: number;
}

interface Notification {
  id: string;
  type: string;
  message: string;
  timestamp: Date;
  priority: string;
}

const PRIORITY_COLORS: Record<string, string> = {
  critical: '#FF3B30',
  high: '#FF9500',
  medium: '#FFCC00',
  normal: Colors.textSecondary,
};

const REASON_LABELS: Record<string, string> = {
  harassment: 'Harassment',
  inappropriate: 'Inappropriate',
  spam: 'Spam',
  hate_speech: 'Hate Speech',
  sexual_content: 'Sexual Content',
  illegal: 'Illegal',
  impersonation: 'Impersonation',
  other: 'Other',
};

export default function AdminModerationScreen() {
  const router = useRouter();
  const { user } = useAuthStore();
  
  const [queue, setQueue] = useState<ReportedUser[]>([]);
  const [stats, setStats] = useState<ModerationStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [expandedUser, setExpandedUser] = useState<string | null>(null);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [wsConnected, setWsConnected] = useState(false);
  
  const wsRef = useRef<WebSocket | null>(null);
  const pulseAnim = useRef(new Animated.Value(1)).current;
  
  // Pulse animation for new notifications
  const startPulse = useCallback(() => {
    Animated.sequence([
      Animated.timing(pulseAnim, {
        toValue: 1.2,
        duration: 200,
        useNativeDriver: true,
      }),
      Animated.timing(pulseAnim, {
        toValue: 1,
        duration: 200,
        useNativeDriver: true,
      }),
    ]).start();
  }, [pulseAnim]);
  
  // WebSocket connection for real-time updates
  const connectWebSocket = useCallback(async () => {
    try {
      const token = await AsyncStorage.getItem('token');
      if (!token) return;
      
      // Get the base URL and convert to WebSocket URL
      const baseUrl = api.defaults.baseURL || '';
      const wsUrl = baseUrl.replace('http', 'ws').replace('/api', '') + `/ws/admin/moderation?token=${token}`;
      
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('Admin WebSocket connected');
        setWsConnected(true);
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleWebSocketMessage(data);
        } catch (e) {
          console.error('WebSocket message parse error:', e);
        }
      };
      
      ws.onclose = () => {
        console.log('Admin WebSocket disconnected');
        setWsConnected(false);
        // Attempt reconnect after 5 seconds
        setTimeout(connectWebSocket, 5000);
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
      wsRef.current = ws;
      
      // Keep-alive ping every 30 seconds
      const pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }));
        }
      }, 30000);
      
      return () => {
        clearInterval(pingInterval);
        ws.close();
      };
    } catch (error) {
      console.error('WebSocket connection error:', error);
    }
  }, []);
  
  const handleWebSocketMessage = useCallback((data: any) => {
    switch (data.type) {
      case 'new_report':
        // Add notification
        const newNotification: Notification = {
          id: data.report_id,
          type: 'new_report',
          message: `New ${data.priority} priority report: ${data.reported_user.name} reported for ${data.reason}`,
          timestamp: new Date(),
          priority: data.priority,
        };
        setNotifications(prev => [newNotification, ...prev.slice(0, 9)]);
        
        // Refresh queue
        loadQueue();
        loadStats();
        startPulse();
        break;
        
      case 'action_taken':
      case 'bulk_action_taken':
        // Refresh queue after action
        loadQueue();
        loadStats();
        break;
        
      case 'queue_update':
        setQueue(data.data);
        break;
        
      case 'connected':
        if (data.stats) {
          setStats(prev => prev ? { ...prev, ...data.stats } : null);
        }
        break;
    }
  }, [startPulse]);
  
  const loadQueue = async () => {
    try {
      const response = await api.get('/admin/moderation/queue');
      setQueue(response.data);
    } catch (error: any) {
      if (error.response?.status === 403) {
        Alert.alert('Access Denied', 'Admin access required.');
        router.back();
      }
    }
  };
  
  const loadStats = async () => {
    try {
      const response = await api.get('/admin/moderation/stats');
      setStats(response.data);
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };
  
  const loadData = async () => {
    setLoading(true);
    await Promise.all([loadQueue(), loadStats()]);
    setLoading(false);
  };
  
  const handleRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };
  
  useEffect(() => {
    loadData();
    connectWebSocket();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);
  
  const handleAction = async (userId: string, action: string, reason?: string) => {
    const actionLabels: Record<string, string> = {
      dismiss: 'Dismiss all reports',
      warn: 'Issue warning',
      restrict: 'Restrict account',
      suspend: 'Suspend for 7 days',
      ban: 'Permanently ban',
    };
    
    Alert.alert(
      `Confirm: ${actionLabels[action]}`,
      `This will ${action === 'dismiss' ? 'dismiss all reports for' : 'apply to'} this user. Are you sure?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Confirm',
          style: action === 'ban' ? 'destructive' : 'default',
          onPress: async () => {
            setActionLoading(userId);
            try {
              await api.post(`/admin/moderation/action/user/${userId}`, {
                action,
                reason: reason || `${action} via admin dashboard`,
                duration_days: action === 'suspend' ? 7 : undefined,
              });
              
              Alert.alert('Success', `Action '${action}' applied successfully.`);
              await loadData();
            } catch (error: any) {
              Alert.alert('Error', error.response?.data?.detail || 'Action failed');
            } finally {
              setActionLoading(null);
            }
          },
        },
      ]
    );
  };
  
  const renderStatCard = (title: string, value: number, color: string, icon: string) => (
    <View style={[styles.statCard, { borderLeftColor: color }]}>
      <Ionicons name={icon as any} size={24} color={color} />
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{title}</Text>
    </View>
  );
  
  const renderReportedUser = (item: ReportedUser) => {
    const isExpanded = expandedUser === item.user_id;
    const priorityColor = PRIORITY_COLORS[item.priority] || Colors.textSecondary;
    
    return (
      <Card key={item.user_id} style={styles.userCard}>
        <TouchableOpacity
          style={styles.userHeader}
          onPress={() => setExpandedUser(isExpanded ? null : item.user_id)}
        >
          <View style={styles.userInfo}>
            <View style={[styles.priorityBadge, { backgroundColor: priorityColor + '20' }]}>
              <Text style={[styles.priorityText, { color: priorityColor }]}>
                {item.priority.toUpperCase()}
              </Text>
            </View>
            <View style={styles.userDetails}>
              <Text style={styles.userName}>{item.user.full_name}</Text>
              <Text style={styles.userEmail}>{item.user.email}</Text>
            </View>
          </View>
          <View style={styles.userStats}>
            <View style={styles.reportCountBadge}>
              <Text style={styles.reportCount}>{item.report_count}</Text>
              <Text style={styles.reportCountLabel}>reports</Text>
            </View>
            <Ionicons
              name={isExpanded ? 'chevron-up' : 'chevron-down'}
              size={20}
              color={Colors.textSecondary}
            />
          </View>
        </TouchableOpacity>
        
        {isExpanded && (
          <View style={styles.expandedContent}>
            {/* Reasons */}
            <View style={styles.reasonsContainer}>
              <Text style={styles.reasonsLabel}>Report Reasons:</Text>
              <View style={styles.reasonsTags}>
                {item.reasons.map((reason, idx) => (
                  <View key={idx} style={styles.reasonTag}>
                    <Text style={styles.reasonTagText}>
                      {REASON_LABELS[reason] || reason}
                    </Text>
                  </View>
                ))}
              </View>
            </View>
            
            {/* Recent Reports */}
            <View style={styles.reportsSection}>
              <Text style={styles.reportsSectionTitle}>Recent Reports</Text>
              {item.reports.slice(0, 3).map((report, idx) => (
                <View key={idx} style={styles.reportItem}>
                  <View style={styles.reportHeader}>
                    <Text style={styles.reporterName}>{report.reporter_name}</Text>
                    <Text style={styles.reportTime}>
                      {new Date(report.created_at).toLocaleDateString()}
                    </Text>
                  </View>
                  <Text style={styles.reportReason}>{REASON_LABELS[report.reason] || report.reason}</Text>
                  {report.details && (
                    <Text style={styles.reportDetails}>{report.details}</Text>
                  )}
                </View>
              ))}
            </View>
            
            {/* User Status */}
            <View style={styles.statusSection}>
              <Text style={styles.statusLabel}>
                Status: <Text style={styles.statusValue}>{item.user.moderation_status}</Text>
              </Text>
              {item.user.warnings_count > 0 && (
                <Text style={styles.warningsText}>
                  Warnings: {item.user.warnings_count}
                </Text>
              )}
            </View>
            
            {/* Action Buttons */}
            <View style={styles.actionButtons}>
              <TouchableOpacity
                style={[styles.actionBtn, styles.dismissBtn]}
                onPress={() => handleAction(item.user_id, 'dismiss')}
                disabled={actionLoading === item.user_id}
              >
                {actionLoading === item.user_id ? (
                  <ActivityIndicator size="small" color={Colors.text} />
                ) : (
                  <>
                    <Ionicons name="close-circle-outline" size={18} color={Colors.text} />
                    <Text style={styles.actionBtnText}>Dismiss</Text>
                  </>
                )}
              </TouchableOpacity>
              
              <TouchableOpacity
                style={[styles.actionBtn, styles.warnBtn]}
                onPress={() => handleAction(item.user_id, 'warn')}
                disabled={actionLoading === item.user_id}
              >
                <Ionicons name="warning-outline" size={18} color="#FF9500" />
                <Text style={[styles.actionBtnText, { color: '#FF9500' }]}>Warn</Text>
              </TouchableOpacity>
              
              <TouchableOpacity
                style={[styles.actionBtn, styles.suspendBtn]}
                onPress={() => handleAction(item.user_id, 'suspend')}
                disabled={actionLoading === item.user_id}
              >
                <Ionicons name="time-outline" size={18} color="#FF6B6B" />
                <Text style={[styles.actionBtnText, { color: '#FF6B6B' }]}>Suspend</Text>
              </TouchableOpacity>
              
              <TouchableOpacity
                style={[styles.actionBtn, styles.banBtn]}
                onPress={() => handleAction(item.user_id, 'ban')}
                disabled={actionLoading === item.user_id}
              >
                <Ionicons name="ban-outline" size={18} color="#FF3B30" />
                <Text style={[styles.actionBtnText, { color: '#FF3B30' }]}>Ban</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}
      </Card>
    );
  };
  
  if (loading) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={Colors.accent} />
          <Text style={styles.loadingText}>Loading moderation queue...</Text>
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
        <Text style={styles.headerTitle}>Moderation</Text>
        <View style={styles.connectionStatus}>
          <View style={[styles.statusDot, { backgroundColor: wsConnected ? '#4CD964' : '#FF3B30' }]} />
          <Text style={styles.statusText}>{wsConnected ? 'Live' : 'Offline'}</Text>
        </View>
      </View>
      
      {/* Notifications Banner */}
      {notifications.length > 0 && (
        <Animated.View style={[styles.notificationBanner, { transform: [{ scale: pulseAnim }] }]}>
          <Ionicons name="notifications" size={16} color={Colors.accent} />
          <Text style={styles.notificationText} numberOfLines={1}>
            {notifications[0].message}
          </Text>
          <TouchableOpacity onPress={() => setNotifications([])}>
            <Ionicons name="close" size={16} color={Colors.textSecondary} />
          </TouchableOpacity>
        </Animated.View>
      )}
      
      <ScrollView
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={handleRefresh}
            tintColor={Colors.accent}
          />
        }
      >
        {/* Stats Overview */}
        {stats && (
          <View style={styles.statsContainer}>
            {renderStatCard('Pending', stats.pending_reports, '#FF9500', 'alert-circle')}
            {renderStatCard('High Priority', stats.high_priority_cases, '#FF3B30', 'flame')}
            {renderStatCard('Flagged', stats.flagged_users, '#FFCC00', 'flag')}
            {renderStatCard('Suspended', stats.suspended_users, '#5856D6', 'pause-circle')}
          </View>
        )}
        
        {/* Queue */}
        <View style={styles.queueSection}>
          <Text style={styles.sectionTitle}>
            Report Queue ({queue.length})
          </Text>
          
          {queue.length === 0 ? (
            <Card style={styles.emptyCard}>
              <Ionicons name="checkmark-circle" size={48} color={Colors.success} />
              <Text style={styles.emptyTitle}>All Clear!</Text>
              <Text style={styles.emptyText}>No pending reports to review.</Text>
            </Card>
          ) : (
            queue.map(renderReportedUser)
          )}
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
  headerTitle: {
    fontSize: Typography.h3,
    fontWeight: Typography.bold,
    color: Colors.text,
  },
  connectionStatus: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  statusText: {
    fontSize: Typography.caption,
    color: Colors.textSecondary,
  },
  notificationBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.accent + '20',
    paddingVertical: Spacing.sm,
    paddingHorizontal: Spacing.md,
    gap: Spacing.sm,
  },
  notificationText: {
    flex: 1,
    fontSize: Typography.bodySmall,
    color: Colors.text,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: Spacing.md,
  },
  loadingText: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
  },
  statsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: Spacing.screenPadding,
    gap: Spacing.sm,
  },
  statCard: {
    flex: 1,
    minWidth: '45%',
    backgroundColor: Colors.cardBackground,
    borderRadius: 12,
    padding: Spacing.md,
    borderLeftWidth: 4,
    alignItems: 'center',
    gap: 4,
  },
  statValue: {
    fontSize: Typography.h2,
    fontWeight: Typography.bold,
    color: Colors.text,
  },
  statLabel: {
    fontSize: Typography.caption,
    color: Colors.textSecondary,
  },
  queueSection: {
    padding: Spacing.screenPadding,
  },
  sectionTitle: {
    fontSize: Typography.h4,
    fontWeight: Typography.semibold,
    color: Colors.text,
    marginBottom: Spacing.md,
  },
  userCard: {
    marginBottom: Spacing.md,
  },
  userHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  userInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    gap: Spacing.sm,
  },
  priorityBadge: {
    paddingHorizontal: Spacing.sm,
    paddingVertical: 4,
    borderRadius: 6,
  },
  priorityText: {
    fontSize: 10,
    fontWeight: Typography.bold,
  },
  userDetails: {
    flex: 1,
  },
  userName: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold,
    color: Colors.text,
  },
  userEmail: {
    fontSize: Typography.caption,
    color: Colors.textSecondary,
  },
  userStats: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
  },
  reportCountBadge: {
    backgroundColor: Colors.error + '20',
    paddingHorizontal: Spacing.sm,
    paddingVertical: 4,
    borderRadius: 8,
    alignItems: 'center',
  },
  reportCount: {
    fontSize: Typography.h4,
    fontWeight: Typography.bold,
    color: Colors.error,
  },
  reportCountLabel: {
    fontSize: 10,
    color: Colors.error,
  },
  expandedContent: {
    marginTop: Spacing.md,
    paddingTop: Spacing.md,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  reasonsContainer: {
    marginBottom: Spacing.md,
  },
  reasonsLabel: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    marginBottom: Spacing.xs,
  },
  reasonsTags: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.xs,
  },
  reasonTag: {
    backgroundColor: Colors.warning + '20',
    paddingHorizontal: Spacing.sm,
    paddingVertical: 4,
    borderRadius: 12,
  },
  reasonTagText: {
    fontSize: Typography.caption,
    color: Colors.warning,
  },
  reportsSection: {
    marginBottom: Spacing.md,
  },
  reportsSectionTitle: {
    fontSize: Typography.bodySmall,
    fontWeight: Typography.semibold,
    color: Colors.text,
    marginBottom: Spacing.sm,
  },
  reportItem: {
    backgroundColor: Colors.backgroundSecondary,
    padding: Spacing.sm,
    borderRadius: 8,
    marginBottom: Spacing.xs,
  },
  reportHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  reporterName: {
    fontSize: Typography.caption,
    fontWeight: Typography.medium,
    color: Colors.text,
  },
  reportTime: {
    fontSize: Typography.caption,
    color: Colors.textLight,
  },
  reportReason: {
    fontSize: Typography.caption,
    color: Colors.accent,
    marginBottom: 2,
  },
  reportDetails: {
    fontSize: Typography.caption,
    color: Colors.textSecondary,
    fontStyle: 'italic',
  },
  statusSection: {
    marginBottom: Spacing.md,
  },
  statusLabel: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
  },
  statusValue: {
    color: Colors.accent,
    fontWeight: Typography.semibold,
  },
  warningsText: {
    fontSize: Typography.caption,
    color: Colors.warning,
    marginTop: 4,
  },
  actionButtons: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.sm,
  },
  actionBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: Spacing.sm,
    paddingHorizontal: Spacing.md,
    borderRadius: 8,
    gap: 6,
    minWidth: 80,
    justifyContent: 'center',
  },
  dismissBtn: {
    backgroundColor: Colors.backgroundSecondary,
  },
  warnBtn: {
    backgroundColor: '#FF9500' + '20',
  },
  suspendBtn: {
    backgroundColor: '#FF6B6B' + '20',
  },
  banBtn: {
    backgroundColor: '#FF3B30' + '20',
  },
  actionBtnText: {
    fontSize: Typography.caption,
    fontWeight: Typography.semibold,
    color: Colors.text,
  },
  emptyCard: {
    alignItems: 'center',
    padding: Spacing.xl,
    gap: Spacing.md,
  },
  emptyTitle: {
    fontSize: Typography.h4,
    fontWeight: Typography.semibold,
    color: Colors.success,
  },
  emptyText: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
  },
});
