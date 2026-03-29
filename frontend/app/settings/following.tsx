import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  Image,
  Alert,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { Card } from '../../components/Card';
import EmptyState from '../../components/EmptyState';
import Colors from '../../constants/Colors';
import Spacing from '../../constants/Spacing';
import Typography from '../../constants/Typography';
import api from '../../utils/api';

interface FollowUser {
  id: string;
  full_name: string;
  profile_photo?: string;
  business_name?: string;
  is_verified?: boolean;
}

type TabType = 'following' | 'followers';

export default function FollowingScreen() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<TabType>('following');
  const [users, setUsers] = useState<FollowUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [unfollowingId, setUnfollowingId] = useState<string | null>(null);

  useEffect(() => {
    loadUsers();
  }, [activeTab]);

  const loadUsers = async () => {
    setLoading(true);
    try {
      const endpoint = activeTab === 'following' ? '/users/following' : '/users/followers';
      const response = await api.get(endpoint);
      setUsers(response.data);
    } catch (error) {
      console.error('Failed to load users:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    loadUsers();
  }, [activeTab]);

  const handleUnfollow = (user: FollowUser) => {
    Alert.alert(
      'Unfollow',
      `Are you sure you want to unfollow ${user.full_name}?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Unfollow',
          style: 'destructive',
          onPress: async () => {
            setUnfollowingId(user.id);
            try {
              await api.delete(`/users/${user.id}/follow`);
              setUsers(prev => prev.filter(u => u.id !== user.id));
              Alert.alert('Success', `You have unfollowed ${user.full_name}`);
            } catch (error: any) {
              Alert.alert('Error', error.response?.data?.detail || 'Failed to unfollow');
            } finally {
              setUnfollowingId(null);
            }
          },
        },
      ]
    );
  };

  const handleRemoveFollower = (user: FollowUser) => {
    Alert.alert(
      'Remove Follower',
      `Remove ${user.full_name} from your followers?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Remove',
          style: 'destructive',
          onPress: async () => {
            setUnfollowingId(user.id);
            try {
              await api.delete(`/users/${user.id}/follower`);
              setUsers(prev => prev.filter(u => u.id !== user.id));
              Alert.alert('Success', `${user.full_name} has been removed from your followers`);
            } catch (error: any) {
              Alert.alert('Error', error.response?.data?.detail || 'Failed to remove follower');
            } finally {
              setUnfollowingId(null);
            }
          },
        },
      ]
    );
  };

  const renderUser = ({ item }: { item: FollowUser }) => (
    <Card style={styles.userCard}>
      <TouchableOpacity 
        style={styles.userContent}
        onPress={() => router.push(`/hub/${item.id}`)}
        activeOpacity={0.7}
      >
        <View style={styles.userAvatar}>
          {item.profile_photo ? (
            <Image source={{ uri: item.profile_photo }} style={styles.avatarImage} />
          ) : (
            <View style={styles.avatarPlaceholder}>
              <Ionicons name="person" size={24} color={Colors.accent} />
            </View>
          )}
        </View>
        
        <View style={styles.userInfo}>
          <View style={styles.nameRow}>
            <Text style={styles.userName} numberOfLines={1}>{item.full_name}</Text>
            {item.is_verified && (
              <Ionicons name="checkmark-circle" size={16} color={Colors.info} style={{ marginLeft: 4 }} />
            )}
          </View>
          {item.business_name && (
            <Text style={styles.businessName} numberOfLines={1}>{item.business_name}</Text>
          )}
        </View>
        
        <TouchableOpacity
          style={styles.actionButton}
          onPress={() => activeTab === 'following' ? handleUnfollow(item) : handleRemoveFollower(item)}
          disabled={unfollowingId === item.id}
        >
          {unfollowingId === item.id ? (
            <ActivityIndicator size="small" color={Colors.error} />
          ) : (
            <Text style={styles.actionButtonText}>
              {activeTab === 'following' ? 'Unfollow' : 'Remove'}
            </Text>
          )}
        </TouchableOpacity>
      </TouchableOpacity>
    </Card>
  );

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color={Colors.text} />
        </TouchableOpacity>
        <Text style={styles.title}>Connections</Text>
        <View style={{ width: 40 }} />
      </View>

      {/* Tabs */}
      <View style={styles.tabBar}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'following' && styles.activeTab]}
          onPress={() => setActiveTab('following')}
        >
          <Text style={[styles.tabText, activeTab === 'following' && styles.activeTabText]}>
            Following
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'followers' && styles.activeTab]}
          onPress={() => setActiveTab('followers')}
        >
          <Text style={[styles.tabText, activeTab === 'followers' && styles.activeTabText]}>
            Followers
          </Text>
        </TouchableOpacity>
      </View>

      {loading && !refreshing ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={Colors.accent} />
        </View>
      ) : (
        <FlatList
          data={users}
          keyExtractor={(item) => item.id}
          renderItem={renderUser}
          contentContainerStyle={styles.listContent}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={onRefresh}
              tintColor={Colors.accent}
            />
          }
          ListEmptyComponent={
            <EmptyState
              icon="people-outline"
              title={activeTab === 'following' ? 'Not following anyone' : 'No followers yet'}
              message={
                activeTab === 'following'
                  ? 'Discover stylists and follow them to see their work in your feed.'
                  : 'Share your profile to get more followers!'
              }
              actionLabel={activeTab === 'following' ? 'Discover Stylists' : undefined}
              onAction={activeTab === 'following' ? () => router.push('/tabs/discover') : undefined}
            />
          }
        />
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
  title: {
    fontSize: Typography.h3,
    fontWeight: Typography.semibold as any,
    color: Colors.text,
  },
  tabBar: {
    flexDirection: 'row',
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  tab: {
    flex: 1,
    paddingVertical: Spacing.md,
    alignItems: 'center',
  },
  activeTab: {
    borderBottomWidth: 2,
    borderBottomColor: Colors.accent,
  },
  tabText: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
    fontWeight: Typography.medium as any,
  },
  activeTabText: {
    color: Colors.accent,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  listContent: {
    padding: Spacing.screenPadding,
    paddingBottom: Spacing.xxl,
  },
  userCard: {
    marginBottom: Spacing.sm,
  },
  userContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  userAvatar: {
    width: 50,
    height: 50,
    borderRadius: 25,
    overflow: 'hidden',
    marginRight: Spacing.md,
  },
  avatarImage: {
    width: '100%',
    height: '100%',
  },
  avatarPlaceholder: {
    width: '100%',
    height: '100%',
    backgroundColor: Colors.backgroundSecondary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  userInfo: {
    flex: 1,
  },
  nameRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  userName: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold as any,
    color: Colors.text,
  },
  businessName: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  actionButton: {
    backgroundColor: Colors.error + '15',
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    borderRadius: 8,
    minWidth: 80,
    alignItems: 'center',
  },
  actionButtonText: {
    fontSize: Typography.bodySmall,
    fontWeight: Typography.semibold as any,
    color: Colors.error,
  },
});
