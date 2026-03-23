import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  Alert,
  RefreshControl,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { useFocusEffect } from '@react-navigation/native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { Image } from 'expo-image';
import { Card } from '../../../components/Card';
import Button from '../../../components/Button';
import Colors from '../../../constants/Colors';
import Spacing from '../../../constants/Spacing';
import Typography from '../../../constants/Typography';
import api from '../../../utils/api';
import LoadingSpinner from '../../../components/LoadingSpinner';
import { format } from 'date-fns';

interface TimelineEvent {
  id: string;
  type: 'appointment' | 'formula' | 'photo';
  date: string;
  service?: string;
  status?: string;
  notes?: string;
  duration_minutes?: number;
  formula_name?: string;
  formula_details?: string;
  before_photo?: string;
  after_photo?: string;
}

interface LastFormula {
  id: string;
  formula_name: string;
  formula_details: string;
  date_created: string;
}

export default function ClientTimelineScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams<{ id: string }>();
  
  const [client, setClient] = useState<any>(null);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [lastFormula, setLastFormula] = useState<LastFormula | null>(null);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  
  const loadTimeline = useCallback(async () => {
    try {
      const response = await api.get(`/clients/${id}/timeline`);
      setClient(response.data.client);
      setTimeline(response.data.timeline);
      setLastFormula(response.data.last_formula);
      setStats(response.data.stats);
    } catch (error) {
      console.error('Failed to load timeline:', error);
      Alert.alert('Error', 'Failed to load client timeline');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [id]);
  
  useFocusEffect(
    useCallback(() => {
      loadTimeline();
    }, [loadTimeline])
  );
  
  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadTimeline();
  }, [loadTimeline]);
  
  const handleRepeatLastFormula = () => {
    if (!lastFormula) {
      Alert.alert('No Formula', 'This client has no previous formula to repeat.');
      return;
    }
    
    // Navigate to formula screen with pre-filled data
    router.push({
      pathname: `/client/${id}/formula`,
      params: {
        prefill: 'true',
        formula_name: lastFormula.formula_name,
        formula_details: lastFormula.formula_details,
      },
    });
  };
  
  const getRebookStatusBadge = () => {
    if (!client?.rebook_status) return null;
    
    const statusConfig: Record<string, { color: string; icon: string; label: string }> = {
      overdue: { color: Colors.error, icon: 'alert-circle', label: 'Overdue' },
      due_soon: { color: Colors.warning, icon: 'time', label: 'Due Soon' },
      on_track: { color: Colors.success, icon: 'checkmark-circle', label: 'On Track' },
      new: { color: Colors.info, icon: 'person-add', label: 'New Client' },
    };
    
    const config = statusConfig[client.rebook_status] || statusConfig.new;
    
    return (
      <View style={[styles.rebookBadge, { backgroundColor: config.color + '20' }]}>
        <Ionicons name={config.icon as any} size={14} color={config.color} />
        <Text style={[styles.rebookBadgeText, { color: config.color }]}>{config.label}</Text>
      </View>
    );
  };
  
  const renderTimelineItem = ({ item }: { item: TimelineEvent }) => {
    const getIcon = () => {
      switch (item.type) {
        case 'appointment':
          return 'calendar';
        case 'formula':
          return 'flask';
        case 'photo':
          return 'camera';
        default:
          return 'time';
      }
    };
    
    const getColor = () => {
      switch (item.type) {
        case 'appointment':
          return Colors.info;
        case 'formula':
          return Colors.accent;
        case 'photo':
          return Colors.vip;
        default:
          return Colors.textSecondary;
      }
    };
    
    return (
      <View style={styles.timelineItem}>
        <View style={styles.timelineIndicator}>
          <View style={[styles.timelineDot, { backgroundColor: getColor() }]}>
            <Ionicons name={getIcon() as any} size={14} color={Colors.textInverse} />
          </View>
          <View style={styles.timelineLine} />
        </View>
        
        <Card style={styles.timelineCard}>
          <View style={styles.timelineHeader}>
            <Text style={styles.timelineDate}>
              {format(new Date(item.date), 'MMM d, yyyy')}
            </Text>
            <Text style={styles.timelineType}>{item.type}</Text>
          </View>
          
          {item.type === 'appointment' && (
            <>
              <Text style={styles.timelineTitle}>{item.service}</Text>
              <View style={styles.timelineMeta}>
                <Text style={styles.timelineMetaText}>
                  {item.duration_minutes} min • {item.status}
                </Text>
              </View>
              {item.notes && (
                <Text style={styles.timelineNotes}>{item.notes}</Text>
              )}
            </>
          )}
          
          {item.type === 'formula' && (
            <>
              <Text style={styles.timelineTitle}>{item.formula_name}</Text>
              <Text style={styles.timelineDetails}>{item.formula_details}</Text>
            </>
          )}
          
          {item.type === 'photo' && (
            <View style={styles.photoRow}>
              {item.before_photo && (
                <View style={styles.photoContainer}>
                  <Text style={styles.photoLabel}>Before</Text>
                  <Image source={{ uri: item.before_photo }} style={styles.photo} />
                </View>
              )}
              {item.after_photo && (
                <View style={styles.photoContainer}>
                  <Text style={styles.photoLabel}>After</Text>
                  <Image source={{ uri: item.after_photo }} style={styles.photo} />
                </View>
              )}
              {item.notes && (
                <Text style={styles.timelineNotes}>{item.notes}</Text>
              )}
            </View>
          )}
        </Card>
      </View>
    );
  };
  
  if (loading) {
    return <LoadingSpinner />;
  }
  
  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color={Colors.text} />
        </TouchableOpacity>
        <Text style={styles.title}>Timeline</Text>
        <View style={{ width: 24 }} />
      </View>
      
      <FlatList
        data={timeline}
        renderItem={renderTimelineItem}
        keyExtractor={(item) => `${item.type}-${item.id}`}
        contentContainerStyle={styles.listContent}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={Colors.accent} />
        }
        ListHeaderComponent={
          <View style={styles.clientHeader}>
            {/* Client Info */}
            <Card style={styles.clientCard}>
              <View style={styles.clientInfo}>
                <View style={styles.clientAvatar}>
                  {client?.photo ? (
                    <Image source={{ uri: client.photo }} style={styles.avatar} />
                  ) : (
                    <View style={styles.avatarPlaceholder}>
                      <Ionicons name="person" size={32} color={Colors.textSecondary} />
                    </View>
                  )}
                </View>
                <View style={styles.clientDetails}>
                  <View style={styles.clientNameRow}>
                    <Text style={styles.clientName}>{client?.name}</Text>
                    {client?.is_vip && (
                      <Ionicons name="star" size={16} color={Colors.vip} />
                    )}
                  </View>
                  {getRebookStatusBadge()}
                  {client?.next_visit_due && (
                    <Text style={styles.nextVisit}>
                      Next visit: {format(new Date(client.next_visit_due), 'MMM d, yyyy')}
                    </Text>
                  )}
                </View>
              </View>
              
              {/* Stats Row */}
              <View style={styles.statsRow}>
                <View style={styles.statItem}>
                  <Text style={styles.statValue}>{stats?.total_visits || 0}</Text>
                  <Text style={styles.statLabel}>Visits</Text>
                </View>
                <View style={styles.statDivider} />
                <View style={styles.statItem}>
                  <Text style={styles.statValue}>{stats?.total_formulas || 0}</Text>
                  <Text style={styles.statLabel}>Formulas</Text>
                </View>
                <View style={styles.statDivider} />
                <View style={styles.statItem}>
                  <Text style={styles.statValue}>{stats?.total_photos || 0}</Text>
                  <Text style={styles.statLabel}>Photos</Text>
                </View>
              </View>
            </Card>
            
            {/* Quick Actions */}
            <View style={styles.quickActions}>
              <Button
                title="Repeat Last Formula"
                onPress={handleRepeatLastFormula}
                style={styles.repeatButton}
                icon={<Ionicons name="refresh" size={18} color={Colors.buttonText} style={{ marginRight: 8 }} />}
                disabled={!lastFormula}
              />
              
              <TouchableOpacity
                style={styles.addButton}
                onPress={() => router.push(`/appointment/add?client_id=${id}`)}
              >
                <Ionicons name="calendar-outline" size={20} color={Colors.accent} />
                <Text style={styles.addButtonText}>Book</Text>
              </TouchableOpacity>
              
              <TouchableOpacity
                style={styles.addButton}
                onPress={() => router.push(`/client/${id}/formula`)}
              >
                <Ionicons name="flask-outline" size={20} color={Colors.accent} />
                <Text style={styles.addButtonText}>Formula</Text>
              </TouchableOpacity>
            </View>
            
            {/* Last Formula Preview */}
            {lastFormula && (
              <Card style={styles.lastFormulaCard}>
                <View style={styles.lastFormulaHeader}>
                  <Ionicons name="flask" size={18} color={Colors.accent} />
                  <Text style={styles.lastFormulaTitle}>Last Formula</Text>
                  <Text style={styles.lastFormulaDate}>
                    {format(new Date(lastFormula.date_created), 'MMM d, yyyy')}
                  </Text>
                </View>
                <Text style={styles.lastFormulaName}>{lastFormula.formula_name}</Text>
                <Text style={styles.lastFormulaDetails} numberOfLines={2}>
                  {lastFormula.formula_details}
                </Text>
              </Card>
            )}
            
            <Text style={styles.sectionTitle}>Activity History</Text>
          </View>
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Ionicons name="time-outline" size={48} color={Colors.textLight} />
            <Text style={styles.emptyText}>No activity yet</Text>
            <Text style={styles.emptySubtext}>
              Appointments, formulas, and photos will appear here
            </Text>
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
    alignItems: 'center',
    paddingHorizontal: Spacing.screenPadding,
    paddingVertical: Spacing.md,
  },
  backButton: {
    marginRight: Spacing.md,
  },
  title: {
    flex: 1,
    fontSize: Typography.h3,
    fontWeight: Typography.bold,
    color: Colors.text,
  },
  listContent: {
    padding: Spacing.screenPadding,
  },
  clientHeader: {
    marginBottom: Spacing.md,
  },
  clientCard: {
    marginBottom: Spacing.md,
  },
  clientInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: Spacing.md,
  },
  clientAvatar: {
    marginRight: Spacing.md,
  },
  avatar: {
    width: 64,
    height: 64,
    borderRadius: 32,
  },
  avatarPlaceholder: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: Colors.backgroundSecondary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  clientDetails: {
    flex: 1,
  },
  clientNameRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: Spacing.xs,
  },
  clientName: {
    fontSize: Typography.h4,
    fontWeight: Typography.bold,
    color: Colors.text,
    marginRight: Spacing.xs,
  },
  rebookBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    paddingHorizontal: Spacing.sm,
    paddingVertical: 2,
    borderRadius: 12,
    marginBottom: Spacing.xs,
  },
  rebookBadgeText: {
    fontSize: Typography.caption,
    fontWeight: Typography.medium,
    marginLeft: 4,
  },
  nextVisit: {
    fontSize: Typography.caption,
    color: Colors.textSecondary,
  },
  statsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingTop: Spacing.md,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statDivider: {
    width: 1,
    height: 32,
    backgroundColor: Colors.border,
  },
  statValue: {
    fontSize: Typography.h3,
    fontWeight: Typography.bold,
    color: Colors.text,
  },
  statLabel: {
    fontSize: Typography.caption,
    color: Colors.textSecondary,
  },
  quickActions: {
    flexDirection: 'row',
    marginBottom: Spacing.md,
    gap: Spacing.sm,
  },
  repeatButton: {
    flex: 1,
  },
  addButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.cardBackground,
    paddingVertical: Spacing.sm,
    paddingHorizontal: Spacing.md,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: Colors.accent + '30',
  },
  addButtonText: {
    fontSize: Typography.bodySmall,
    color: Colors.accent,
    marginLeft: Spacing.xs,
  },
  lastFormulaCard: {
    marginBottom: Spacing.md,
    backgroundColor: Colors.accent + '10',
    borderWidth: 1,
    borderColor: Colors.accent + '30',
  },
  lastFormulaHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: Spacing.sm,
  },
  lastFormulaTitle: {
    fontSize: Typography.bodySmall,
    fontWeight: Typography.semibold,
    color: Colors.accent,
    marginLeft: Spacing.xs,
    flex: 1,
  },
  lastFormulaDate: {
    fontSize: Typography.caption,
    color: Colors.textSecondary,
  },
  lastFormulaName: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold,
    color: Colors.text,
    marginBottom: Spacing.xs,
  },
  lastFormulaDetails: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
  },
  sectionTitle: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold,
    color: Colors.text,
    marginBottom: Spacing.md,
  },
  timelineItem: {
    flexDirection: 'row',
    marginBottom: Spacing.md,
  },
  timelineIndicator: {
    alignItems: 'center',
    marginRight: Spacing.md,
  },
  timelineDot: {
    width: 28,
    height: 28,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  timelineLine: {
    width: 2,
    flex: 1,
    backgroundColor: Colors.border,
    marginTop: Spacing.xs,
  },
  timelineCard: {
    flex: 1,
  },
  timelineHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.xs,
  },
  timelineDate: {
    fontSize: Typography.caption,
    color: Colors.textSecondary,
  },
  timelineType: {
    fontSize: Typography.caption,
    color: Colors.textLight,
    textTransform: 'capitalize',
  },
  timelineTitle: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold,
    color: Colors.text,
    marginBottom: Spacing.xs,
  },
  timelineMeta: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  timelineMetaText: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    textTransform: 'capitalize',
  },
  timelineNotes: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    marginTop: Spacing.xs,
    fontStyle: 'italic',
  },
  timelineDetails: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
  },
  photoRow: {
    marginTop: Spacing.xs,
  },
  photoContainer: {
    marginBottom: Spacing.sm,
  },
  photoLabel: {
    fontSize: Typography.caption,
    color: Colors.textSecondary,
    marginBottom: Spacing.xs,
  },
  photo: {
    width: '100%',
    height: 120,
    borderRadius: 8,
  },
  emptyContainer: {
    alignItems: 'center',
    paddingVertical: Spacing.xxl,
  },
  emptyText: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold,
    color: Colors.textSecondary,
    marginTop: Spacing.md,
  },
  emptySubtext: {
    fontSize: Typography.bodySmall,
    color: Colors.textLight,
    marginTop: Spacing.xs,
    textAlign: 'center',
  },
});
