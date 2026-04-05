import React, { useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Modal } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import Colors from '../constants/Colors';
import Spacing from '../constants/Spacing';
import Typography from '../constants/Typography';
import { useSubscriptionStore, usePremiumFeature } from '../store/subscriptionStore';
import { useAuthStore } from '../store/authStore';
import { useTrialStore, TRIAL_LIMITS } from '../store/trialStore';

interface PremiumGateProps {
  feature: string;
  children: React.ReactNode;
  fallback?: React.ReactNode;
  showUpgradePrompt?: boolean;
}

/**
 * PremiumGate - Wraps content that requires premium subscription
 * 
 * TRIAL SYSTEM: Users get 3 free uses, then paywall activates on 4th use
 * TESTER BYPASS: App Store Review accounts (is_tester=true) bypass all gates
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
  const { getTrialStatus, loadUsage } = useTrialStore();
  const [showModal, setShowModal] = React.useState(false);

  // Load trial usage on mount
  useEffect(() => {
    loadUsage();
  }, []);

  // CRITICAL: Testers ALWAYS get access (App Store Review bypass)
  const isTesterAccount = isTester || user?.is_tester;
  
  // Check trial status
  const trialStatus = getTrialStatus();
  
  // If user is premium, tester, or has trial remaining - show content
  if (isPremium || isTesterAccount || (!trialStatus.isTrialExpired && !requiresPremium)) {
    return <>{children}</>;
  }
  
  // If feature doesn't require premium and trial not expired - show content
  if (!requiresPremium) {
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
 * TrialGate - Blocks users after 3 free uses with paywall
 * 
 * CRITICAL: This is the main paywall gate that enforces the trial limit
 * - Users get 3 free "premium actions" (creating clients, formulas, posts, etc.)
 * - On the 4th action, they are blocked and shown paywall
 * - Testers (App Store Review) bypass this entirely
 * - Premium subscribers bypass this entirely
 */
interface TrialGateProps {
  children: React.ReactNode;
  onTrialExpired?: () => void;
}

