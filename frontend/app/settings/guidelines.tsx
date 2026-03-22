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
import { Card } from '../../components/Card';
import Colors from '../../constants/Colors';
import Spacing from '../../constants/Spacing';
import Typography from '../../constants/Typography';

interface GuidelineSection {
  icon: string;
  title: string;
  rules: string[];
  color: string;
}

const GUIDELINES: GuidelineSection[] = [
  {
    icon: 'heart-outline',
    title: 'Respect & Kindness',
    color: Colors.success,
    rules: [
      'Treat all community members with respect and professionalism',
      'No harassment, bullying, intimidation, or personal attacks',
      'No discriminatory language based on race, gender, religion, or identity',
      'Support and uplift fellow stylists in the community',
    ],
  },
  {
    icon: 'ban-outline',
    title: 'Prohibited Content',
    color: Colors.error,
    rules: [
      'No sexual, explicit, or adult content of any kind',
      'No nudity or sexually suggestive imagery',
      'No violent, graphic, or disturbing content',
      'No promotion of dangerous activities or substances',
    ],
  },
  {
    icon: 'shield-outline',
    title: 'Safety & Legality',
    color: Colors.warning,
    rules: [
      'No illegal activities or promotion of illegal services',
      'No threats, doxxing, or sharing of private information',
      'No scams, fraud, or deceptive practices',
      'No impersonation of other stylists or businesses',
    ],
  },
  {
    icon: 'briefcase-outline',
    title: 'Professional Standards',
    color: Colors.info,
    rules: [
      'Share only hairstyling and professional beauty content',
      'Be honest about your credentials and experience',
      'Respect client confidentiality in all posts',
      'No spam, excessive self-promotion, or misleading claims',
    ],
  },
];

const ENFORCEMENT_LEVELS = [
  {
    level: 'Warning',
    description: 'First-time or minor violations receive a warning with explanation.',
    icon: 'alert-circle-outline',
    color: '#FFCC00',
  },
  {
    level: 'Restriction',
    description: 'Repeated warnings may limit certain features temporarily.',
    icon: 'lock-closed-outline',
    color: '#FF9500',
  },
  {
    level: 'Suspension',
    description: 'Serious violations result in temporary account suspension (7-30 days).',
    icon: 'time-outline',
    color: '#FF6B6B',
  },
  {
    level: 'Permanent Ban',
    description: 'Severe or repeated violations result in permanent account removal.',
    icon: 'close-circle-outline',
    color: '#FF3B30',
  },
];

