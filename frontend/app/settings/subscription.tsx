import React, { useEffect, useState } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  ScrollView, 
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  Linking,
  Platform
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { Card } from '../../components/Card';
import Colors from '../../constants/Colors';
import Spacing from '../../constants/Spacing';
import Typography from '../../constants/Typography';
import { useSubscriptionStore, useSubscriptionInfo } from '../../store/subscriptionStore';
import { useAuthStore } from '../../store/authStore';

export default function SubscriptionScreen() {
  const router = useRouter();
  const { user } = useAuthStore();
  const { 
    isLoading,
    isPremium,
    packages,
    currentOffering,
    error,
    configure,
    purchasePackage,
    restorePurchases,
    clearError,
    identifyUser
  } = useSubscriptionStore();
  
  // Get dynamic pricing info
  const { price, period, title, expirationDate } = useSubscriptionInfo();

  const [isRestoring, setIsRestoring] = useState(false);
  const [isInitializing, setIsInitializing] = useState(true);

  useEffect(() => {
    initializeSubscription();
  }, [user?.id]);

  const initializeSubscription = async () => {
    setIsInitializing(true);
    try {
      // Configure RevenueCat with user ID for tracking
      if (user?.id) {
        await identifyUser(user.id);
      } else {
        await configure();
      }
    } catch (e) {
      console.error('Subscription init error:', e);
    } finally {
      setIsInitializing(false);
    }
  };

  useEffect(() => {
    if (error) {
      Alert.alert('Subscription Error', error, [
        { text: 'OK', onPress: clearError }
      ]);
    }
  }, [error]);

  const handlePurchase = async () => {
    if (packages.length === 0) {
      Alert.alert(
        'No Products Available',
        'Subscription products are not available at this time. Please try again later.',
        [{ text: 'OK' }]
      );
      return;
    }

    // Find monthly package (or first available)
    const monthlyPackage = packages.find(p => 
      p.packageType === 'MONTHLY' || 
      p.identifier.toLowerCase().includes('monthly') ||
      p.identifier === '$rc_monthly'
    ) || packages[0];

    if (monthlyPackage) {
      const success = await purchasePackage(monthlyPackage);
      if (success) {
        Alert.alert(
          'Welcome to StyleFlow Pro!',
          'Thank you for subscribing! You now have access to all premium features.',
          [{ text: 'Continue', onPress: () => router.back() }]
        );
      }
    }
  };

  const handleRestore = async () => {
    setIsRestoring(true);
    const restored = await restorePurchases();
    setIsRestoring(false);

    if (restored) {
      Alert.alert(
        'Purchases Restored',
        'Your subscription has been restored successfully!',
        [{ text: 'Continue', onPress: () => router.back() }]
      );
    } else {
      Alert.alert(
        'No Purchases Found',
        'We couldn\'t find any previous purchases associated with your Apple ID. If you believe this is an error, please contact support.',
        [{ text: 'OK' }]
      );
    }
  };

  const openTerms = () => {
    Linking.openURL('https://dmmhc92-bot.github.io/style-flow-d/terms-of-service.html');
  };

  const openPrivacy = () => {
    Linking.openURL('https://dmmhc92-bot.github.io/style-flow-d/privacy-policy.html');
  };

  const openManageSubscription = () => {
    if (Platform.OS === 'ios') {
      Linking.openURL('https://apps.apple.com/account/subscriptions');
    } else {
      Linking.openURL('https://play.google.com/store/account/subscriptions');
    }
  };

  // Loading state while initializing
  if (isInitializing) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={styles.header}>
          <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
            <Ionicons name="close" size={24} color={Colors.text} />
          </TouchableOpacity>
          <Text style={styles.title}>StyleFlow Pro</Text>
          <View style={{ width: 40 }} />
        </View>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={Colors.accent} />
          <Text style={styles.loadingText}>Loading subscription options...</Text>
        </View>
      </SafeAreaView>
    );
  }

  // Premium user management screen
  if (isPremium) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={styles.header}>
          <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
            <Ionicons name="arrow-back" size={24} color={Colors.text} />
          </TouchableOpacity>
          <Text style={styles.title}>StyleFlow Pro</Text>
          <View style={{ width: 40 }} />
        </View>
        
        <ScrollView contentContainerStyle={styles.scrollContent}>
          <View style={styles.premiumBadge}>
            <Ionicons name="diamond" size={48} color={Colors.vip} />
            <Text style={styles.premiumTitle}>You're a Pro!</Text>
            <Text style={styles.premiumSubtitle}>
              Thank you for your subscription
            </Text>
          </View>

          <Card style={styles.statusCard}>
            <View style={styles.statusRow}>
              <Ionicons name="checkmark-circle" size={24} color={Colors.success} />
              <Text style={styles.statusText}>Premium Active</Text>
            </View>
            {expirationDate && (
              <Text style={styles.statusDetail}>
                Renews on {expirationDate.toLocaleDateString()}
              </Text>
            )}
          </Card>

          <View style={styles.premiumFeatures}>
            <Text style={styles.featuresTitle}>Your Premium Benefits:</Text>
            {[
              'Unlimited clients',
              'Advanced analytics',
              'AI Assistant (unlimited)',
              'Priority support',
              'Custom branding',
              'Data export'
            ].map((feature, index) => (
              <View key={index} style={styles.feature}>
                <Ionicons name="checkmark-circle" size={24} color={Colors.success} />
                <Text style={styles.featureText}>{feature}</Text>
              </View>
            ))}
          </View>

          <TouchableOpacity 
            style={styles.manageButton} 
            onPress={openManageSubscription}
          >
            <Text style={styles.manageButtonText}>Manage Subscription</Text>
          </TouchableOpacity>

          <View style={styles.footer}>
            <TouchableOpacity onPress={openTerms}>
              <Text style={styles.footerLink}>Terms of Service</Text>
            </TouchableOpacity>
            <Text style={styles.footerDivider}>•</Text>
            <TouchableOpacity onPress={openPrivacy}>
              <Text style={styles.footerLink}>Privacy Policy</Text>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </SafeAreaView>
    );
  }

  // Display price from RevenueCat or fallback to configured price
  const displayPrice = price || '$12.99';
  const displayPeriod = period || 'month';

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Ionicons name="close" size={24} color={Colors.text} />
        </TouchableOpacity>
        <Text style={styles.title}>StyleFlow Pro</Text>
        <View style={{ width: 40 }} />
      </View>
      
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Hero Section */}
        <View style={styles.heroSection}>
          <View style={styles.proIcon}>
            <Ionicons name="diamond" size={64} color={Colors.vip} />
          </View>
          <Text style={styles.heroTitle}>Upgrade to Pro</Text>
          <Text style={styles.heroSubtitle}>
            Unlock the full power of StyleFlow
          </Text>
        </View>
        
        {/* Price Card - Dynamic from RevenueCat */}
        <Card style={styles.priceCard}>
          <View style={styles.priceRow}>
            <Text style={styles.priceAmount}>{displayPrice}</Text>
            <Text style={styles.pricePeriod}>/{displayPeriod}</Text>
          </View>
          <Text style={styles.priceNote}>
            Cancel anytime • Auto-renews {displayPeriod}ly
          </Text>
        </Card>
        
        {/* Features List */}
        <View style={styles.featuresSection}>
          <Text style={styles.featuresTitle}>Premium Features Include:</Text>
          
          {[
            { icon: 'people', text: 'Unlimited clients', desc: 'No limits on your client base' },
            { icon: 'analytics', text: 'Advanced analytics', desc: 'Deep insights into your business' },
            { icon: 'chatbubble-ellipses', text: 'AI Assistant (unlimited)', desc: 'Get help anytime, no limits' },
            { icon: 'headset', text: 'Priority support', desc: '24/7 dedicated support team' },
            { icon: 'color-palette', text: 'Custom branding', desc: 'Personalize your experience' },
            { icon: 'download', text: 'Export data', desc: 'Download all your data anytime' },
          ].map((feature, index) => (
            <View key={index} style={styles.featureItem}>
              <View style={styles.featureIconContainer}>
                <Ionicons name={feature.icon as any} size={24} color={Colors.accent} />
              </View>
              <View style={styles.featureContent}>
                <Text style={styles.featureText}>{feature.text}</Text>
                <Text style={styles.featureDesc}>{feature.desc}</Text>
              </View>
            </View>
          ))}
        </View>
        
        {/* Subscribe Button */}
        <TouchableOpacity
          style={[styles.subscribeButton, (isLoading || packages.length === 0) && styles.buttonDisabled]}
          onPress={handlePurchase}
          disabled={isLoading || packages.length === 0}
        >
          {isLoading ? (
            <ActivityIndicator color={Colors.background} />
          ) : (
            <>
              <Ionicons name="diamond" size={20} color={Colors.background} />
              <Text style={styles.subscribeButtonText}>
                {packages.length === 0 ? 'Loading...' : 'Subscribe Now'}
              </Text>
            </>
          )}
        </TouchableOpacity>

        {/* Restore Purchases */}
        <TouchableOpacity
          style={styles.restoreButton}
          onPress={handleRestore}
          disabled={isRestoring || isLoading}
        >
          {isRestoring ? (
            <ActivityIndicator size="small" color={Colors.accent} />
          ) : (
            <Text style={styles.restoreButtonText}>Restore Purchases</Text>
          )}
        </TouchableOpacity>

        {/* Terms & Privacy - Required for App Store */}
        <View style={styles.legalSection}>
          <Text style={styles.legalText}>
            By subscribing, you agree to our{' '}
            <Text style={styles.legalLink} onPress={openTerms}>
              Terms of Service
            </Text>
            {' '}and{' '}
            <Text style={styles.legalLink} onPress={openPrivacy}>
              Privacy Policy
            </Text>
          </Text>
          <Text style={styles.legalSmall}>
            Payment will be charged to your {Platform.OS === 'ios' ? 'Apple ID' : 'Google Play'} account at confirmation of purchase.
            Subscription automatically renews unless cancelled at least 24 hours before
            the end of the current period. Your account will be charged for renewal within
            24 hours prior to the end of the current period.
          </Text>
        </View>
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
    fontWeight: Typography.semibold as any,
    color: Colors.text,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: Spacing.md,
    fontSize: Typography.body,
    color: Colors.textSecondary,
  },
  scrollContent: {
    padding: Spacing.screenPadding,
    paddingBottom: Spacing.xxl,
  },
  heroSection: {
    alignItems: 'center',
    paddingVertical: Spacing.xl,
  },
  proIcon: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: Colors.vip + '15',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.md,
  },
  heroTitle: {
    fontSize: Typography.h1,
    fontWeight: Typography.bold as any,
    color: Colors.text,
    marginTop: Spacing.sm,
  },
  heroSubtitle: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
    marginTop: Spacing.xs,
    textAlign: 'center',
  },
  priceCard: {
    alignItems: 'center',
    paddingVertical: Spacing.xl,
    marginVertical: Spacing.lg,
    backgroundColor: Colors.accent + '10',
    borderWidth: 2,
    borderColor: Colors.accent,
  },
  priceRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
  },
  priceAmount: {
    fontSize: 48,
    fontWeight: Typography.bold as any,
    color: Colors.accent,
  },
  pricePeriod: {
    fontSize: Typography.h3,
    color: Colors.textSecondary,
    marginLeft: 4,
  },
  priceNote: {
    fontSize: Typography.bodySmall,
    color: Colors.textLight,
    marginTop: Spacing.sm,
  },
  featuresSection: {
    marginBottom: Spacing.xl,
  },
  featuresTitle: {
    fontSize: Typography.h4,
    fontWeight: Typography.semibold as any,
    color: Colors.text,
    marginBottom: Spacing.lg,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: Spacing.md,
  },
  featureIconContainer: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: Colors.accent + '15',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: Spacing.md,
  },
  featureContent: {
    flex: 1,
  },
  featureText: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold as any,
    color: Colors.text,
  },
  featureDesc: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  feature: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: Spacing.md,
  },
  subscribeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.accent,
    paddingVertical: Spacing.md,
    borderRadius: Spacing.radiusMedium,
    marginBottom: Spacing.md,
    gap: Spacing.sm,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  subscribeButtonText: {
    fontSize: Typography.body,
    fontWeight: Typography.bold as any,
    color: Colors.background,
  },
  restoreButton: {
    alignItems: 'center',
    paddingVertical: Spacing.md,
    marginBottom: Spacing.lg,
  },
  restoreButtonText: {
    fontSize: Typography.body,
    color: Colors.accent,
    fontWeight: Typography.medium as any,
  },
  legalSection: {
    alignItems: 'center',
    paddingTop: Spacing.md,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  legalText: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 20,
  },
  legalLink: {
    color: Colors.accent,
    textDecorationLine: 'underline',
  },
  legalSmall: {
    fontSize: 11,
    color: Colors.textLight,
    textAlign: 'center',
    marginTop: Spacing.sm,
    lineHeight: 16,
  },
  // Premium user styles
  premiumBadge: {
    alignItems: 'center',
    paddingVertical: Spacing.xl,
  },
  premiumTitle: {
    fontSize: Typography.h2,
    fontWeight: Typography.bold as any,
    color: Colors.vip,
    marginTop: Spacing.md,
  },
  premiumSubtitle: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
    marginTop: Spacing.xs,
  },
  statusCard: {
    padding: Spacing.lg,
    marginBottom: Spacing.xl,
    backgroundColor: Colors.success + '10',
    borderWidth: 1,
    borderColor: Colors.success + '30',
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: Spacing.sm,
  },
  statusText: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold as any,
    color: Colors.success,
    marginLeft: Spacing.sm,
  },
  statusDetail: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    marginLeft: 32,
  },
  premiumFeatures: {
    marginBottom: Spacing.xl,
  },
  manageButton: {
    alignItems: 'center',
    paddingVertical: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: Spacing.radiusMedium,
    marginBottom: Spacing.xl,
  },
  manageButtonText: {
    fontSize: Typography.body,
    color: Colors.text,
    fontWeight: Typography.medium as any,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: Spacing.md,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  footerLink: {
    fontSize: Typography.bodySmall,
    color: Colors.accent,
  },
  footerDivider: {
    color: Colors.textLight,
    marginHorizontal: Spacing.sm,
  },
});
