import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ActivityIndicator } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import Colors from '../constants/Colors';
import Spacing from '../constants/Spacing';
import Typography from '../constants/Typography';
import { useSyncStatus } from '../utils/syncService';

interface SyncStatusBarProps {
  showAlways?: boolean;
  compact?: boolean;
}

/**
 * SyncStatusBar - Shows offline status and pending sync indicator
 * 
 * Displays:
 * - Offline banner when no connection
 * - Syncing indicator when uploading changes
 * - Pending changes count badge
 */
export const SyncStatusBar: React.FC<SyncStatusBarProps> = ({ 
  showAlways = false,
  compact = false 
}) => {
  const { 
    isOnline, 
    isSyncing, 
    pendingCount, 
    hasPendingChanges,
    forceSyncNow 
  } = useSyncStatus();
  
  // Don't show if online and no pending changes (unless showAlways)
  if (isOnline && !hasPendingChanges && !isSyncing && !showAlways) {
    return null;
  }
  
  if (compact) {
    return (
      <View style={styles.compactContainer}>
        {!isOnline && (
          <View style={styles.compactBadge}>
            <Ionicons name="cloud-offline" size={14} color={Colors.warning} />
          </View>
        )}
        {hasPendingChanges && (
          <View style={styles.pendingBadge}>
            <Text style={styles.pendingBadgeText}>{pendingCount}</Text>
          </View>
        )}
        {isSyncing && (
          <ActivityIndicator size="small" color={Colors.accent} />
        )}
      </View>
    );
  }
  
  // Offline state
  if (!isOnline) {
    return (
      <View style={styles.offlineBar}>
        <Ionicons name="cloud-offline" size={18} color={Colors.warning} />
        <Text style={styles.offlineText}>
          You're offline • Changes saved locally
        </Text>
        {hasPendingChanges && (
          <View style={styles.countBadge}>
            <Text style={styles.countText}>{pendingCount}</Text>
          </View>
        )}
      </View>
    );
  }
  
  // Syncing state
  if (isSyncing) {
    return (
      <View style={styles.syncingBar}>
        <ActivityIndicator size="small" color={Colors.accent} />
        <Text style={styles.syncingText}>
          Syncing your changes...
        </Text>
      </View>
    );
  }
  
  // Has pending changes but online (about to sync)
  if (hasPendingChanges) {
    return (
      <TouchableOpacity style={styles.pendingBar} onPress={forceSyncNow}>
        <Ionicons name="cloud-upload-outline" size={18} color={Colors.accent} />
        <Text style={styles.pendingText}>
          {pendingCount} pending • Tap to sync now
        </Text>
      </TouchableOpacity>
    );
  }
  
  return null;
};

/**
 * OfflineIndicator - Small indicator for header/toolbar
 */
export const OfflineIndicator: React.FC = () => {
  const { isOnline, hasPendingChanges } = useSyncStatus();
  
  if (isOnline && !hasPendingChanges) return null;
  
  return (
    <View style={styles.indicator}>
      {!isOnline ? (
        <Ionicons name="cloud-offline" size={16} color={Colors.warning} />
      ) : (
        <View style={styles.syncDot} />
      )}
    </View>
  );
};

/**
 * SyncStatusText - Text-only status for settings/profile
 */
export const SyncStatusText: React.FC = () => {
  const { isOnline, isSyncing, lastSyncAt, pendingCount } = useSyncStatus();
  
  let statusText = '';
  let statusColor = Colors.textSecondary;
  
  if (!isOnline) {
    statusText = 'Offline - changes saved locally';
    statusColor = Colors.warning;
  } else if (isSyncing) {
    statusText = 'Syncing...';
    statusColor = Colors.accent;
  } else if (pendingCount > 0) {
    statusText = `${pendingCount} changes pending sync`;
    statusColor = Colors.accent;
  } else if (lastSyncAt) {
    const lastSync = new Date(lastSyncAt);
    const now = new Date();
    const diffMins = Math.round((now.getTime() - lastSync.getTime()) / 60000);
    
    if (diffMins < 1) {
      statusText = 'Just synced';
    } else if (diffMins < 60) {
      statusText = `Synced ${diffMins}m ago`;
    } else {
      statusText = `Synced ${Math.round(diffMins / 60)}h ago`;
    }
    statusColor = Colors.success;
  } else {
    statusText = 'All synced';
    statusColor = Colors.success;
  }
  
  return (
    <View style={styles.statusTextContainer}>
      <View style={[styles.statusDot, { backgroundColor: statusColor }]} />
      <Text style={[styles.statusText, { color: statusColor }]}>{statusText}</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  // Full bar styles
  offlineBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.warning + '20',
    paddingVertical: Spacing.sm,
    paddingHorizontal: Spacing.md,
    gap: Spacing.sm,
  },
  offlineText: {
    fontSize: Typography.bodySmall,
    color: Colors.warning,
    fontWeight: Typography.medium as any,
  },
  syncingBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.accent + '15',
    paddingVertical: Spacing.sm,
    paddingHorizontal: Spacing.md,
    gap: Spacing.sm,
  },
  syncingText: {
    fontSize: Typography.bodySmall,
    color: Colors.accent,
    fontWeight: Typography.medium as any,
  },
  pendingBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.accent + '10',
    paddingVertical: Spacing.sm,
    paddingHorizontal: Spacing.md,
    gap: Spacing.sm,
  },
  pendingText: {
    fontSize: Typography.bodySmall,
    color: Colors.accent,
    fontWeight: Typography.medium as any,
  },
  countBadge: {
    backgroundColor: Colors.warning,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 10,
    minWidth: 20,
    alignItems: 'center',
  },
  countText: {
    fontSize: 10,
    color: Colors.background,
    fontWeight: Typography.bold as any,
  },
  
  // Compact styles
  compactContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.xs,
  },
  compactBadge: {
    padding: 4,
  },
  pendingBadge: {
    backgroundColor: Colors.accent,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 10,
    minWidth: 18,
    alignItems: 'center',
  },
  pendingBadgeText: {
    fontSize: 10,
    color: Colors.background,
    fontWeight: Typography.bold as any,
  },
  
  // Indicator styles
  indicator: {
    marginLeft: Spacing.sm,
  },
  syncDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: Colors.accent,
  },
  
  // Status text styles
  statusTextContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.xs,
  },
  statusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  statusText: {
    fontSize: Typography.caption,
  },
});

export default SyncStatusBar;
