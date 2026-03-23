import React from 'react';
import { View, Text, StyleSheet, Animated } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useNetwork } from '../contexts/NetworkContext';
import Colors from '../constants/Colors';
import Spacing from '../constants/Spacing';
import Typography from '../constants/Typography';

export const SyncIndicator: React.FC = () => {
  const { isOnline, isSyncing, pendingChanges } = useNetwork();
  const spinValue = React.useRef(new Animated.Value(0)).current;

  // Rotate animation for syncing
  React.useEffect(() => {
    if (isSyncing) {
      Animated.loop(
        Animated.timing(spinValue, {
          toValue: 1,
          duration: 1000,
          useNativeDriver: true,
        })
      ).start();
    } else {
      spinValue.setValue(0);
    }
  }, [isSyncing, spinValue]);

  const spin = spinValue.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });

  // Don't show anything if online and no pending changes and not syncing
  if (isOnline && pendingChanges === 0 && !isSyncing) {
    return null;
  }

  return (
    <View style={styles.container}>
      {!isOnline ? (
        // Offline indicator
        <View style={[styles.badge, styles.offlineBadge]}>
          <Ionicons name="cloud-offline" size={14} color={Colors.textInverse} />
          <Text style={styles.badgeText}>Offline</Text>
        </View>
      ) : isSyncing ? (
        // Syncing indicator
        <View style={[styles.badge, styles.syncingBadge]}>
          <Animated.View style={{ transform: [{ rotate: spin }] }}>
            <Ionicons name="sync" size={14} color={Colors.textInverse} />
          </Animated.View>
          <Text style={styles.badgeText}>Syncing...</Text>
        </View>
      ) : pendingChanges > 0 ? (
        // Pending changes indicator
        <View style={[styles.badge, styles.pendingBadge]}>
          <Ionicons name="cloud-upload" size={14} color={Colors.textInverse} />
          <Text style={styles.badgeText}>{pendingChanges}</Text>
        </View>
      ) : null}
    </View>
  );
};

// Compact version for header
export const SyncIndicatorCompact: React.FC = () => {
  const { isOnline, isSyncing, pendingChanges } = useNetwork();
  const spinValue = React.useRef(new Animated.Value(0)).current;

  React.useEffect(() => {
    if (isSyncing) {
      Animated.loop(
        Animated.timing(spinValue, {
          toValue: 1,
          duration: 1000,
          useNativeDriver: true,
        })
      ).start();
    } else {
      spinValue.setValue(0);
    }
  }, [isSyncing, spinValue]);

  const spin = spinValue.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });

  if (isOnline && pendingChanges === 0 && !isSyncing) {
    return null;
  }

  return (
    <View style={styles.compactContainer}>
      {!isOnline ? (
        <Ionicons name="cloud-offline" size={18} color={Colors.warning} />
      ) : isSyncing ? (
        <Animated.View style={{ transform: [{ rotate: spin }] }}>
          <Ionicons name="sync" size={18} color={Colors.info} />
        </Animated.View>
      ) : pendingChanges > 0 ? (
        <View style={styles.compactBadge}>
          <Ionicons name="cloud-upload" size={16} color={Colors.accent} />
          <View style={styles.countBadge}>
            <Text style={styles.countText}>{pendingChanges}</Text>
          </View>
        </View>
      ) : null}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: Spacing.md,
    right: Spacing.md,
    zIndex: 1000,
  },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: Spacing.sm,
    paddingVertical: Spacing.xs,
    borderRadius: 12,
    gap: 4,
  },
  offlineBadge: {
    backgroundColor: Colors.warning,
  },
  syncingBadge: {
    backgroundColor: Colors.info,
  },
  pendingBadge: {
    backgroundColor: Colors.accent,
  },
  badgeText: {
    fontSize: Typography.caption,
    fontWeight: Typography.semibold,
    color: Colors.textInverse,
  },
  compactContainer: {
    marginRight: Spacing.sm,
  },
  compactBadge: {
    position: 'relative',
  },
  countBadge: {
    position: 'absolute',
    top: -4,
    right: -6,
    backgroundColor: Colors.error,
    borderRadius: 8,
    minWidth: 14,
    height: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  countText: {
    fontSize: 9,
    fontWeight: Typography.bold,
    color: Colors.textInverse,
  },
});
