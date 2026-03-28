import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TextInput,
  TouchableOpacity,
  RefreshControl,
  Image,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { Card } from '../../components/Card';
import { VerifiedBadgeInline, FeaturedBadge } from '../../components/CredentialBadge';
import EmptyState from '../../components/EmptyState';
import Colors from '../../constants/Colors';
import Spacing from '../../constants/Spacing';
import Typography from '../../constants/Typography';
import api from '../../utils/api';

type FilterType = 'all' | 'featured' | 'nearby';

export default function DiscoverScreen() {
  const router = useRouter();
  const [users, setUsers] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeFilter, setActiveFilter] = useState<FilterType>('all');
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  
  useEffect(() => {
    loadUsers();
  }, [activeFilter]);
  
  useEffect(() => {
    const timer = setTimeout(() => {
      loadUsers();
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);
  
  const loadUsers = async () => {
    setLoading(true);
    try {
      // Build query params
      const params = new URLSearchParams();
      
      if (searchQuery) {
        // Check if search looks like a city, name, or specialty
        params.append('name', searchQuery);
        params.append('city', searchQuery);
        params.append('specialty', searchQuery);
      }
      
      if (activeFilter === 'featured') {
        params.append('featured', 'true');
      }
      
      // Use the enhanced profiles discover endpoint
      const response = await api.get(`/profiles/discover?${params.toString()}`);
      setUsers(response.data);
    } catch (error) {
      // Fallback to original endpoint
      try {
        const fallbackResponse = await api.get(`/users/discover?search=${encodeURIComponent(searchQuery)}`);
        setUsers(fallbackResponse.data);
      } catch (fallbackError) {
        console.error('Failed to load users:', fallbackError);
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };
  
  const onRefresh = useCallback(() => {
    setRefreshing(true);
    loadUsers();
  }, [searchQuery, activeFilter]);
  
  const renderUser = ({ item }: { item: any }) => (
    <Card
      style={styles.userCard}
      onPress={() => router.push(`/hub/${item.id}`)}
    >
      <View style={styles.userContent}>
        {/* Avatar */}
        <View style={styles.userAvatar}>
          {item.profile_photo ? (
            <Image 
              source={{ uri: item.profile_photo }} 
              style={styles.avatarImage}
            />
          ) : (
            <View style={styles.avatarPlaceholder}>
              <Ionicons name="person" size={28} color={Colors.accent} />
            </View>
          )}
          {item.is_verified && (
            <View style={styles.verifiedBadgeOverlay}>
              <Ionicons name="checkmark-circle" size={18} color={Colors.info} />
            </View>
          )}
        </View>
        
        {/* User Info */}
        <View style={styles.userInfo}>
          <View style={styles.nameRow}>
            <Text style={styles.userName} numberOfLines={1}>{item.full_name}</Text>
            {item.is_verified && <VerifiedBadgeInline size={14} />}
          </View>
          
          {item.business_name && (
            <Text style={styles.businessName} numberOfLines={1}>{item.business_name}</Text>
          )}
          
          <View style={styles.metaRow}>
            {item.city && (
              <View style={styles.metaItem}>
                <Ionicons name="location-outline" size={12} color={Colors.textSecondary} />
                <Text style={styles.metaText}>{item.city}</Text>
              </View>
            )}
            {item.followers_count > 0 && (
              <View style={styles.metaItem}>
                <Ionicons name="people-outline" size={12} color={Colors.textSecondary} />
                <Text style={styles.metaText}>{item.followers_count}</Text>
              </View>
            )}
            {item.portfolio_count > 0 && (
              <View style={styles.metaItem}>
                <Ionicons name="images-outline" size={12} color={Colors.textSecondary} />
                <Text style={styles.metaText}>{item.portfolio_count}</Text>
              </View>
            )}
          </View>
          
          {item.specialties && (
            <Text style={styles.specialties} numberOfLines={1}>{item.specialties}</Text>
          )}
        </View>
        
        {/* Featured Badge or Arrow */}
        {item.is_featured ? (
          <FeaturedBadge size="small" />
        ) : (
          <Ionicons name="chevron-forward" size={20} color={Colors.textSecondary} />
        )}
      </View>
    </Card>
  );
  
  const renderHeader = () => (
    <View style={styles.filtersContainer}>
      <TouchableOpacity 
        style={[styles.filterChip, activeFilter === 'all' && styles.filterChipActive]}
        onPress={() => setActiveFilter('all')}
      >
        <Text style={[styles.filterText, activeFilter === 'all' && styles.filterTextActive]}>
          All
        </Text>
      </TouchableOpacity>
      <TouchableOpacity 
        style={[styles.filterChip, activeFilter === 'featured' && styles.filterChipActive]}
        onPress={() => setActiveFilter('featured')}
      >
        <Ionicons 
          name="star" 
          size={14} 
          color={activeFilter === 'featured' ? Colors.background : Colors.vip} 
        />
        <Text style={[styles.filterText, activeFilter === 'featured' && styles.filterTextActive]}>
          Featured
        </Text>
      </TouchableOpacity>
    </View>
  );
  
  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <Text style={styles.title}>Stylist Hub</Text>
        <Text style={styles.subtitle}>Discover talented professionals</Text>
      </View>
      
      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <Ionicons name="search" size={20} color={Colors.textSecondary} />
        <TextInput
          style={styles.searchInput}
          placeholder="Search by name, city, or specialty..."
          placeholderTextColor={Colors.textLight}
          value={searchQuery}
          onChangeText={setSearchQuery}
          autoCapitalize="none"
          autoCorrect={false}
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
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.list}
        ListHeaderComponent={renderHeader}
        refreshControl={
          <RefreshControl 
            refreshing={refreshing} 
            onRefresh={onRefresh} 
            tintColor={Colors.accent} 
          />
        }
        ListEmptyComponent={
          loading ? null : (
            <EmptyState
              icon="people-outline"
              title="No Stylists Found"
              description={
                searchQuery 
                  ? "Try adjusting your search or filters"
                  : "Be the first to join the community!"
              }
              actionLabel={searchQuery ? "Clear Search" : undefined}
              onAction={searchQuery ? () => setSearchQuery('') : undefined}
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
    paddingTop: Spacing.md,
    paddingBottom: Spacing.sm,
  },
  title: {
    fontSize: Typography.h2,
    fontWeight: Typography.bold as any,
    color: Colors.accent,
  },
  subtitle: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.backgroundSecondary,
    borderRadius: 12,
    marginHorizontal: Spacing.screenPadding,
    marginBottom: Spacing.md,
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
  filtersContainer: {
    flexDirection: 'row',
    gap: Spacing.sm,
    marginBottom: Spacing.md,
  },
  filterChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    borderRadius: 20,
    backgroundColor: Colors.backgroundSecondary,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  filterChipActive: {
    backgroundColor: Colors.accent,
    borderColor: Colors.accent,
  },
  filterText: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    fontWeight: Typography.medium as any,
  },
  filterTextActive: {
    color: Colors.background,
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
    position: 'relative',
    marginRight: Spacing.md,
  },
  avatarImage: {
    width: 56,
    height: 56,
    borderRadius: 28,
    borderWidth: 2,
    borderColor: Colors.accent + '60',
  },
  avatarPlaceholder: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: Colors.accent + '20',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: Colors.accent + '40',
  },
  verifiedBadgeOverlay: {
    position: 'absolute',
    bottom: -2,
    right: -2,
    backgroundColor: Colors.background,
    borderRadius: 9,
    padding: 1,
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
    marginTop: 1,
  },
  metaRow: {
    flexDirection: 'row',
    gap: Spacing.sm,
    marginTop: 4,
  },
  metaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 2,
  },
  metaText: {
    fontSize: Typography.caption,
    color: Colors.textSecondary,
  },
  specialties: {
    fontSize: Typography.caption,
    color: Colors.accent,
    marginTop: 4,
    fontWeight: Typography.medium as any,
  },
});
