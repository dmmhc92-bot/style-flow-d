import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Linking,
  Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { Card } from '../../components/Card';
import Colors from '../../constants/Colors';
import Spacing from '../../constants/Spacing';
import Typography from '../../constants/Typography';
import { useAuthStore } from '../../store/authStore';

export default function MoreScreen() {
  const router = useRouter();
  const { user, logout, deleteAccount } = useAuthStore();
  
  const handleLogout = () => {
    Alert.alert(
      'Logout',
      'Are you sure you want to logout?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Logout',
          style: 'destructive',
          onPress: async () => {
            await logout();
            router.replace('/auth/login');
          },
        },
      ]
    );
  };
  
  const handleDeleteAccount = () => {
    Alert.alert(
      'Delete Account',
      'This will permanently delete your account and all data. This action cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await deleteAccount();
              router.replace('/auth/login');
            } catch (error: any) {
              Alert.alert('Error', error.message);
            }
          },
        },
      ]
    );
  };
  
  const MenuItem = ({ icon, title, onPress, color, showBadge }: any) => (
    <TouchableOpacity style={styles.menuItem} onPress={onPress}>
      <View style={[styles.menuIcon, { backgroundColor: (color || Colors.accent) + '15' }]}>
        <Ionicons name={icon} size={24} color={color || Colors.accent} />
      </View>
      <Text style={styles.menuTitle}>{title}</Text>
      {showBadge && (
        <View style={styles.badge}>
          <Text style={styles.badgeText}>Pro</Text>
        </View>
      )}
      <Ionicons name="chevron-forward" size={20} color={Colors.textSecondary} />
    </TouchableOpacity>
  );
  
  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.header}>
          <Text style={styles.title}>More</Text>
        </View>
        
        {/* Profile Section */}
        <Card style={styles.profileCard}>
          <View style={styles.profileContent}>
            <View style={styles.profileAvatar}>
              {user?.profile_photo ? (
                <Text>Image</Text>
              ) : (
                <Ionicons name="person" size={40} color={Colors.textSecondary} />
              )}
            </View>
            <View style={styles.profileInfo}>
              <Text style={styles.profileName}>{user?.full_name}</Text>
              {user?.business_name && (
                <Text style={styles.profileBusiness}>{user.business_name}</Text>
              )}
              <Text style={styles.profileEmail}>{user?.email}</Text>
            </View>
            <TouchableOpacity
              style={styles.editButton}
              onPress={() => router.push('/profile/edit')}
            >
              <Ionicons name="create-outline" size={20} color={Colors.accent} />
            </TouchableOpacity>
          </View>
        </Card>
        
        {/* Business Tools */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Creative Tools</Text>
          <Card style={styles.menuCard}>
            <MenuItem
              icon="flask"
              title="Formula Vault"
              onPress={() => router.push('/settings/formulas')}
            />
            <View style={styles.divider} />
            <MenuItem
              icon="images"
              title="Gallery"
              onPress={() => router.push('/tabs/gallery')}
            />
            <View style={styles.divider} />
            <MenuItem
              icon="briefcase"
              title="Portfolio"
              onPress={() => router.push('/portfolio')}
            />
            <View style={styles.divider} />
            <MenuItem
              icon="calendar-outline"
              title="No-Show Tracking"
              onPress={() => router.push('/settings/no-shows')}
            />
          </Card>
        </View>
        
        {/* AI Assistant */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>AI Assistant</Text>
          <Card style={styles.menuCard}>
            <MenuItem
              icon="sparkles"
              title="AI Chat Assistant"
              onPress={() => router.push('/ai/chat')}
              color={Colors.accent}
            />
          </Card>
        </View>
        
        {/* Subscription */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Subscription</Text>
          <Card style={styles.menuCard}>
            <MenuItem
              icon="diamond"
              title="StyleFlow Pro"
              onPress={() => router.push('/settings/subscription')}
              color={Colors.vip}
              showBadge
            />
          </Card>
        </View>
        
        {/* Support & Legal */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Support & Legal</Text>
          <Card style={styles.menuCard}>
            <MenuItem
              icon="help-circle"
              title="Support"
              onPress={() => Linking.openURL('https://styleflow.app/support')}
            />
            <View style={styles.divider} />
            <MenuItem
              icon="document-text"
              title="Privacy Policy"
              onPress={() => Linking.openURL('https://styleflow.app/privacy')}
            />
            <View style={styles.divider} />
            <MenuItem
              icon="shield-checkmark"
              title="Terms of Service"
              onPress={() => Linking.openURL('https://styleflow.app/terms')}
            />
          </Card>
        </View>
        
        {/* Privacy & Safety */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Privacy & Safety</Text>
          <Card style={styles.menuCard}>
            <MenuItem
              icon="ban-outline"
              title="Blocked Users"
              onPress={() => router.push('/settings/blocked')}
            />
            <View style={styles.divider} />
            <MenuItem
              icon="shield-outline"
              title="Community Guidelines"
              onPress={() => router.push('/settings/guidelines')}
            />
          </Card>
        </View>
        
        {/* Admin Section - Only shown to admins */}
        {user?.is_admin && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Admin</Text>
            <Card style={[styles.menuCard, styles.adminCard]}>
              <MenuItem
                icon="shield-half"
                title="Moderation Dashboard"
                onPress={() => router.push('/admin/moderation')}
                color={Colors.accent}
              />
            </Card>
          </View>
        )}
        
        {/* Account Actions */}
        <View style={styles.section}>
          <Card style={styles.menuCard}>
            <MenuItem
              icon="log-out-outline"
              title="Logout"
              onPress={handleLogout}
              color={Colors.textSecondary}
            />
            <View style={styles.divider} />
            <MenuItem
              icon="trash-outline"
              title="Delete Account"
              onPress={handleDeleteAccount}
              color={Colors.error}
            />
          </Card>
        </View>
        
        <Text style={styles.version}>StyleFlow v1.0.0</Text>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  scrollContent: {
    paddingBottom: Spacing.xxl,
  },
  header: {
    paddingHorizontal: Spacing.screenPadding,
    paddingVertical: Spacing.md,
  },
  title: {
    fontSize: Typography.h2,
    fontWeight: Typography.bold,
    color: Colors.text,
  },
  profileCard: {
    marginHorizontal: Spacing.screenPadding,
    marginBottom: Spacing.lg,
  },
  profileContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  profileAvatar: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: Colors.backgroundSecondary,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: Spacing.md,
  },
  profileInfo: {
    flex: 1,
  },
  profileName: {
    fontSize: Typography.h4,
    fontWeight: Typography.semibold,
    color: Colors.text,
    marginBottom: 2,
  },
  profileBusiness: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    marginBottom: 2,
  },
  profileEmail: {
    fontSize: Typography.bodySmall,
    color: Colors.textLight,
  },
  editButton: {
    padding: Spacing.sm,
  },
  section: {
    marginBottom: Spacing.lg,
  },
  sectionTitle: {
    fontSize: Typography.bodySmall,
    fontWeight: Typography.semibold,
    color: Colors.textSecondary,
    marginBottom: Spacing.sm,
    marginLeft: Spacing.screenPadding,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  menuCard: {
    marginHorizontal: Spacing.screenPadding,
  },
  adminCard: {
    borderWidth: 1,
    borderColor: Colors.accent + '40',
    backgroundColor: Colors.accent + '05',
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: Spacing.md,
  },
  menuIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: Spacing.md,
  },
  menuTitle: {
    flex: 1,
    fontSize: Typography.body,
    color: Colors.text,
    fontWeight: Typography.medium,
  },
  badge: {
    backgroundColor: Colors.vip + '20',
    paddingHorizontal: Spacing.sm,
    paddingVertical: 2,
    borderRadius: 8,
    marginRight: Spacing.sm,
  },
  badgeText: {
    fontSize: Typography.caption,
    fontWeight: Typography.semibold,
    color: Colors.vip,
  },
  divider: {
    height: 1,
    backgroundColor: Colors.border,
    marginLeft: 56,
  },
  version: {
    fontSize: Typography.caption,
    color: Colors.textLight,
    textAlign: 'center',
    marginTop: Spacing.xl,
  },
});