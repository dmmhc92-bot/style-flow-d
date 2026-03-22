import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import Button from '../../components/Button';
import Colors from '../../constants/Colors';
import Spacing from '../../constants/Spacing';
import Typography from '../../constants/Typography';
import { useAuthStore } from '../../store/authStore';

interface AccountStatusProps {
  status: 'warned' | 'restricted' | 'suspended' | 'banned';
  reason?: string;
  suspendedUntil?: Date;
  warningsCount?: number;
}

const STATUS_CONFIG = {
  warned: {
    icon: 'alert-circle',
    title: 'Account Warning',
    color: '#FFCC00',
    description: 'Your account has received a warning for violating community guidelines.',
    canAccess: true,
  },
  restricted: {
    icon: 'lock-closed',
    title: 'Account Restricted',
    color: '#FF9500',
    description: 'Some features have been temporarily restricted due to policy violations.',
    canAccess: true,
  },
  suspended: {
    icon: 'time',
    title: 'Account Suspended',
    color: '#FF6B6B',
    description: 'Your account has been temporarily suspended for violating community guidelines.',
    canAccess: false,
  },
  banned: {
    icon: 'close-circle',
    title: 'Account Permanently Banned',
    color: '#FF3B30',
    description: 'Your account has been permanently banned for severe or repeated violations of our community guidelines.',
    canAccess: false,
  },
};

