import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  Linking,
  ActivityIndicator,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import Button from '../../components/Button';
import { Card } from '../../components/Card';
import Colors from '../../constants/Colors';
import Spacing from '../../constants/Spacing';
import Typography from '../../constants/Typography';
import api from '../../utils/api';

export default function UserProfileScreen() {
  const router = useRouter();
  const { id } = useLocalSearchParams();
  
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [following, setFollowing] = useState(false);
  const [followLoading, setFollowLoading] = useState(false);
  
  useEffect(() => {
    loadProfile();
  }, [id]);
  
  const loadProfile = async () => {
    setLoading(true);
    try {
      const response = await api.get(`/users/${id}/profile`);
      setProfile(response.data);
      setFollowing(response.data.is_following);
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.detail || 'Failed to load profile');
      router.back();
    } finally {
      setLoading(false);
    }
  };
  
  const handleFollow = async () => {
    setFollowLoading(true);
    try {
      if (following) {
        await api.delete(`/users/${id}/follow`);
        setFollowing(false);
        setProfile({ ...profile, followers_count: profile.followers_count - 1 });
      } else {
        await api.post(`/users/${id}/follow`);
        setFollowing(true);
        setProfile({ ...profile, followers_count: profile.followers_count + 1 });
      }
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.detail || 'Action failed');
    } finally {
      setFollowLoading(false);
    }
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
      } else {
        Alert.alert('Error', 'Cannot open this link');
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
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color={Colors.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Profile</Text>
        <View style={{ width: 40 }} />
      </View>
      
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.profileHeader}>
          <View style={styles.avatar}>
            <Ionicons name="person" size={48} color={Colors.accent} />
          </View>
          
          <Text style={styles.name}>{profile.full_name}</Text>
          {profile.business_name && (
            <Text style={styles.businessName}>{profile.business_name}</Text>
          )}
          {profile.city && (
            <Text style={styles.city}>{profile.city}</Text>
          )}
          
          <View style={styles.stats}>
            <View style={styles.stat}>
              <Text style={styles.statValue}>{profile.followers_count || 0}</Text>
              <Text style={styles.statLabel}>Followers</Text>
            </View>
            <View style={styles.statDivider} />
            <View style={styles.stat}>
              <Text style={styles.statValue}>{profile.following_count || 0}</Text>
              <Text style={styles.statLabel}>Following</Text>
            </View>
          </View>
          
          <Button
            title={following ? 'Following' : 'Follow'}
            onPress={handleFollow}
            loading={followLoading}
            variant={following ? 'outline' : 'primary'}
            style={styles.followButton}
          />
        </View>
        
        {profile.bio && (
          <Card style={styles.section}>
            <Text style={styles.sectionTitle}>About</Text>
            <Text style={styles.bio}>{profile.bio}</Text>
          </Card>
        )}
        
        {profile.specialties && (
          <Card style={styles.section}>
            <Text style={styles.sectionTitle}>Specialties</Text>
            <Text style={styles.specialties}>{profile.specialties}</Text>
          </Card>
        )}
        
        {(profile.instagram_handle || profile.tiktok_handle || profile.website_url) && (
          <Card style={styles.section}>
            <Text style={styles.sectionTitle}>Connect</Text>
            {profile.instagram_handle && (
              <TouchableOpacity
                style={styles.socialLink}
                onPress={() => openSocialLink('instagram', profile.instagram_handle)}
              >
                <Ionicons name="logo-instagram" size={24} color={Colors.accent} />
                <Text style={styles.socialText}>{profile.instagram_handle}</Text>
                <Ionicons name="open-outline" size={16} color={Colors.textSecondary} />
              </TouchableOpacity>
            )}
            {profile.tiktok_handle && (
              <TouchableOpacity
                style={styles.socialLink}
                onPress={() => openSocialLink('tiktok', profile.tiktok_handle)}
              >
                <Ionicons name="logo-tiktok" size={24} color={Colors.accent} />
                <Text style={styles.socialText}>{profile.tiktok_handle}</Text>
                <Ionicons name="open-outline" size={16} color={Colors.textSecondary} />
              </TouchableOpacity>
            )}
            {profile.website_url && (
              <TouchableOpacity
                style={styles.socialLink}
                onPress={() => openSocialLink('website', profile.website_url)}
              >
                <Ionicons name="globe-outline" size={24} color={Colors.accent} />
                <Text style={styles.socialText}>{profile.website_url}</Text>
                <Ionicons name="open-outline" size={16} color={Colors.textSecondary} />
              </TouchableOpacity>
            )}
          </Card>
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
  scrollContent: {
    padding: Spacing.screenPadding,
  },
  profileHeader: {
    alignItems: 'center',
    marginBottom: Spacing.lg,
  },
  avatar: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: Colors.accent + '20',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.md,
    borderWidth: 3,
    borderColor: Colors.accent + '40',
  },
  name: {
    fontSize: Typography.h2,
    fontWeight: Typography.bold,
    color: Colors.text,
    marginBottom: Spacing.xs,
  },
  businessName: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
    marginBottom: Spacing.xs,
  },
  city: {
    fontSize: Typography.bodySmall,
    color: Colors.textLight,
    marginBottom: Spacing.md,
  },
  stats: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: Spacing.lg,
  },
  stat: {
    alignItems: 'center',
    paddingHorizontal: Spacing.xl,
  },
  statValue: {
    fontSize: Typography.h3,
    fontWeight: Typography.bold,
    color: Colors.text,
  },
  statLabel: {
    fontSize: Typography.caption,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  statDivider: {
    width: 1,
    height: 30,
    backgroundColor: Colors.border,
  },
  followButton: {
    minWidth: 200,
  },
  section: {
    marginBottom: Spacing.md,
  },
  sectionTitle: {
    fontSize: Typography.h4,
    fontWeight: Typography.semibold,
    color: Colors.text,
    marginBottom: Spacing.sm,
  },
  bio: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
    lineHeight: Typography.body * Typography.lineHeightNormal,
  },
  specialties: {
    fontSize: Typography.body,
    color: Colors.accent,
  },
  socialLink: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: Spacing.sm,
    marginTop: Spacing.xs,
  },
  socialText: {
    flex: 1,
    fontSize: Typography.body,
    color: Colors.text,
    marginLeft: Spacing.md,
  },
});