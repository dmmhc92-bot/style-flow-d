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

export default function SupportScreen() {
  const router = useRouter();

  const handleEmailPress = () => {
    Linking.openURL(`mailto:${SUPPORT_EMAIL}?subject=StyleFlow Support Request`);
  };

  const supportTopics = [
    {
      icon: 'person-circle',
      title: 'Account Issues',
      description: 'Login problems, password reset, account settings',
    },
    {
      icon: 'bug',
      title: 'Report a Bug',
      description: 'Something not working correctly? Let us know',
    },
    {
      icon: 'bulb',
      title: 'Feature Request',
      description: 'Have an idea to improve StyleFlow?',
    },
    {
      icon: 'shield',
      title: 'Safety & Privacy',
      description: 'Report abuse, harassment, or privacy concerns',
    },
    {
      icon: 'card',
      title: 'Billing & Subscriptions',
      description: 'Questions about payments or premium features',
    },
    {
      icon: 'help-circle',
      title: 'General Help',
      description: 'Any other questions or feedback',
    },
  ];

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={24} color={Colors.text} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Support</Text>
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
            <Ionicons name="chatbubbles" size={40} color={Colors.accent} />
          </View>
          <Text style={styles.heroTitle}>How Can We Help?</Text>
          <Text style={styles.heroSubtitle}>
            We're here to support you. Reach out anytime.
          </Text>
        </View>

        {/* Primary Contact */}
        <TouchableOpacity style={styles.primaryContact} onPress={handleEmailPress}>
          <View style={styles.primaryContactIcon}>
            <Ionicons name="mail" size={28} color={Colors.buttonText} />
          </View>
          <View style={styles.primaryContactContent}>
            <Text style={styles.primaryContactTitle}>Email Support</Text>
            <Text style={styles.primaryContactEmail}>{SUPPORT_EMAIL}</Text>
            <Text style={styles.primaryContactHint}>Tap to send us an email</Text>
          </View>
          <Ionicons name="chevron-forward" size={20} color={Colors.buttonText} />
        </TouchableOpacity>

        {/* Response Time */}
        <View style={styles.responseTime}>
          <Ionicons name="time" size={18} color={Colors.accent} />
          <Text style={styles.responseTimeText}>
            We typically respond within 24-48 hours
          </Text>
        </View>

        {/* Support Topics */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>What do you need help with?</Text>
          <View style={styles.topicsGrid}>
            {supportTopics.map((topic, index) => (
              <TouchableOpacity
                key={index}
                style={styles.topicCard}
                onPress={() => Linking.openURL(`mailto:${SUPPORT_EMAIL}?subject=StyleFlow: ${topic.title}`)}
              >
                <View style={styles.topicIcon}>
                  <Ionicons name={topic.icon as any} size={24} color={Colors.accent} />
                </View>
                <Text style={styles.topicTitle}>{topic.title}</Text>
                <Text style={styles.topicDescription}>{topic.description}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* FAQ Hint */}
        <View style={styles.faqHint}>
          <Ionicons name="information-circle" size={20} color={Colors.info} />
          <Text style={styles.faqHintText}>
            When contacting support, please include details about your issue and any relevant screenshots to help us assist you faster.
          </Text>
        </View>

        {/* Quick Links */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Quick Links</Text>
          <TouchableOpacity 
            style={styles.quickLink}
            onPress={() => router.push('/privacy')}
          >
            <Ionicons name="shield-checkmark" size={20} color={Colors.accent} />
            <Text style={styles.quickLinkText}>Privacy Policy</Text>
            <Ionicons name="chevron-forward" size={18} color={Colors.textSecondary} />
          </TouchableOpacity>
          <TouchableOpacity 
            style={styles.quickLink}
            onPress={() => router.push('/terms')}
          >
            <Ionicons name="document-text" size={20} color={Colors.accent} />
            <Text style={styles.quickLinkText}>Terms of Service</Text>
            <Ionicons name="chevron-forward" size={18} color={Colors.textSecondary} />
          </TouchableOpacity>
          <TouchableOpacity 
            style={styles.quickLink}
            onPress={() => router.push('/settings/guidelines')}
          >
            <Ionicons name="people" size={20} color={Colors.accent} />
            <Text style={styles.quickLinkText}>Community Guidelines</Text>
            <Ionicons name="chevron-forward" size={18} color={Colors.textSecondary} />
          </TouchableOpacity>
        </View>

        <View style={styles.footer}>
          <Text style={styles.footerText}>StyleFlow v1.0.0</Text>
          <Text style={styles.footerSubtext}>Made with care for stylists everywhere</Text>
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
    fontSize: Typography.body,
    color: Colors.textSecondary,
    textAlign: 'center',
  },
  primaryContact: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.accent,
    padding: Spacing.lg,
    borderRadius: Spacing.radiusLarge,
    marginBottom: Spacing.md,
  },
  primaryContactIcon: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: 'rgba(0,0,0,0.15)',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: Spacing.md,
  },
  primaryContactContent: {
    flex: 1,
  },
  primaryContactTitle: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold,
    color: Colors.buttonText,
    marginBottom: 2,
  },
  primaryContactEmail: {
    fontSize: Typography.bodySmall,
    color: Colors.buttonText,
    opacity: 0.9,
  },
  primaryContactHint: {
    fontSize: Typography.caption,
    color: Colors.buttonText,
    opacity: 0.7,
    marginTop: 4,
  },
  responseTime: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: Spacing.sm,
    marginBottom: Spacing.xl,
  },
  responseTimeText: {
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
  topicsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginHorizontal: -Spacing.xs,
  },
  topicCard: {
    width: '50%',
    padding: Spacing.xs,
  },
  topicIcon: {
    width: 44,
    height: 44,
    borderRadius: 12,
    backgroundColor: Colors.accent + '15',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.sm,
  },
  topicTitle: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold,
    color: Colors.text,
    marginBottom: 4,
  },
  topicDescription: {
    fontSize: Typography.caption,
    color: Colors.textSecondary,
    lineHeight: 18,
  },
  faqHint: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: Colors.info + '10',
    padding: Spacing.md,
    borderRadius: Spacing.radiusMedium,
    marginBottom: Spacing.xl,
    gap: Spacing.sm,
  },
  faqHintText: {
    flex: 1,
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    lineHeight: 20,
  },
  quickLink: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.backgroundSecondary,
    padding: Spacing.md,
    borderRadius: Spacing.radiusMedium,
    marginBottom: Spacing.sm,
  },
  quickLinkText: {
    flex: 1,
    fontSize: Typography.body,
    color: Colors.text,
    marginLeft: Spacing.sm,
  },
  footer: {
    alignItems: 'center',
    marginTop: Spacing.lg,
    paddingTop: Spacing.lg,
    borderTopWidth: 1,
    borderTopColor: Colors.border,
  },
  footerText: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    fontWeight: Typography.medium,
  },
  footerSubtext: {
    fontSize: Typography.caption,
    color: Colors.textLight,
    marginTop: 4,
  },
});
