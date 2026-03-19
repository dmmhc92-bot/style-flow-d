import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { Card } from '../../components/Card';
import Colors from '../../constants/Colors';
import Spacing from '../../constants/Spacing';
import Typography from '../../constants/Typography';

export default function SubscriptionScreen() {
  const router = useRouter();
  
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
        <View style={styles.heroSection}>
          <Ionicons name="diamond" size={64} color={Colors.vip} />
          <Text style={styles.heroTitle}>Upgrade to Pro</Text>
          <Text style={styles.heroSubtitle}>Unlock premium features</Text>
        </View>
        
        <Card style={styles.priceCard}>
          <Text style={styles.priceAmount}>$12</Text>
          <Text style={styles.pricePeriod}>/month</Text>
          <Text style={styles.priceNote}>Cancel anytime</Text>
        </Card>
        
        <View style={styles.featuresSection}>
          <Text style={styles.featuresTitle}>Premium Features:</Text>
          
          <View style={styles.feature}>
            <Ionicons name="checkmark-circle" size={24} color={Colors.success} />
            <Text style={styles.featureText}>Unlimited clients</Text>
          </View>
          
          <View style={styles.feature}>
            <Ionicons name="checkmark-circle" size={24} color={Colors.success} />
            <Text style={styles.featureText}>Advanced analytics</Text>
          </View>
          
          <View style={styles.feature}>
            <Ionicons name="checkmark-circle" size={24} color={Colors.success} />
            <Text style={styles.featureText}>AI Assistant with unlimited queries</Text>
          </View>
          
          <View style={styles.feature}>
            <Ionicons name="checkmark-circle" size={24} color={Colors.success} />
            <Text style={styles.featureText}>Priority support</Text>
          </View>
        </View>
        
        <Text style={styles.note}>
          Note: This is a demo. Subscription requires Apple IAP / RevenueCat integration for production.
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
    fontWeight: Typography.semibold,
    color: Colors.text,
  },
  scrollContent: {
    padding: Spacing.screenPadding,
  },
  heroSection: {
    alignItems: 'center',
    paddingVertical: Spacing.xxl,
  },
  heroTitle: {
    fontSize: Typography.h1,
    fontWeight: Typography.bold,
    color: Colors.text,
    marginTop: Spacing.md,
  },
  heroSubtitle: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
    marginTop: Spacing.xs,
  },
  priceCard: {
    alignItems: 'center',
    paddingVertical: Spacing.xl,
    marginBottom: Spacing.xl,
    backgroundColor: Colors.accent + '10',
    borderWidth: 2,
    borderColor: Colors.accent,
  },
  priceAmount: {
    fontSize: 56,
    fontWeight: Typography.bold,
    color: Colors.accent,
  },
  pricePeriod: {
    fontSize: Typography.h3,
    color: Colors.textSecondary,
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
    fontWeight: Typography.semibold,
    color: Colors.text,
    marginBottom: Spacing.lg,
  },
  feature: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: Spacing.md,
  },
  featureText: {
    fontSize: Typography.body,
    color: Colors.text,
    marginLeft: Spacing.md,
  },
  note: {
    fontSize: Typography.bodySmall,
    color: Colors.textLight,
    textAlign: 'center',
    fontStyle: 'italic',
  },
});