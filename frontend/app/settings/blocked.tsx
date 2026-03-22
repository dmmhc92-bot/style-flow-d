import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { Card } from '../../components/Card';
import { EmptyState } from '../../components/EmptyState';
import Colors from '../../constants/Colors';
import Spacing from '../../constants/Spacing';
import Typography from '../../constants/Typography';
import api from '../../utils/api';

interface BlockedUser {
  id: string;
  full_name: string;
  business_name?: string;
  profile_photo?: string;
  blocked_at: string;
}

export default function BlockedUsersScreen() {
  const router = useRouter();
  const [blockedUsers, setBlockedUsers] = useState<BlockedUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [unblocking, setUnblocking] = useState<string | null>(null);

  useEffect(() => {
    loadBlockedUsers();
  }, []);

  const loadBlockedUsers = async () => {
    setLoading(true);
    try {
      const response = await api.get('/blocked');
      setBlockedUsers(response.data);
    } catch (error) {
      console.error('Failed to load blocked users:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUnblock = (user: BlockedUser) => {
    Alert.alert(
      'Unblock User',
      `Are you sure you want to unblock ${user.full_name}? They will be able to see your profile and interact with you again.`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Unblock',
          onPress: async () => {
            setUnblocking(user.id);
            try {
              await api.delete(`/block/${user.id}`);
              setBlockedUsers(blockedUsers.filter((u) => u.id !== user.id));
              Alert.alert('Unblocked', `${user.full_name} has been unblocked.`);
            } catch (error: any) {
              Alert.alert('Error', error.response?.data?.detail || 'Failed to unblock user');
            } finally {
              setUnblocking(null);
            }
          },
        },
      ]
    );
  };

  const renderBlockedUser = ({ item }: { item: BlockedUser }) => (
    <Card style={styles.userCard}>
      <View style={styles.userInfo}>
        <View style={styles.avatar}>
          <Ionicons name="person" size={24} color={Colors.textSecondary} />
        </View>
        <View style={styles.userDetails}>
          <Text style={styles.userName}>{item.full_name}</Text>
          {item.business_name && (
            <Text style={styles.userBusiness}>{item.business_name}</Text>
          )}
          <Text style={styles.blockedDate}>
            Blocked {new Date(item.blocked_at).toLocaleDateString()}
          </Text>
        </View>
      </View>
      <TouchableOpacity
        style={styles.unblockButton}
        onPress={() => handleUnblock(item)}
        disabled={unblocking === item.id}
      >
        {unblocking === item.id ? (
          <ActivityIndicator size="small" color={Colors.accent} />
        ) : (
          <Text style={styles.unblockText}>Unblock</Text>
        )}
      </TouchableOpacity>
    </Card>
  );

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color={Colors.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Blocked Users</Text>
        <View style={{ width: 40 }} />
      </View>

      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={Colors.accent} />
        </View>
      ) : blockedUsers.length === 0 ? (
        <EmptyState
          icon="shield-checkmark-outline"
          title="No Blocked Users"
          description="You haven't blocked anyone. Block users who violate community guidelines or make you uncomfortable."
        />
      ) : (
        <>
          <View style={styles.infoSection}>
            <Ionicons name="information-circle" size={20} color={Colors.info} />
            <Text style={styles.infoText}>
              Blocked users cannot see your profile, send you messages, or interact with your content.
            </Text>
          </View>
          <FlatList
            data={blockedUsers}
            keyExtractor={(item) => item.id}
            renderItem={renderBlockedUser}
            contentContainerStyle={styles.list}
            ItemSeparatorComponent={() => <View style={styles.separator} />}
          />
        </>
      )}
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
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  infoSection: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    padding: Spacing.screenPadding,
    backgroundColor: Colors.info + '10',
    gap: Spacing.sm,
    marginBottom: Spacing.md,
  },
  infoText: {
    flex: 1,
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    lineHeight: 20,
  },
  list: {
    padding: Spacing.screenPadding,
  },
  separator: {
    height: Spacing.md,
  },
  userCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  userInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  avatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: Colors.backgroundSecondary,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: Spacing.md,
  },
  userDetails: {
    flex: 1,
  },
  userName: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold,
    color: Colors.text,
  },
  userBusiness: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  blockedDate: {
    fontSize: Typography.caption,
    color: Colors.textLight,
    marginTop: 2,
  },
  unblockButton: {
    paddingVertical: Spacing.sm,
    paddingHorizontal: Spacing.md,
    backgroundColor: Colors.accent + '20',
    borderRadius: 8,
    minWidth: 80,
    alignItems: 'center',
  },
  unblockText: {
    fontSize: Typography.bodySmall,
    fontWeight: Typography.semibold,
    color: Colors.accent,
  },
});
