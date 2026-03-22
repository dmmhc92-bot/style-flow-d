import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TextInput,
  TouchableOpacity,
  RefreshControl,
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

export default function DiscoverScreen() {
  const router = useRouter();
  const [users, setUsers] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  
  useEffect(() => {
    loadUsers();
  }, []);
  
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchQuery.length > 0) {
        searchUsers();
      } else {
        loadUsers();
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);
  
  const loadUsers = async () => {
    setLoading(true);
    try {
      const response = await api.get('/users/discover');
      setUsers(response.data);
    } catch (error) {
      console.error('Failed to load users:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const searchUsers = async () => {
    setLoading(true);
    try {
      const response = await api.get(`/users/discover?search=${encodeURIComponent(searchQuery)}`);
      setUsers(response.data);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const onRefresh = async () => {
    setRefreshing(true);
    await loadUsers();
    setRefreshing(false);
  };
  
  const renderUser = ({ item }: any) => (
    <Card
      style={styles.userCard}
      onPress={() => router.push(`/discover/${item.id}`)}
    >
      <View style={styles.userContent}>
        <View style={styles.userAvatar}>
          {item.profile_photo ? (
            <View style={styles.avatarWithPhoto}>
              <Ionicons name="person" size={32} color={Colors.accent} />
            </View>
          ) : (
            <Ionicons name="person-outline" size={32} color={Colors.textSecondary} />
          )}
        </View>
        
        <View style={styles.userInfo}>
          <Text style={styles.userName}>{item.full_name}</Text>
          {item.business_name && (
            <Text style={styles.businessName}>{item.business_name}</Text>
          )}
          {item.city && (
            <Text style={styles.city}>{item.city}</Text>
          )}
          {item.specialties && (
            <Text style={styles.specialties} numberOfLines={1}>{item.specialties}</Text>
          )}
        </View>
        
        <Ionicons name="chevron-forward" size={20} color={Colors.textSecondary} />
      </View>
    </Card>
  );
  
  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <Text style={styles.title}>Discover</Text>
      </View>
      
      <View style={styles.searchContainer}>
        <Ionicons name="search" size={20} color={Colors.textSecondary} />
        <TextInput
          style={styles.searchInput}
          placeholder="Search by name, city, or specialty..."
          placeholderTextColor={Colors.textLight}
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
        {searchQuery.length > 0 && (
          <TouchableOpacity onPress={() => setSearchQuery('')}>
            <Ionicons name="close-circle" size={20} color={Colors.textSecondary} />
          </TouchableOpacity>
        )}
      </View>
      
      <FlatList
        data={users}
        renderItem={renderUser}
        keyExtractor={(item: any) => item.id}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={Colors.accent} />
        }
        ListEmptyComponent={
          loading ? null : (
            <EmptyState
              icon="people-outline"
              title="No Stylists Found"
              description="Try searching by name, city, or specialty to discover talented stylists"
              actionLabel="Clear Search"
              onAction={() => setSearchQuery('')}
            />
          )
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
    paddingHorizontal: Spacing.screenPadding,
    paddingVertical: Spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  title: {
    fontSize: Typography.h2,
    fontWeight: Typography.bold,
    color: Colors.text,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.backgroundCard,
    borderRadius: Spacing.radiusMedium,
    marginHorizontal: Spacing.screenPadding,
    marginVertical: Spacing.md,
    paddingHorizontal: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  searchInput: {
    flex: 1,
    paddingVertical: Spacing.md,
    paddingHorizontal: Spacing.sm,
    fontSize: Typography.body,
    color: Colors.text,
  },
  list: {
    padding: Spacing.screenPadding,
  },
  userCard: {
    marginBottom: Spacing.md,
  },
  userContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  userAvatar: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: Colors.accent + '20',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: Spacing.md,
    borderWidth: 2,
    borderColor: Colors.accent + '40',
  },
  avatarWithPhoto: {
    width: '100%',
    height: '100%',
    alignItems: 'center',
    justifyContent: 'center',
  },
  userInfo: {
    flex: 1,
  },
  userName: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold,
    color: Colors.text,
    marginBottom: 2,
  },
  businessName: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    marginBottom: 2,
  },
  city: {
    fontSize: Typography.caption,
    color: Colors.textLight,
    marginBottom: 2,
  },
  specialties: {
    fontSize: Typography.caption,
    color: Colors.accent,
    marginTop: 2,
  },
});