export default function CommunityGuidelinesScreen() {
  const router = useRouter();

  const renderGuidelineSection = (section: GuidelineSection, index: number) => (
    <Card key={index} style={styles.guidelineCard}>
      <View style={styles.guidelineHeader}>
        <View style={[styles.iconContainer, { backgroundColor: section.color + '20' }]}>
          <Ionicons name={section.icon as any} size={24} color={section.color} />
        </View>
        <Text style={styles.guidelineTitle}>{section.title}</Text>
      </View>
      <View style={styles.rulesList}>
        {section.rules.map((rule, ruleIndex) => (
          <View key={ruleIndex} style={styles.ruleItem}>
            <View style={[styles.ruleBullet, { backgroundColor: section.color }]} />
            <Text style={styles.ruleText}>{rule}</Text>
          </View>
        ))}
      </View>
    </Card>
  );

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color={Colors.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Community Guidelines</Text>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Hero Section */}
        <View style={styles.heroSection}>
          <View style={styles.heroIcon}>
            <Ionicons name="shield-checkmark" size={48} color={Colors.accent} />
          </View>
          <Text style={styles.heroTitle}>Our Community Standards</Text>
          <Text style={styles.heroSubtitle}>
            StyleFlow is a professional community for hairstylists. We're committed
            to maintaining a safe, respectful, and inspiring space for all members.
          </Text>
        </View>

        {/* Guidelines Sections */}
        <View style={styles.guidelinesContainer}>
          {GUIDELINES.map(renderGuidelineSection)}
        </View>

        {/* Enforcement Section */}
        <View style={styles.enforcementSection}>
          <Text style={styles.sectionTitle}>Enforcement Actions</Text>
          <Text style={styles.sectionSubtitle}>
            Violations are reviewed by our moderation team and may result in:
          </Text>
          
          {ENFORCEMENT_LEVELS.map((level, index) => (
            <View key={index} style={styles.enforcementItem}>
              <View style={[styles.enforcementIcon, { backgroundColor: level.color + '20' }]}>
                <Ionicons name={level.icon as any} size={20} color={level.color} />
              </View>
              <View style={styles.enforcementContent}>
                <Text style={[styles.enforcementLevel, { color: level.color }]}>
                  {level.level}
                </Text>
                <Text style={styles.enforcementDesc}>{level.description}</Text>
              </View>
            </View>
          ))}
        </View>

        {/* Warning Banner */}
        <View style={styles.warningBanner}>
          <Ionicons name="warning" size={24} color={Colors.error} />
          <Text style={styles.warningText}>
            Severe violations including illegal activity, threats, or exploitation
            may be reported to law enforcement authorities.
          </Text>
        </View>

        {/* Reporting Info */}
        <Card style={styles.reportingCard}>
          <View style={styles.reportingHeader}>
            <Ionicons name="flag" size={20} color={Colors.accent} />
            <Text style={styles.reportingTitle}>See Something? Report It.</Text>
          </View>
          <Text style={styles.reportingText}>
            Help us maintain community safety by reporting violations. Reports are
            confidential and reviewed within 24-48 hours.
          </Text>
          <Text style={styles.reportingNote}>
            Note: False or malicious reporting may result in action against your account.
          </Text>
        </Card>

        {/* Last Updated */}
        <Text style={styles.lastUpdated}>
          Last updated: March 2026
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
  headerTitle: {
    fontSize: Typography.h4,
    fontWeight: Typography.bold,
    color: Colors.text,
  },
  scrollContent: {
    padding: Spacing.screenPadding,
    paddingBottom: Spacing.xxl,
  },
  heroSection: {
    alignItems: 'center',
    paddingVertical: Spacing.xl,
  },
  heroIcon: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: Colors.accent + '20',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.md,
  },
  heroTitle: {
    fontSize: Typography.h2,
    fontWeight: Typography.bold,
    color: Colors.text,
    marginBottom: Spacing.sm,
    textAlign: 'center',
  },
  heroSubtitle: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 22,
  },
  guidelinesContainer: {
    gap: Spacing.md,
  },
  guidelineCard: {
    padding: Spacing.md,
  },
  guidelineHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: Spacing.md,
    gap: Spacing.sm,
  },
  iconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  guidelineTitle: {
    fontSize: Typography.h4,
    fontWeight: Typography.semibold,
    color: Colors.text,
  },
  rulesList: {
    gap: Spacing.sm,
  },
  ruleItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: Spacing.sm,
  },
  ruleBullet: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginTop: 7,
  },
  ruleText: {
    flex: 1,
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    lineHeight: 20,
  },
  enforcementSection: {
    marginTop: Spacing.xl,
    marginBottom: Spacing.lg,
  },
  sectionTitle: {
    fontSize: Typography.h3,
    fontWeight: Typography.bold,
    color: Colors.text,
    marginBottom: Spacing.xs,
  },
  sectionSubtitle: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
    marginBottom: Spacing.md,
  },
  enforcementItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    paddingVertical: Spacing.sm,
    gap: Spacing.md,
  },
  enforcementIcon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
  },
  enforcementContent: {
    flex: 1,
  },
  enforcementLevel: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold,
    marginBottom: 2,
  },
  enforcementDesc: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    lineHeight: 18,
  },
  warningBanner: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: Colors.error + '15',
    borderRadius: 12,
    padding: Spacing.md,
    gap: Spacing.sm,
    marginBottom: Spacing.lg,
    borderWidth: 1,
    borderColor: Colors.error + '30',
  },
  warningText: {
    flex: 1,
    fontSize: Typography.bodySmall,
    color: Colors.text,
    lineHeight: 20,
    fontWeight: Typography.medium,
  },
  reportingCard: {
    backgroundColor: Colors.accent + '10',
    borderWidth: 1,
    borderColor: Colors.accent + '30',
  },
  reportingHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
    marginBottom: Spacing.sm,
  },
  reportingTitle: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold,
    color: Colors.accent,
  },
  reportingText: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    lineHeight: 20,
    marginBottom: Spacing.sm,
  },
  reportingNote: {
    fontSize: Typography.caption,
    color: Colors.textLight,
    fontStyle: 'italic',
  },
  lastUpdated: {
    fontSize: Typography.caption,
    color: Colors.textLight,
    textAlign: 'center',
    marginTop: Spacing.xl,
  },
});
