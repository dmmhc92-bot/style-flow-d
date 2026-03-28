import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Modal } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import Colors from '../constants/Colors';
import Spacing from '../constants/Spacing';
import Typography from '../constants/Typography';
import { useSubscriptionStore, usePremiumFeature } from '../store/subscriptionStore';
import { useAuthStore } from '../store/authStore';

interface PremiumGateProps {
  feature: string;
  children: React.ReactNode;
  fallback?: React.ReactNode;
  showUpgradePrompt?: boolean;
}

/**
 * PremiumGate - Wraps content that requires premium subscription
 * 
 * IMPORTANT: isTester accounts (App Store Review) automatically bypass all gates
 * 
 * Usage:
 * <PremiumGate feature="unlimited_clients">
 *   <UnlimitedClientsFeature />
 * </PremiumGate>
 */
export const PremiumGate: React.FC<PremiumGateProps> = ({ 
  feature, 
  children, 
  fallback,
  showUpgradePrompt = true 
}) => {
  const router = useRouter();
  const { hasAccess, requiresPremium, isPremium } = usePremiumFeature(feature);
  const { isTester, user } = useAuthStore();
  const [showModal, setShowModal] = React.useState(false);

  // CRITICAL: Testers ALWAYS get access (App Store Review bypass)
  const isTesterAccount = isTester || user?.is_tester;
  
  // If feature doesn't require premium, user has premium, OR user is a tester - show content
  if (hasAccess || isTesterAccount) {
    return <>{children}</>;
  }

  // If no fallback and no prompt, just hide the content
  if (!fallback && !showUpgradePrompt) {
    return null;
  }

  const handleUpgrade = () => {
    setShowModal(false);
    router.push('/settings/subscription');
  };

  // Show fallback or locked UI
  return (
    <>
      {fallback || (
        <TouchableOpacity 
          style={styles.lockedContainer}
          onPress={() => setShowModal(true)}
        >
          <View style={styles.lockedIcon}>
            <Ionicons name="lock-closed" size={24} color={Colors.vip} />
          </View>
          <Text style={styles.lockedText}>Premium Feature</Text>
          <Text style={styles.lockedSubtext}>Tap to unlock</Text>
        </TouchableOpacity>
      )}

      {showUpgradePrompt && (
        <Modal
          visible={showModal}
          transparent
          animationType="fade"
          onRequestClose={() => setShowModal(false)}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.modalContent}>
              <View style={styles.modalIcon}>
                <Ionicons name="diamond" size={48} color={Colors.vip} />
              </View>
              <Text style={styles.modalTitle}>Premium Feature</Text>
              <Text style={styles.modalText}>
                This feature is available with StyleFlow Pro subscription.
              </Text>
              <TouchableOpacity style={styles.upgradeButton} onPress={handleUpgrade}>
                <Text style={styles.upgradeButtonText}>Upgrade to Pro</Text>
              </TouchableOpacity>
              <TouchableOpacity 
                style={styles.cancelButton} 
                onPress={() => setShowModal(false)}
              >
                <Text style={styles.cancelButtonText}>Not Now</Text>
              </TouchableOpacity>
            </View>
          </View>
        </Modal>
      )}
    </>
  );
};

/**
 * PremiumBadge - Shows a small badge indicating premium content
 */
export const PremiumBadge: React.FC<{ style?: any }> = ({ style }) => {
  return (
    <View style={[styles.badge, style]}>
      <Ionicons name="diamond" size={12} color={Colors.vip} />
      <Text style={styles.badgeText}>PRO</Text>
    </View>
  );
};

/**
 * PremiumButton - Button that navigates to subscription screen
 * Hidden for testers since they already have full access
 */
export const PremiumButton: React.FC<{ 
  title?: string;
  style?: any;
  onPress?: () => void;
}> = ({ title = 'Upgrade to Pro', style, onPress }) => {
  const router = useRouter();
  const { isPremium } = useSubscriptionStore();
  const { isTester, user } = useAuthStore();

  // Hide for premium users AND testers
  if (isPremium || isTester || user?.is_tester) return null;

  const handlePress = () => {
    if (onPress) {
      onPress();
    } else {
      router.push('/settings/subscription');
    }
  };

  return (
    <TouchableOpacity style={[styles.premiumButton, style]} onPress={handlePress}>
      <Ionicons name="diamond" size={16} color={Colors.background} />
      <Text style={styles.premiumButtonText}>{title}</Text>
    </TouchableOpacity>
  );
};

