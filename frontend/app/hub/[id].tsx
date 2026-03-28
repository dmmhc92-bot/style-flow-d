import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Image,
  Dimensions,
  Alert,
  Linking,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import Button from '../../components/Button';
import { CredentialBadge, VerifiedBadgeInline } from '../../components/CredentialBadge';
import { ReportModal } from '../../components/ReportModal';
import Colors from '../../constants/Colors';
import Spacing from '../../constants/Spacing';
import Typography from '../../constants/Typography';
import api from '../../utils/api';
import { useAuthStore } from '../../store/authStore';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const GRID_GAP = 2;
const GRID_COLUMNS = 3;
const IMAGE_SIZE = (SCREEN_WIDTH - GRID_GAP * (GRID_COLUMNS - 1)) / GRID_COLUMNS;

type TabType = 'portfolio' | 'posts';

export default function StylistHubProfileScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams();
  const { user: currentUser } = useAuthStore();
  
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [following, setFollowing] = useState(false);
  const [followLoading, setFollowLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<TabType>('portfolio');
  const [showReportModal, setShowReportModal] = useState(false);
  const [showMoreOptions, setShowMoreOptions] = useState(false);
  
  const isOwnProfile = currentUser?.id === id;
  
  useEffect(() => {
    loadProfile();
  }, [id]);
  
  const loadProfile = async () => {
    try {
      const response = await api.get(`/profiles/${id}`);
      setProfile(response.data);
      setFollowing(response.data.is_following);
    } catch (error: any) {
      if (error.response?.status === 403) {
        Alert.alert('Blocked', 'You cannot view this profile.');
      } else {
        Alert.alert('Error', error.response?.data?.detail || 'Failed to load profile');
      }
      router.back();
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };
  
  const onRefresh = useCallback(() => {
    setRefreshing(true);
    loadProfile();
  }, [id]);
  
  const handleFollow = async () => {
    setFollowLoading(true);
    try {
      if (following) {
        await api.delete(`/users/${id}/follow`);
        setFollowing(false);
        setProfile((p: any) => ({ ...p, followers_count: p.followers_count - 1 }));
      } else {
        await api.post(`/users/${id}/follow`);
        setFollowing(true);
        setProfile((p: any) => ({ ...p, followers_count: p.followers_count + 1 }));
      }
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.detail || 'Action failed');
    } finally {
      setFollowLoading(false);
    }
  };
  
  const handleBlock = () => {
    Alert.alert(
      'Block User',
      `Are you sure you want to block ${profile?.full_name}?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Block',
          style: 'destructive',
          onPress: async () => {
            try {
              await api.post(`/block/${id}`);
              Alert.alert('Blocked', `${profile?.full_name} has been blocked.`);
              router.back();
            } catch (error: any) {
              Alert.alert('Error', error.response?.data?.detail || 'Failed to block user');
            }
          },
        },
      ]
    );
  };
  
  const openSocialLink = async (type: string, handle: string) => {
    let url = '';
    if (type === 'instagram') {
      url = `https://instagram.com/${handle.replace('@', '')}`;
    } else if (type === 'tiktok') {
      url = `https://tiktok.com/@${handle.replace('@', '')}`;
    } else if (type === 'website') {
      url = handle.startsWith('http') ? handle : `https://${handle}`;
    }
    
    try {
      const supported = await Linking.canOpenURL(url);
      if (supported) {
        await Linking.openURL(url);
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to open link');
    }
  };
  
  if (loading || !profile) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={Colors.accent} />
        </View>
      </SafeAreaView>
    );
  }
  
  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.headerButton} onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color={Colors.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle} numberOfLines={1}>
          {profile.full_name}
        </Text>
        {!isOwnProfile ? (
          <TouchableOpacity 
            style={styles.headerButton} 
            onPress={() => setShowMoreOptions(!showMoreOptions)}
          >
            <Ionicons name="ellipsis-horizontal" size={24} color={Colors.text} />
          </TouchableOpacity>
        ) : (
          <TouchableOpacity 
            style={styles.headerButton} 
            onPress={() => router.push('/profile/edit')}
          >
            <Ionicons name="create-outline" size={24} color={Colors.text} />
          </TouchableOpacity>
        )}
      </View>
      
      {/* More Options Dropdown */}
      {showMoreOptions && (
        <View style={styles.optionsDropdown}>
          <TouchableOpacity 
            style={styles.optionItem}
            onPress={() => {
              setShowMoreOptions(false);
              setShowReportModal(true);
            }}
          >
            <Ionicons name="flag-outline" size={20} color={Colors.warning} />
            <Text style={styles.optionText}>Report</Text>
          </TouchableOpacity>
          <View style={styles.optionDivider} />
          <TouchableOpacity 
            style={styles.optionItem}
            onPress={() => {
              setShowMoreOptions(false);
              handleBlock();
            }}
          >
            <Ionicons name="ban-outline" size={20} color={Colors.error} />
            <Text style={[styles.optionText, { color: Colors.error }]}>Block</Text>
          </TouchableOpacity>
        </View>
      )}
      
      <ScrollView
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor={Colors.accent}
          />
        }
      >
        {/* Instagram-Style Profile Header */}
        <View style={styles.profileHeader}>
          {/* Avatar + Stats Row */}
          <View style={styles.avatarStatsRow}>
            {/* Avatar */}
            <View style={styles.avatarContainer}>
              {(profile.profile_icon_url || profile.profile_photo) ? (
                <Image 
                  source={{ uri: profile.profile_icon_url || profile.profile_photo }} 
                  style={styles.avatar}
                />
              ) : (
                <View style={styles.avatarPlaceholder}>
                  <Ionicons name="person" size={40} color={Colors.accent} />
                </View>
              )}
              {profile.is_verified && (
                <View style={styles.verifiedOverlay}>
                  <Ionicons name="checkmark-circle" size={24} color={Colors.info} />
                </View>
              )}
            </View>
            
            {/* Stats */}
            <View style={styles.statsContainer}>
              <TouchableOpacity style={styles.statItem}>
                <Text style={styles.statNumber}>{profile.portfolio_count || 0}</Text>
                <Text style={styles.statLabel}>Works</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.statItem}>
                <Text style={styles.statNumber}>{profile.followers_count || 0}</Text>
                <Text style={styles.statLabel}>Followers</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.statItem}>
                <Text style={styles.statNumber}>{profile.following_count || 0}</Text>
                <Text style={styles.statLabel}>Following</Text>
              </TouchableOpacity>
            </View>
          </View>
          
          {/* Name + Credentials */}
          <View style={styles.nameSection}>
            <View style={styles.nameRow}>
              <Text style={styles.displayName}>{profile.full_name}</Text>
              {profile.is_verified && <VerifiedBadgeInline size={18} />}
            </View>
            
            {profile.business_name && (
              <Text style={styles.businessName}>{profile.business_name}</Text>
            )}
            
            {/* Credential Badge */}
            <CredentialBadge
              isVerified={profile.is_verified}
              licenseState={profile.license_state}
              certifications={profile.certifications}
              size="medium"
              showDetails
            />
          </View>
          
          {/* Bio */}
          {profile.bio && (
            <Text style={styles.bio}>{profile.bio}</Text>
          )}
          
          {/* Location + Specialties */}
          <View style={styles.infoRow}>
            {profile.city && (
              <View style={styles.infoItem}>
                <Ionicons name="location-outline" size={14} color={Colors.textSecondary} />
                <Text style={styles.infoText}>{profile.city}</Text>
              </View>
            )}
          </View>
          
          {/* Specialties Chips */}
          {profile.specialties && profile.specialties.length > 0 && (
            <View style={styles.specialtiesContainer}>
              {(Array.isArray(profile.specialties) ? profile.specialties : [profile.specialties]).map((specialty: string, index: number) => (
                <View key={index} style={styles.specialtyChip}>
                  <Ionicons name="sparkles" size={12} color={Colors.accent} />
                  <Text style={styles.specialtyChipText}>{specialty}</Text>
                </View>
              ))}
            </View>
          )}
          
          {/* Credentials display */}
          {profile.credentials && (
            <View style={styles.credentialsRow}>
              <Ionicons name="ribbon" size={14} color={Colors.vip} />
              <Text style={styles.credentialsText}>{profile.credentials}</Text>
            </View>
          )}
          
          {/* Social Links */}
          {(profile.instagram_handle || profile.tiktok_handle || profile.website_url) && (
            <View style={styles.socialLinks}>
              {profile.instagram_handle && (
                <TouchableOpacity 
                  style={styles.socialButton}
                  onPress={() => openSocialLink('instagram', profile.instagram_handle)}
                >
                  <Ionicons name="logo-instagram" size={20} color={Colors.accent} />
                </TouchableOpacity>
              )}
              {profile.tiktok_handle && (
                <TouchableOpacity 
                  style={styles.socialButton}
                  onPress={() => openSocialLink('tiktok', profile.tiktok_handle)}
                >
                  <Ionicons name="logo-tiktok" size={20} color={Colors.accent} />
                </TouchableOpacity>
              )}
              {profile.website_url && (
                <TouchableOpacity 
                  style={styles.socialButton}
                  onPress={() => openSocialLink('website', profile.website_url)}
                >
                  <Ionicons name="globe-outline" size={20} color={Colors.accent} />
                </TouchableOpacity>
              )}
            </View>
          )}
          
          {/* Action Buttons */}
          <View style={styles.actionButtons}>
            {!isOwnProfile ? (
              <>
                <Button
                  title={following ? 'Following' : 'Follow'}
                  onPress={handleFollow}
                  loading={followLoading}
                  variant={following ? 'outline' : 'primary'}
                  style={styles.followButton}
                />
                <TouchableOpacity style={styles.messageButton}>
                  <Ionicons name="chatbubble-outline" size={20} color={Colors.text} />
                </TouchableOpacity>
              </>
            ) : (
              <Button
                title="Edit Profile"
                onPress={() => router.push('/profile/edit')}
                variant="outline"
                style={styles.editButton}
              />
            )}
          </View>
        </View>
        
        {/* Tab Bar */}
        <View style={styles.tabBar}>
          <TouchableOpacity 
            style={[styles.tab, activeTab === 'portfolio' && styles.activeTab]}
            onPress={() => setActiveTab('portfolio')}
          >
            <Ionicons 
              name="grid-outline" 
              size={24} 
              color={activeTab === 'portfolio' ? Colors.accent : Colors.textSecondary} 
            />
          </TouchableOpacity>
          <TouchableOpacity 
            style={[styles.tab, activeTab === 'posts' && styles.activeTab]}
            onPress={() => setActiveTab('posts')}
          >
            <Ionicons 
              name="images-outline" 
              size={24} 
              color={activeTab === 'posts' ? Colors.accent : Colors.textSecondary} 
            />
          </TouchableOpacity>
        </View>
        
        {/* Portfolio Grid */}
        {activeTab === 'portfolio' && (
          <View style={styles.portfolioGrid}>
            {profile.portfolio && profile.portfolio.length > 0 ? (
              profile.portfolio.map((item: any, index: number) => (
                <TouchableOpacity 
                  key={item.id || index} 
                  style={styles.gridItem}
                  activeOpacity={0.8}
                >
                  <Image 
                    source={{ uri: item.image }} 
                    style={styles.gridImage}
                    resizeMode="cover"
                  />
                </TouchableOpacity>
              ))
            ) : (
              <View style={styles.emptyGrid}>
                <Ionicons name="images-outline" size={48} color={Colors.textSecondary} />
                <Text style={styles.emptyText}>No portfolio items yet</Text>
              </View>
            )}
          </View>
        )}
        
        {/* Posts Tab (Placeholder) */}
        {activeTab === 'posts' && (
          <View style={styles.emptyGrid}>
            <Ionicons name="camera-outline" size={48} color={Colors.textSecondary} />
            <Text style={styles.emptyText}>No posts yet</Text>
          </View>
        )}
      </ScrollView>
      
      {/* Report Modal */}
      <ReportModal
        visible={showReportModal}
        onClose={() => setShowReportModal(false)}
        reportedUserId={id as string}
        reportedUserName={profile?.full_name}
        contentType="profile"
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
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: Spacing.sm,
    paddingVertical: Spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  headerButton: {
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    flex: 1,
    fontSize: Typography.h3,
    fontWeight: Typography.bold as any,
    color: Colors.text,
    textAlign: 'center',
    marginHorizontal: Spacing.sm,
  },
  optionsDropdown: {
    position: 'absolute',
    top: 100,
    right: Spacing.screenPadding,
    backgroundColor: Colors.cardBackground,
    borderRadius: 12,
    padding: Spacing.sm,
    zIndex: 100,
    elevation: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    minWidth: 150,
  },
  optionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: Spacing.sm,
    paddingHorizontal: Spacing.md,
    gap: Spacing.sm,
  },
  optionText: {
    fontSize: Typography.body,
    color: Colors.text,
    fontWeight: Typography.medium as any,
  },
  optionDivider: {
    height: 1,
    backgroundColor: Colors.border,
    marginVertical: Spacing.xs,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  profileHeader: {
    padding: Spacing.screenPadding,
  },
  avatarStatsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: Spacing.md,
  },
  avatarContainer: {
    position: 'relative',
    marginRight: Spacing.lg,
  },
  avatar: {
    width: 86,
    height: 86,
    borderRadius: 43,
    borderWidth: 3,
    borderColor: Colors.accent,
  },
  avatarPlaceholder: {
    width: 86,
    height: 86,
    borderRadius: 43,
    backgroundColor: Colors.accent + '20',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 3,
    borderColor: Colors.accent + '40',
  },
  verifiedOverlay: {
    position: 'absolute',
    bottom: 0,
    right: 0,
    backgroundColor: Colors.background,
    borderRadius: 12,
    padding: 2,
  },
  statsContainer: {
    flex: 1,
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  statItem: {
    alignItems: 'center',
  },
  statNumber: {
    fontSize: Typography.h3,
    fontWeight: Typography.bold as any,
    color: Colors.text,
  },
  statLabel: {
    fontSize: Typography.caption,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  nameSection: {
    marginBottom: Spacing.sm,
  },
  nameRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  displayName: {
    fontSize: Typography.body,
    fontWeight: Typography.bold as any,
    color: Colors.text,
  },
  businessName: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  bio: {
    fontSize: Typography.body,
    color: Colors.text,
    lineHeight: 20,
    marginBottom: Spacing.sm,
  },
  infoRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.md,
    marginBottom: Spacing.sm,
  },
  infoItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  infoText: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
  },
  specialtiesContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.xs,
    marginBottom: Spacing.sm,
  },
  specialtyChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.accent + '15',
    paddingHorizontal: Spacing.sm,
    paddingVertical: 4,
    borderRadius: 12,
    gap: 4,
  },
  specialtyChipText: {
    fontSize: Typography.caption,
    color: Colors.accent,
    fontWeight: Typography.medium as any,
  },
  credentialsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: Spacing.sm,
    paddingVertical: 4,
  },
  credentialsText: {
    fontSize: Typography.bodySmall,
    color: Colors.vip,
    fontWeight: Typography.medium as any,
  },
  specialtiesText: {
    fontSize: Typography.bodySmall,
    color: Colors.accent,
    fontWeight: Typography.medium as any,
  },
  socialLinks: {
    flexDirection: 'row',
    gap: Spacing.md,
    marginBottom: Spacing.md,
  },
  socialButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: Colors.backgroundSecondary,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  actionButtons: {
    flexDirection: 'row',
    gap: Spacing.sm,
  },
  followButton: {
    flex: 1,
  },
  editButton: {
    flex: 1,
  },
  messageButton: {
    width: 44,
    height: 44,
    borderRadius: 8,
    backgroundColor: Colors.backgroundSecondary,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  tabBar: {
    flexDirection: 'row',
    borderTopWidth: 1,
    borderTopColor: Colors.border,
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
  portfolioGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  gridItem: {
    width: IMAGE_SIZE,
    height: IMAGE_SIZE,
    marginRight: GRID_GAP,
    marginBottom: GRID_GAP,
  },
  gridImage: {
    width: '100%',
    height: '100%',
    backgroundColor: Colors.backgroundSecondary,
  },
  emptyGrid: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: Spacing.xxl * 2,
  },
  emptyText: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
    marginTop: Spacing.md,
  },
});
