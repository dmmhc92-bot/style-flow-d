import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Linking,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import Colors from '../constants/Colors';
import Spacing from '../constants/Spacing';
import Typography from '../constants/Typography';

const SUPPORT_EMAIL = 'styleflowsupport@gmail.com';
const LAST_UPDATED = 'March 23, 2025';

export default function TermsOfServiceScreen() {
  const router = useRouter();

  const handleEmailPress = () => {
    Linking.openURL(`mailto:${SUPPORT_EMAIL}`);
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color={Colors.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Terms of Service</Text>
        <View style={styles.placeholder} />
      </View>

      <ScrollView 
        style={styles.content} 
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
      >
        {/* Hero */}
        <View style={styles.hero}>
          <View style={styles.iconContainer}>
            <Ionicons name="document-text" size={40} color={Colors.accent} />
          </View>
          <Text style={styles.heroTitle}>Terms of Service</Text>
          <Text style={styles.heroSubtitle}>Last updated: {LAST_UPDATED}</Text>
        </View>

        {/* Acceptance */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>1. Acceptance of Terms</Text>
          <Text style={styles.paragraph}>
            By downloading, installing, or using StyleFlow ("App"), you agree to be bound by these Terms of Service ("Terms"). If you do not agree to these Terms, do not use the App.
          </Text>
        </View>

        {/* Eligibility */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>2. Eligibility</Text>
          <Text style={styles.paragraph}>
            You must be at least 13 years old to use StyleFlow. By using the App, you represent that you meet this age requirement and have the legal capacity to enter into these Terms.
          </Text>
        </View>

        {/* Account Responsibilities */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>3. Account Responsibilities</Text>
          <Text style={styles.paragraph}>As a user of StyleFlow, you agree to:</Text>
          <View style={styles.bulletList}>
            <View style={styles.bulletItem}>
              <View style={styles.bullet} />
              <Text style={styles.bulletText}>Provide accurate and complete information when creating your account</Text>
            </View>
            <View style={styles.bulletItem}>
              <View style={styles.bullet} />
              <Text style={styles.bulletText}>Maintain the security of your account credentials</Text>
            </View>
            <View style={styles.bulletItem}>
              <View style={styles.bullet} />
              <Text style={styles.bulletText}>Notify us immediately of any unauthorized access</Text>
            </View>
            <View style={styles.bulletItem}>
              <View style={styles.bullet} />
              <Text style={styles.bulletText}>Accept responsibility for all activities under your account</Text>
            </View>
          </View>
        </View>

        {/* Content Guidelines */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>4. Content Guidelines</Text>
          <Text style={styles.paragraph}>
            You retain ownership of content you create. However, by posting content on StyleFlow, you grant us a license to display it within the App. You agree NOT to post:
          </Text>
          <View style={styles.warningBox}>
            <View style={styles.warningItem}>
              <Ionicons name="close-circle" size={18} color={Colors.error} />
              <Text style={styles.warningText}>Illegal, harmful, or offensive content</Text>
            </View>
            <View style={styles.warningItem}>
              <Ionicons name="close-circle" size={18} color={Colors.error} />
              <Text style={styles.warningText}>Content that infringes intellectual property rights</Text>
            </View>
            <View style={styles.warningItem}>
              <Ionicons name="close-circle" size={18} color={Colors.error} />
              <Text style={styles.warningText}>Spam, misleading, or fraudulent content</Text>
            </View>
            <View style={styles.warningItem}>
              <Ionicons name="close-circle" size={18} color={Colors.error} />
              <Text style={styles.warningText}>Content that harasses or discriminates against others</Text>
            </View>
            <View style={styles.warningItem}>
              <Ionicons name="close-circle" size={18} color={Colors.error} />
              <Text style={styles.warningText}>Malicious software or harmful code</Text>
            </View>
          </View>
        </View>

        {/* Community Standards */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>5. Community Standards</Text>
          <Text style={styles.paragraph}>
            StyleFlow is a professional community for hair stylists. Users are expected to:
          </Text>
          <View style={styles.bulletList}>
            <View style={styles.bulletItem}>
              <View style={[styles.bullet, { backgroundColor: Colors.success }]} />
              <Text style={styles.bulletText}>Treat all community members with respect</Text>
            </View>
            <View style={styles.bulletItem}>
              <View style={[styles.bullet, { backgroundColor: Colors.success }]} />
              <Text style={styles.bulletText}>Share authentic, original work</Text>
            </View>
            <View style={styles.bulletItem}>
              <View style={[styles.bullet, { backgroundColor: Colors.success }]} />
              <Text style={styles.bulletText}>Provide constructive feedback</Text>
            </View>
            <View style={styles.bulletItem}>
              <View style={[styles.bullet, { backgroundColor: Colors.success }]} />
              <Text style={styles.bulletText}>Report violations of these guidelines</Text>
            </View>
          </View>
        </View>

        {/* Account Termination */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>6. Account Termination</Text>
          <View style={styles.highlightBox}>
            <Ionicons name="warning" size={24} color={Colors.warning} />
            <Text style={styles.highlightText}>
              We reserve the right to suspend or terminate accounts that violate these Terms, engage in fraudulent activity, or harm other users. Repeat violations will result in permanent bans.
            </Text>
          </View>
          <Text style={[styles.paragraph, { marginTop: Spacing.md }]}>
            You may delete your account at any time through the app settings. Upon deletion, all your data will be permanently removed from our servers.
          </Text>
        </View>

        {/* Subscriptions */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>7. Subscriptions & Payments</Text>
          <Text style={styles.paragraph}>
            StyleFlow may offer premium subscription features in the future. If subscriptions are introduced:
          </Text>
          <View style={styles.bulletList}>
            <View style={styles.bulletItem}>
              <View style={styles.bullet} />
              <Text style={styles.bulletText}>Pricing will be clearly displayed before purchase</Text>
            </View>
            <View style={styles.bulletItem}>
              <View style={styles.bullet} />
              <Text style={styles.bulletText}>Subscriptions auto-renew unless cancelled</Text>
            </View>
            <View style={styles.bulletItem}>
              <View style={styles.bullet} />
              <Text style={styles.bulletText}>Refunds are subject to App Store/Play Store policies</Text>
            </View>
            <View style={styles.bulletItem}>
              <View style={styles.bullet} />
              <Text style={styles.bulletText}>You can manage subscriptions through your device settings</Text>
            </View>
          </View>
        </View>

        {/* Intellectual Property */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>8. Intellectual Property</Text>
          <Text style={styles.paragraph}>
            StyleFlow and its original content, features, and functionality are owned by StyleFlow and protected by international copyright, trademark, and other intellectual property laws.
          </Text>
        </View>

        {/* Disclaimers */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>9. Disclaimers</Text>
          <Text style={styles.paragraph}>
            StyleFlow is provided "as is" without warranties of any kind. We do not guarantee that the App will be uninterrupted, secure, or error-free. Use of the App is at your own risk.
          </Text>
        </View>

        {/* Limitation of Liability */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>10. Limitation of Liability</Text>
          <Text style={styles.paragraph}>
            To the maximum extent permitted by law, StyleFlow shall not be liable for any indirect, incidental, special, consequential, or punitive damages arising from your use of the App.
          </Text>
        </View>

        {/* Changes to Terms */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>11. Changes to Terms</Text>
          <Text style={styles.paragraph}>
            We may update these Terms from time to time. Continued use of the App after changes constitutes acceptance of the new Terms. We will notify users of significant changes.
          </Text>
        </View>

        {/* Governing Law */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>12. Governing Law</Text>
          <Text style={styles.paragraph}>
            These Terms shall be governed by and construed in accordance with applicable laws, without regard to conflict of law principles.
          </Text>
        </View>

        {/* Contact */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>13. Contact Us</Text>
          <Text style={styles.paragraph}>
            If you have questions about these Terms, please contact us:
          </Text>
          <TouchableOpacity style={styles.contactButton} onPress={handleEmailPress}>
            <Ionicons name="mail" size={20} color={Colors.buttonText} />
            <Text style={styles.contactButtonText}>{SUPPORT_EMAIL}</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.footer}>
          <Text style={styles.footerText}>© 2025 StyleFlow. All rights reserved.</Text>
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
    alignItems: 'center',
    justifyContent: 'space-between',
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
    fontWeight: Typography.semibold,
    color: Colors.text,
  },
  placeholder: {
    width: 40,
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    padding: Spacing.screenPadding,
    paddingBottom: Spacing.xxl,
  },
  hero: {
    alignItems: 'center',
    marginBottom: Spacing.xl,
  },
  iconContainer: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: Colors.accent + '15',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.md,
  },
  heroTitle: {
    fontSize: Typography.h2,
    fontWeight: Typography.bold,
    color: Colors.text,
    marginBottom: Spacing.xs,
  },
  heroSubtitle: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
  },
  section: {
    marginBottom: Spacing.xl,
  },
  sectionTitle: {
    fontSize: Typography.h4,
    fontWeight: Typography.semibold,
    color: Colors.text,
    marginBottom: Spacing.md,
  },
  paragraph: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
    lineHeight: 24,
  },
  bulletList: {
    gap: Spacing.sm,
    marginTop: Spacing.sm,
  },
  bulletItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  bullet: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: Colors.accent,
    marginTop: 8,
    marginRight: Spacing.sm,
  },
  bulletText: {
    flex: 1,
    fontSize: Typography.body,
    color: Colors.textSecondary,
    lineHeight: 22,
  },
  warningBox: {
    backgroundColor: Colors.error + '10',
    padding: Spacing.md,
    borderRadius: Spacing.radiusMedium,
    marginTop: Spacing.sm,
    gap: Spacing.sm,
  },
  warningItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
  },
  warningText: {
    flex: 1,
    fontSize: Typography.body,
    color: Colors.textSecondary,
  },
  highlightBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: Colors.warning + '10',
    padding: Spacing.md,
    borderRadius: Spacing.radiusMedium,
    borderLeftWidth: 3,
    borderLeftColor: Colors.warning,
    gap: Spacing.sm,
  },
  highlightText: {
    flex: 1,
    fontSize: Typography.body,
    color: Colors.text,
    lineHeight: 22,
  },
  contactButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.accent,
    paddingVertical: Spacing.md,
    paddingHorizontal: Spacing.lg,
    borderRadius: Spacing.radiusMedium,
    marginTop: Spacing.md,
    gap: Spacing.sm,
  },
  contactButtonText: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold,
    color: Colors.buttonText,
  },
  footer: {
    alignItems: 'center',
    marginTop: Spacing.xl,
    paddingTop: Spacing.lg,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  footerText: {
    fontSize: Typography.caption,
    color: Colors.textLight,
  },
});