/**
 * withPremiumGate - HOC for wrapping entire screens
 * IMPORTANT: Testers (App Store Review) automatically bypass all gates
 */
export function withPremiumGate<P extends object>(
  WrappedComponent: React.ComponentType<P>,
  feature: string
) {
  return function PremiumGatedComponent(props: P) {
    const { hasAccess } = usePremiumFeature(feature);
    const { isTester, user } = useAuthStore();
    const router = useRouter();

    // CRITICAL: Testers ALWAYS get access (App Store Review bypass)
    const isTesterAccount = isTester || user?.is_tester;
    
    if (!hasAccess && !isTesterAccount) {
      return (
        <View style={styles.fullScreenLock}>
          <View style={styles.lockContent}>
            <View style={styles.lockIconLarge}>
              <Ionicons name="diamond" size={64} color={Colors.vip} />
            </View>
            <Text style={styles.lockTitle}>Premium Feature</Text>
            <Text style={styles.lockDescription}>
              This feature requires a StyleFlow Pro subscription.
            </Text>
            <TouchableOpacity 
              style={styles.upgradeButton}
              onPress={() => router.push('/settings/subscription')}
            >
              <Text style={styles.upgradeButtonText}>Upgrade to Pro</Text>
            </TouchableOpacity>
            <TouchableOpacity 
              style={styles.backButton}
              onPress={() => router.back()}
            >
              <Text style={styles.backButtonText}>Go Back</Text>
            </TouchableOpacity>
          </View>
        </View>
      );
    }

    return <WrappedComponent {...props} />;
  };
}

const styles = StyleSheet.create({
  lockedContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: Spacing.xl,
    backgroundColor: Colors.backgroundSecondary,
    borderRadius: Spacing.radiusMedium,
    borderWidth: 1,
    borderColor: Colors.border,
    borderStyle: 'dashed',
  },
  lockedIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: Colors.vip + '15',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.sm,
  },
  lockedText: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold as any,
    color: Colors.text,
  },
  lockedSubtext: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    marginTop: 4,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: Spacing.screenPadding,
  },
  modalContent: {
    backgroundColor: Colors.background,
    borderRadius: Spacing.radiusLarge,
    padding: Spacing.xl,
    width: '100%',
    maxWidth: 320,
    alignItems: 'center',
  },
  modalIcon: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: Colors.vip + '15',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.md,
  },
  modalTitle: {
    fontSize: Typography.h3,
    fontWeight: Typography.bold as any,
    color: Colors.text,
    marginBottom: Spacing.sm,
  },
  modalText: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginBottom: Spacing.lg,
  },
  upgradeButton: {
    backgroundColor: Colors.accent,
    paddingVertical: Spacing.md,
    paddingHorizontal: Spacing.xl,
    borderRadius: Spacing.radiusMedium,
    width: '100%',
    alignItems: 'center',
    marginBottom: Spacing.sm,
  },
  upgradeButtonText: {
    color: Colors.background,
    fontSize: Typography.body,
    fontWeight: Typography.bold as any,
  },
  cancelButton: {
    paddingVertical: Spacing.md,
  },
  cancelButtonText: {
    color: Colors.textSecondary,
    fontSize: Typography.body,
  },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.vip + '15',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    gap: 4,
  },
  badgeText: {
    fontSize: 10,
    fontWeight: Typography.bold as any,
    color: Colors.vip,
  },
  premiumButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.accent,
    paddingVertical: Spacing.sm,
    paddingHorizontal: Spacing.md,
    borderRadius: Spacing.radiusMedium,
    gap: Spacing.xs,
  },
  premiumButtonText: {
    color: Colors.background,
    fontSize: Typography.bodySmall,
    fontWeight: Typography.semibold as any,
  },
  fullScreenLock: {
    flex: 1,
    backgroundColor: Colors.background,
    justifyContent: 'center',
    alignItems: 'center',
    padding: Spacing.screenPadding,
  },
  lockContent: {
    alignItems: 'center',
    maxWidth: 300,
  },
  lockIconLarge: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: Colors.vip + '15',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.lg,
  },
  lockTitle: {
    fontSize: Typography.h2,
    fontWeight: Typography.bold as any,
    color: Colors.text,
    marginBottom: Spacing.sm,
  },
  lockDescription: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginBottom: Spacing.xl,
  },
  backButton: {
    marginTop: Spacing.md,
    paddingVertical: Spacing.md,
  },
  backButtonText: {
    color: Colors.textSecondary,
    fontSize: Typography.body,
  },
});
