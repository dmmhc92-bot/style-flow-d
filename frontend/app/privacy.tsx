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

export default function PrivacyPolicyScreen() {
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
        <Text style={styles.headerTitle}>Privacy Policy</Text>
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
            <Ionicons name="shield-checkmark" size={40} color={Colors.accent} />
          </View>
          <Text style={styles.heroTitle}>Your Privacy Matters</Text>
          <Text style={styles.heroSubtitle}>Last updated: {LAST_UPDATED}</Text>
        </View>

        {/* Introduction */}
        <View style={styles.section}>
          <Text style={styles.paragraph}>
            StyleFlow ("we", "our", or "us") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, and safeguard your information when you use our mobile application.
          </Text>
        </View>

        {/* Data Collection */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Information We Collect</Text>
          
          <View style={styles.subsection}>
            <Text style={styles.subsectionTitle}>Account Information</Text>
            <Text style={styles.paragraph}>
              When you create an account, we collect your email address, name, and password (encrypted). You may optionally provide a profile photo, business name, bio, and location.
            </Text>
          </View>

          <View style={styles.subsection}>
            <Text style={styles.subsectionTitle}>Content You Create</Text>
            <Text style={styles.paragraph}>
              We store content you create including client records, appointments, formulas, gallery images, posts, and comments. This data is essential for the app's core functionality.
            </Text>
          </View>

          <View style={styles.subsection}>
            <Text style={styles.subsectionTitle}>Usage Data</Text>
            <Text style={styles.paragraph}>
              We collect anonymous usage data to improve our services, including app interactions, feature usage patterns, and performance metrics.
            </Text>
          </View>
        </View>

        {/* Data Usage */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>How We Use Your Data</Text>
          <View style={styles.bulletList}>
            <View style={styles.bulletItem}>
              <View style={styles.bullet} />
              <Text style={styles.bulletText}>Provide and maintain our services</Text>
            </View>
            <View style={styles.bulletItem}>
              <View style={styles.bullet} />
              <Text style={styles.bulletText}>Personalize your experience</Text>
            </View>
            <View style={styles.bulletItem}>
              <View style={styles.bullet} />
              <Text style={styles.bulletText}>Send important account notifications</Text>
            </View>
            <View style={styles.bulletItem}>
              <View style={styles.bullet} />
              <Text style={styles.bulletText}>Improve app performance and features</Text>
            </View>
            <View style={styles.bulletItem}>
              <View style={styles.bullet} />
              <Text style={styles.bulletText}>Ensure platform safety and security</Text>
            </View>
          </View>
        </View>

        {/* Data Protection */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Data Protection</Text>
          <View style={styles.highlightBox}>
            <Ionicons name="lock-closed" size={24} color={Colors.accent} />
            <Text style={styles.highlightText}>
              We do NOT sell, trade, or rent your personal information to third parties. Your data is encrypted and stored securely.
            </Text>
          </View>
        </View>

        {/* User Rights */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Your Rights</Text>
          
          <View style={styles.rightCard}>
            <View style={styles.rightIcon}>
              <Ionicons name="eye" size={20} color={Colors.accent} />
            </View>
            <View style={styles.rightContent}>
              <Text style={styles.rightTitle}>Access Your Data</Text>
              <Text style={styles.rightDescription}>View all personal data we store about you</Text>
            </View>
          </View>

          <View style={styles.rightCard}>
            <View style={styles.rightIcon}>
              <Ionicons name="create" size={20} color={Colors.accent} />
            </View>
            <View style={styles.rightContent}>
              <Text style={styles.rightTitle}>Update Your Data</Text>
              <Text style={styles.rightDescription}>Correct or modify your personal information</Text>
            </View>
          </View>

          <View style={styles.rightCard}>
            <View style={styles.rightIcon}>
              <Ionicons name="download" size={20} color={Colors.accent} />
            </View>
            <View style={styles.rightContent}>
              <Text style={styles.rightTitle}>Export Your Data</Text>
              <Text style={styles.rightDescription}>Request a copy of your data</Text>
            </View>
          </View>

          <View style={styles.rightCard}>
            <View style={styles.rightIcon}>
              <Ionicons name="trash" size={20} color={Colors.error} />
            </View>
            <View style={styles.rightContent}>
              <Text style={styles.rightTitle}>Delete Your Account</Text>
              <Text style={styles.rightDescription}>Permanently delete your account and all associated data from Settings</Text>
            </View>
          </View>
        </View>

        {/* Third Party Services */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Third-Party Services</Text>
          <Text style={styles.paragraph}>
            We may use third-party services for analytics, authentication, and payment processing. These services have their own privacy policies governing the use of your information.
          </Text>
        </View>

        {/* Children's Privacy */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Children's Privacy</Text>
          <Text style={styles.paragraph}>
            StyleFlow is not intended for users under 13 years of age. We do not knowingly collect personal information from children under 13.
          </Text>
        </View>

        {/* Updates */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Policy Updates</Text>
          <Text style={styles.paragraph}>
            We may update this Privacy Policy from time to time. We will notify you of any changes by posting the new policy on this page and updating the "Last updated" date.
          </Text>
        </View>

        {/* Contact */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Contact Us</Text>
          <Text style={styles.paragraph}>
            If you have questions about this Privacy Policy or your personal data, please contact us:
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
  subsection: {
    marginBottom: Spacing.md,
  },
  subsectionTitle: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold,
    color: Colors.accent,
    marginBottom: Spacing.xs,
  },
  paragraph: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
    lineHeight: 24,
  },
  bulletList: {
    gap: Spacing.sm,
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
  highlightBox: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: Colors.accent + '10',
    padding: Spacing.md,
    borderRadius: Spacing.radiusMedium,
    borderLeftWidth: 3,
    borderLeftColor: Colors.accent,
    gap: Spacing.sm,
  },
  highlightText: {
    flex: 1,
    fontSize: Typography.body,
    color: Colors.text,
    lineHeight: 22,
    fontWeight: Typography.medium,
  },
  rightCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.backgroundSecondary,
    padding: Spacing.md,
    borderRadius: Spacing.radiusMedium,
    marginBottom: Spacing.sm,
  },
  rightIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: Colors.accent + '15',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: Spacing.md,
  },
  rightContent: {
    flex: 1,
  },
  rightTitle: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold,
    color: Colors.text,
    marginBottom: 2,
  },
  rightDescription: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
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