export const TrialGate: React.FC<TrialGateProps> = ({ children, onTrialExpired }) => {
  const router = useRouter();
  const { isPremium } = useSubscriptionStore();
  const { isTester, user } = useAuthStore();
  const { getTrialStatus, loadUsage } = useTrialStore();
  const [showPaywall, setShowPaywall] = React.useState(false);

  // Load trial usage on mount
  useEffect(() => {
    loadUsage();
  }, []);

  // CRITICAL: Testers ALWAYS bypass (App Store Review)
  const isTesterAccount = isTester || user?.is_tester;
  
  // Check trial status
  const trialStatus = getTrialStatus();
  
  // Premium users and testers always have access
  if (isPremium || isTesterAccount) {
    return <>{children}</>;
  }
  
  // If trial expired, show paywall
  if (trialStatus.isTrialExpired) {
    return (
      <View style={styles.fullScreenLock}>
        <View style={styles.lockContent}>
          <View style={styles.lockIconLarge}>
            <Ionicons name="diamond" size={64} color={Colors.vip} />
          </View>
          <Text style={styles.lockTitle}>Free Trial Ended</Text>
          <Text style={styles.lockDescription}>
            You've used your {TRIAL_LIMITS.MAX_FREE_USES} free premium actions.{'\n'}
            Subscribe to StyleFlow Pro to continue.
          </Text>
          <TouchableOpacity 
            style={styles.upgradeButton}
            onPress={() => router.push('/settings/subscription')}
          >
            <Text style={styles.upgradeButtonText}>Subscribe Now - $9.99/mo</Text>
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
  
  return <>{children}</>;
};

/**
 * useTrialAction - Hook to track and validate premium actions
 * 
 * Usage:
 * const { canPerformAction, performAction, remainingUses } = useTrialAction('clientsCreated');
 * 
 * if (canPerformAction) {
 *   await performAction(); // Increments usage
 *   // Do the action
 * } else {
 *   // Show paywall
 * }
 */
export const useTrialAction = (actionType: 'clientsCreated' | 'formulasCreated' | 'appointmentsCreated' | 'postsCreated' | 'aiChatsUsed') => {
  const router = useRouter();
  const { isPremium } = useSubscriptionStore();
  const { isTester, user } = useAuthStore();
  const { getTrialStatus, incrementUsage, loadUsage } = useTrialStore();
  const [showPaywall, setShowPaywall] = React.useState(false);

  // CRITICAL: Testers ALWAYS bypass
  const isTesterAccount = isTester || user?.is_tester;
  
  // Check if user can perform this action
  const trialStatus = getTrialStatus();
  const canPerformAction = isPremium || isTesterAccount || !trialStatus.isTrialExpired;
  const remainingUses = Math.max(0, TRIAL_LIMITS.MAX_FREE_USES - trialStatus.totalUsed);

  // Perform the action (increment usage counter)
  const performAction = async (): Promise<boolean> => {
    // Premium/tester users don't consume trial
    if (isPremium || isTesterAccount) {
      return true;
    }
    
    // Check if trial expired
    if (trialStatus.isTrialExpired) {
      setShowPaywall(true);
      return false;
    }
    
    // Increment usage
    const success = await incrementUsage(actionType);
    
    // Check if this was the last free action
    const newStatus = getTrialStatus();
    if (newStatus.isTrialExpired) {
      // Show paywall after this action completes
      setTimeout(() => setShowPaywall(true), 500);
    }
    
    return success;
  };

  const PaywallModal = () => (
    <Modal
      visible={showPaywall}
      transparent
      animationType="slide"
      onRequestClose={() => setShowPaywall(false)}
    >
      <View style={styles.paywallOverlay}>
        <View style={styles.paywallContent}>
          <TouchableOpacity 
            style={styles.closeButton}
            onPress={() => setShowPaywall(false)}
          >
            <Ionicons name="close" size={24} color={Colors.text} />
          </TouchableOpacity>
          
          <View style={styles.paywallIcon}>
            <Ionicons name="diamond" size={56} color={Colors.vip} />
          </View>
          
          <Text style={styles.paywallTitle}>Free Trial Ended</Text>
          
          <Text style={styles.paywallSubtitle}>
            You've used all {TRIAL_LIMITS.MAX_FREE_USES} free premium actions
          </Text>
          
          <View style={styles.featuresList}>
            <FeatureItem icon="people" text="Unlimited clients" />
            <FeatureItem icon="flask" text="Unlimited formulas" />
            <FeatureItem icon="sparkles" text="AI Assistant" />
            <FeatureItem icon="calendar" text="Full scheduling" />
            <FeatureItem icon="images" text="Portfolio showcase" />
          </View>
          
          <TouchableOpacity 
            style={styles.subscribeButton}
            onPress={() => {
              setShowPaywall(false);
              router.push('/settings/subscription');
            }}
          >
            <Text style={styles.subscribeButtonText}>Subscribe Now - $9.99/mo</Text>
          </TouchableOpacity>
          
          <Text style={styles.trialNote}>
            Cancel anytime • 7-day money back guarantee
          </Text>
        </View>
      </View>
    </Modal>
  );

  return {
    canPerformAction,
    performAction,
    remainingUses,
    showPaywall,
    setShowPaywall,
    PaywallModal,
    isPremium: isPremium || isTesterAccount,
  };
};

const FeatureItem = ({ icon, text }: { icon: string; text: string }) => (
  <View style={styles.featureItem}>
    <Ionicons name={icon as any} size={20} color={Colors.accent} />
    <Text style={styles.featureText}>{text}</Text>
  </View>
);

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
 * TrialBadge - Shows remaining free uses
 */
export const TrialBadge: React.FC<{ style?: any }> = ({ style }) => {
  const { isPremium } = useSubscriptionStore();
  const { isTester, user } = useAuthStore();
  const { getTrialStatus } = useTrialStore();
  
  // Don't show for premium or testers
  if (isPremium || isTester || user?.is_tester) return null;
  
  const { totalUsed, maxFree, isTrialExpired } = getTrialStatus();
  const remaining = Math.max(0, maxFree - totalUsed);
  
  if (isTrialExpired) return null;
  
  return (
    <View style={[styles.trialBadge, style]}>
      <Ionicons name="gift" size={12} color={Colors.accent} />
      <Text style={styles.trialBadgeText}>{remaining} free left</Text>
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

/**
 * withTrialGate - HOC that wraps screens with trial limit enforcement
 * Shows paywall after 3 free uses
 */
export function withTrialGate<P extends object>(WrappedComponent: React.ComponentType<P>) {
  return function TrialGatedComponent(props: P) {
    return (
      <TrialGate>
        <WrappedComponent {...props} />
      </TrialGate>
    );
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
  trialBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.accent + '15',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    gap: 4,
  },
  trialBadgeText: {
    fontSize: 10,
    fontWeight: Typography.semibold as any,
    color: Colors.accent,
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
    lineHeight: 22,
  },
  backButton: {
    marginTop: Spacing.md,
    paddingVertical: Spacing.md,
  },
  backButtonText: {
    color: Colors.textSecondary,
    fontSize: Typography.body,
  },
  // Paywall Modal Styles
  paywallOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.85)',
    justifyContent: 'flex-end',
  },
  paywallContent: {
    backgroundColor: Colors.background,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: Spacing.xl,
    paddingTop: Spacing.lg,
    paddingBottom: 40,
    alignItems: 'center',
  },
  closeButton: {
    position: 'absolute',
    top: Spacing.md,
    right: Spacing.md,
    padding: Spacing.sm,
    zIndex: 1,
  },
  paywallIcon: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: Colors.vip + '15',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.md,
    marginTop: Spacing.md,
  },
  paywallTitle: {
    fontSize: Typography.h2,
    fontWeight: Typography.bold as any,
    color: Colors.text,
    marginBottom: Spacing.xs,
  },
  paywallSubtitle: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginBottom: Spacing.lg,
  },
  featuresList: {
    width: '100%',
    marginBottom: Spacing.lg,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: Spacing.sm,
    gap: Spacing.sm,
  },
  featureText: {
    fontSize: Typography.body,
    color: Colors.text,
  },
  subscribeButton: {
    backgroundColor: Colors.accent,
    paddingVertical: Spacing.md,
    paddingHorizontal: Spacing.xl,
    borderRadius: Spacing.radiusMedium,
    width: '100%',
    alignItems: 'center',
    marginBottom: Spacing.sm,
  },
  subscribeButtonText: {
    color: Colors.background,
    fontSize: Typography.body,
    fontWeight: Typography.bold as any,
  },
  trialNote: {
    fontSize: Typography.caption,
    color: Colors.textLight,
    marginTop: Spacing.sm,
  },
});