export default function AccountStatusScreen() {
  const router = useRouter();
  const { user, logout } = useAuthStore();
  
  // Get status from user object or default to warned for testing
  const status = (user?.moderation_status as AccountStatusProps['status']) || 'warned';
  const reason = user?.last_warning_reason || user?.suspension_reason || user?.ban_reason || 'Policy violation';
  const suspendedUntil = user?.suspended_until ? new Date(user.suspended_until) : undefined;
  const warningsCount = user?.warnings_count || 0;
  
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.warned;
  
  const formatDate = (date: Date) => {
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };
  
  const handleAppeal = () => {
    router.push('/account/appeal');
  };
  
  const handleViewGuidelines = () => {
    router.push('/settings/guidelines');
  };
  
  const handleContinue = () => {
    router.replace('/tabs');
  };
  
  const handleLogout = async () => {
    await logout();
    router.replace('/');
  };

  return (
    <SafeAreaView style={styles.container} edges={['top', 'bottom']}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Status Icon */}
        <View style={[styles.iconContainer, { backgroundColor: config.color + '20' }]}>
          <Ionicons name={config.icon as any} size={64} color={config.color} />
        </View>
        
        {/* Title */}
        <Text style={[styles.title, { color: config.color }]}>{config.title}</Text>
        
        {/* Description */}
        <Text style={styles.description}>{config.description}</Text>
        
        {/* Reason Card */}
        <View style={styles.reasonCard}>
          <View style={styles.reasonHeader}>
            <Ionicons name="information-circle" size={20} color={Colors.accent} />
            <Text style={styles.reasonTitle}>Reason for Action</Text>
          </View>
          <Text style={styles.reasonText}>{reason}</Text>
          
          {warningsCount > 0 && status !== 'banned' && (
            <View style={styles.warningCountContainer}>
              <Ionicons name="warning" size={16} color={Colors.warning} />
              <Text style={styles.warningCountText}>
                Total warnings: {warningsCount}
              </Text>
            </View>
          )}
        </View>
        
        {/* Suspension Duration */}
        {status === 'suspended' && suspendedUntil && (
          <View style={styles.durationCard}>
            <View style={styles.durationHeader}>
              <Ionicons name="calendar" size={20} color={Colors.info} />
              <Text style={styles.durationTitle}>Suspension Period</Text>
            </View>
            <Text style={styles.durationText}>
              Your account will be restored on:
            </Text>
            <Text style={styles.durationDate}>{formatDate(suspendedUntil)}</Text>
          </View>
        )}
        
        {/* What This Means */}
        <View style={styles.infoSection}>
          <Text style={styles.infoTitle}>What This Means</Text>
          
          {status === 'warned' && (
            <View style={styles.infoList}>
              <InfoItem text="This is a formal warning about your account activity" />
              <InfoItem text="You can continue using StyleFlow normally" />
              <InfoItem text="Additional violations may result in restrictions or suspension" />
            </View>
          )}
          
          {status === 'restricted' && (
            <View style={styles.infoList}>
              <InfoItem text="Some features may be limited (posting, messaging)" />
              <InfoItem text="You can still view content and manage existing data" />
              <InfoItem text="Restrictions will be reviewed after a period of good behavior" />
            </View>
          )}
          
          {status === 'suspended' && (
            <View style={styles.infoList}>
              <InfoItem text="You cannot access app features during suspension" />
              <InfoItem text="Your profile is hidden from other users" />
              <InfoItem text="Your data is preserved and will be available after suspension ends" />
            </View>
          )}
          
          {status === 'banned' && (
            <View style={styles.infoList}>
              <InfoItem text="You cannot access any StyleFlow features" />
              <InfoItem text="Your profile and content have been removed" />
              <InfoItem text="Creating new accounts to circumvent this ban is prohibited" />
            </View>
          )}
        </View>
        
        {/* Guidelines Link */}
        <TouchableOpacity style={styles.guidelinesLink} onPress={handleViewGuidelines}>
          <Ionicons name="book-outline" size={20} color={Colors.accent} />
          <Text style={styles.guidelinesText}>Review Community Guidelines</Text>
          <Ionicons name="chevron-forward" size={16} color={Colors.accent} />
        </TouchableOpacity>
        
        {/* Appeal Info */}
        {(status === 'suspended' || status === 'banned') && (
          <View style={styles.appealSection}>
            <Text style={styles.appealTitle}>Believe this is a mistake?</Text>
            <Text style={styles.appealText}>
              You can submit an appeal to our moderation team. Appeals are typically reviewed within 3-5 business days.
            </Text>
            <TouchableOpacity style={styles.appealButton} onPress={handleAppeal}>
              <Ionicons name="mail-outline" size={18} color={Colors.text} />
              <Text style={styles.appealButtonText}>Submit Appeal</Text>
            </TouchableOpacity>
          </View>
        )}
        
        {/* Action Buttons */}
        <View style={styles.actionButtons}>
          {config.canAccess && (
            <Button
              title="I Understand, Continue"
              onPress={handleContinue}
              style={styles.continueButton}
            />
          )}
          
          <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
            <Ionicons name="log-out-outline" size={18} color={Colors.textSecondary} />
            <Text style={styles.logoutText}>Logout</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const InfoItem = ({ text }: { text: string }) => (
  <View style={styles.infoItem}>
    <View style={styles.infoBullet} />
    <Text style={styles.infoText}>{text}</Text>
  </View>
);

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  scrollContent: {
    padding: Spacing.screenPadding,
    paddingTop: Spacing.xl,
    alignItems: 'center',
  },
  iconContainer: {
    width: 120,
    height: 120,
    borderRadius: 60,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.lg,
  },
  title: {
    fontSize: Typography.h2,
    fontWeight: Typography.bold,
    textAlign: 'center',
    marginBottom: Spacing.sm,
  },
  description: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: Spacing.xl,
    paddingHorizontal: Spacing.md,
  },
  reasonCard: {
    width: '100%',
    backgroundColor: Colors.cardBackground,
    borderRadius: 12,
    padding: Spacing.md,
    marginBottom: Spacing.md,
    borderLeftWidth: 4,
    borderLeftColor: Colors.accent,
  },
  reasonHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
    marginBottom: Spacing.sm,
  },
  reasonTitle: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold,
    color: Colors.text,
  },
  reasonText: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
    lineHeight: 22,
  },
  warningCountContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.xs,
    marginTop: Spacing.sm,
    paddingTop: Spacing.sm,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  warningCountText: {
    fontSize: Typography.bodySmall,
    color: Colors.warning,
    fontWeight: Typography.medium,
  },
  durationCard: {
    width: '100%',
    backgroundColor: Colors.info + '15',
    borderRadius: 12,
    padding: Spacing.md,
    marginBottom: Spacing.lg,
    borderWidth: 1,
    borderColor: Colors.info + '30',
  },
  durationHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
    marginBottom: Spacing.sm,
  },
  durationTitle: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold,
    color: Colors.info,
  },
  durationText: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    marginBottom: Spacing.xs,
  },
  durationDate: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold,
    color: Colors.text,
  },
  infoSection: {
    width: '100%',
    marginBottom: Spacing.lg,
  },
  infoTitle: {
    fontSize: Typography.h4,
    fontWeight: Typography.semibold,
    color: Colors.text,
    marginBottom: Spacing.md,
  },
  infoList: {
    gap: Spacing.sm,
  },
  infoItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: Spacing.sm,
  },
  infoBullet: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: Colors.textSecondary,
    marginTop: 7,
  },
  infoText: {
    flex: 1,
    fontSize: Typography.body,
    color: Colors.textSecondary,
    lineHeight: 22,
  },
  guidelinesLink: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
    paddingVertical: Spacing.md,
    paddingHorizontal: Spacing.lg,
    backgroundColor: Colors.accent + '15',
    borderRadius: 12,
    marginBottom: Spacing.lg,
    width: '100%',
  },
  guidelinesText: {
    flex: 1,
    fontSize: Typography.body,
    color: Colors.accent,
    fontWeight: Typography.medium,
  },
  appealSection: {
    width: '100%',
    backgroundColor: Colors.backgroundSecondary,
    borderRadius: 12,
    padding: Spacing.md,
    marginBottom: Spacing.xl,
  },
  appealTitle: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold,
    color: Colors.text,
    marginBottom: Spacing.xs,
  },
  appealText: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    lineHeight: 20,
    marginBottom: Spacing.md,
  },
  appealButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: Spacing.sm,
    paddingVertical: Spacing.sm,
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: 8,
  },
  appealButtonText: {
    fontSize: Typography.body,
    color: Colors.text,
    fontWeight: Typography.medium,
  },
  actionButtons: {
    width: '100%',
    gap: Spacing.md,
    marginTop: Spacing.md,
  },
  continueButton: {
    width: '100%',
  },
  logoutButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: Spacing.sm,
    paddingVertical: Spacing.md,
  },
  logoutText: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
  },
});
