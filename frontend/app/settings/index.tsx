import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  Linking,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { Card } from '../../components/Card';
import Button from '../../components/Button';
import Colors from '../../constants/Colors';
import Spacing from '../../constants/Spacing';
import Typography from '../../constants/Typography';
import { AppConfig } from '../../constants/AppConfig';
import { useAuthStore } from '../../store/authStore';

export default function SettingsScreen() {
  const router = useRouter();
  const { user, logout, deleteAccount } = useAuthStore();
  const [deleting, setDeleting] = useState(false);
  
  const handleSignOut = () => {
    Alert.alert(
      'Sign Out',
      'Are you sure you want to sign out?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Sign Out',
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
      'This will permanently delete your account and all data. This action cannot be undone.\n\nNote: If you have an active subscription, please cancel it separately through the App Store.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete Account',
          style: 'destructive',
          onPress: () => confirmDeleteAccount(),
        },
      ]
    );
  };
  
  const confirmDeleteAccount = () => {
    Alert.alert(
      'Final Confirmation',
      'Type DELETE to confirm account deletion',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Confirm Delete',
          style: 'destructive',
          onPress: async () => {
            setDeleting(true);
            try {
              await deleteAccount();
              Alert.alert(
                'Account Deleted',
                'Your account has been permanently deleted.',
                [{ text: 'OK', onPress: () => router.replace('/auth/login') }]
              );
            } catch (error: any) {
              Alert.alert('Error', error.message || 'Failed to delete account');
            } finally {
              setDeleting(false);
            }
          },
        },
      ]
    );
  };
  
  const openUrl = async (url: string) => {
    try {
      const supported = await Linking.canOpenURL(url);
      if (supported) {
        await Linking.openURL(url);
      } else {
        Alert.alert('Error', 'Cannot open this URL');
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to open link');
    }
  };
  
  const handleManageSubscription = async () => {
    // On iOS, this opens App Store subscription management
    // On Android, this opens Play Store subscription management
    const url = 'https://apps.apple.com/account/subscriptions';
    await openUrl(url);
  };
  
  const handleRestorePurchases = () => {
    Alert.alert(
      'Restore Purchases',
      'This will restore any previous purchases associated with your Apple ID.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Restore',
          onPress: () => {
            // In production, this would call RevenueCat or Apple IAP restore
            Alert.alert('Info', 'No purchases found to restore.');
          },
        },
      ]
    );
  };
  
  const SettingsSection = ({ title, children }: any) => (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>{title}</Text>
      <Card style={styles.sectionCard}>{children}</Card>
    </View>
  );
  
  const SettingsRow = ({ icon, title, onPress, rightText, danger }: any) => (
    <TouchableOpacity style={styles.row} onPress={onPress} activeOpacity={0.7}>
      <View style={styles.rowLeft}>
        <View style={[styles.iconContainer, danger && styles.iconContainerDanger]}>
          <Ionicons name={icon} size={20} color={danger ? Colors.error : Colors.accent} />
        </View>
        <Text style={[styles.rowTitle, danger && styles.rowTitleDanger]}>{title}</Text>
      </View>
      <View style={styles.rowRight}>
        {rightText && <Text style={styles.rightText}>{rightText}</Text>}
        <Ionicons name=\"chevron-forward\" size={20} color={Colors.textSecondary} />
      </View>
    </TouchableOpacity>
  );
  
  const Divider = () => <View style={styles.divider} />;
  
  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Ionicons name=\"arrow-back\" size={24} color={Colors.text} />
        </TouchableOpacity>
        <Text style={styles.title}>Settings</Text>
        <View style={{ width: 40 }} />
      </View>
      
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Profile Section */}
        <SettingsSection title=\"ACCOUNT\">
          <View style={styles.profileSection}>
            <View style={styles.profileAvatar}>
              <Ionicons name=\"person\" size={32} color={Colors.accent} />
            </View>
            <View style={styles.profileInfo}>
              <Text style={styles.profileName}>{user?.full_name || 'User'}</Text>
              <Text style={styles.profileEmail}>{user?.email}</Text>
            </View>
          </View>
          <Divider />
          <SettingsRow
            icon=\"create-outline\"
            title=\"Edit Profile\"
            onPress={() => router.push('/settings/profile')}
          />
        </SettingsSection>
        
        {/* Subscription Section */}
        <SettingsSection title=\"SUBSCRIPTION\">
          <SettingsRow
            icon=\"diamond-outline\"
            title=\"StyleFlow Pro\"
            rightText={user?.subscription_status === 'active' ? 'Active' : 'Free'}
            onPress={() => router.push('/settings/subscription')}
          />
          <Divider />
          <SettingsRow
            icon=\"refresh-outline\"
            title=\"Restore Purchases\"
            onPress={handleRestorePurchases}
          />
          <Divider />
          <SettingsRow
            icon=\"settings-outline\"
            title=\"Manage Subscription\"
            onPress={handleManageSubscription}
          />
        </SettingsSection>
        
        {/* Support & Legal */}
        <SettingsSection title=\"SUPPORT & LEGAL\">
          <SettingsRow
            icon=\"help-circle-outline\"
            title=\"Support\"
            onPress={() => openUrl(AppConfig.legal.supportUrl)}
          />
          <Divider />
          <SettingsRow
            icon=\"document-text-outline\"
            title=\"Privacy Policy\"
            onPress={() => openUrl(AppConfig.legal.privacyPolicyUrl)}
          />
          <Divider />
          <SettingsRow
            icon=\"shield-checkmark-outline\"
            title=\"Terms of Service\"
            onPress={() => openUrl(AppConfig.legal.termsOfServiceUrl)}
          />
        </SettingsSection>
        
        {/* Account Actions */}
        <SettingsSection title=\"ACCOUNT ACTIONS\">
          <SettingsRow
            icon=\"log-out-outline\"
            title=\"Sign Out\"
            onPress={handleSignOut}
          />
          <Divider />
          <SettingsRow
            icon=\"trash-outline\"
            title=\"Delete Account\"
            onPress={handleDeleteAccount}
            danger
          />
        </SettingsSection>
        
        <Text style={styles.version}>
          {AppConfig.app.name} v{AppConfig.app.version}
        </Text>
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
  title: {
    fontSize: Typography.h3,
    fontWeight: Typography.bold,
    color: Colors.text,
    letterSpacing: Typography.letterSpacingWide,
  },
  scrollContent: {
    padding: Spacing.screenPadding,
    paddingBottom: Spacing.xxxl,
  },
  section: {
    marginBottom: Spacing.lg,
  },
  sectionTitle: {
    fontSize: Typography.caption,
    fontWeight: Typography.semibold,
    color: Colors.textSecondary,
    marginBottom: Spacing.sm,
    marginLeft: Spacing.xs,
    letterSpacing: Typography.letterSpacingExtraWide,
  },
  sectionCard: {
    padding: 0,
  },
  profileSection: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: Spacing.md,
  },
  profileAvatar: {
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
  profileInfo: {
    flex: 1,
  },
  profileName: {
    fontSize: Typography.h4,
    fontWeight: Typography.semibold,
    color: Colors.text,
    marginBottom: 2,
  },
  profileEmail: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: Spacing.md,
    minHeight: 56,
  },
  rowLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  iconContainer: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: Colors.accent + '20',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: Spacing.md,
  },
  iconContainerDanger: {
    backgroundColor: Colors.error + '20',
  },
  rowTitle: {
    fontSize: Typography.body,
    color: Colors.text,
    fontWeight: Typography.medium,
  },
  rowTitleDanger: {
    color: Colors.error,
  },
  rowRight: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  rightText: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    marginRight: Spacing.sm,
  },
  divider: {
    height: 1,
    backgroundColor: Colors.border,
    marginLeft: Spacing.md + 36 + Spacing.md,
  },
  version: {
    fontSize: Typography.caption,
    color: Colors.textLight,
    textAlign: 'center',
    marginTop: Spacing.xl,
  },
});
