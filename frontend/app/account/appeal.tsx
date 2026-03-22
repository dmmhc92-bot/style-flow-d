import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { Card } from '../../components/Card';
import Button from '../../components/Button';
import Colors from '../../constants/Colors';
import Spacing from '../../constants/Spacing';
import Typography from '../../constants/Typography';
import api from '../../utils/api';
import { useAuthStore } from '../../store/authStore';

interface AppealStatus {
  has_appeal: boolean;
  appeal?: {
    id: string;
    status: string;
    appeal_reason: string;
    admin_notes?: string;
    decision_at?: string;
    created_at?: string;
  };
}

const STATUS_CONFIG: Record<string, { color: string; icon: string; label: string }> = {
  pending: { color: '#FFCC00', icon: 'time-outline', label: 'Pending Review' },
  under_review: { color: Colors.info, icon: 'eye-outline', label: 'Under Review' },
  approved: { color: Colors.success, icon: 'checkmark-circle', label: 'Approved' },
  denied: { color: Colors.error, icon: 'close-circle', label: 'Denied' },
};

export default function AppealScreen() {
  const router = useRouter();
  const { user } = useAuthStore();
  
  const [appealStatus, setAppealStatus] = useState<AppealStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  
  const [reason, setReason] = useState('');
  const [additionalDetails, setAdditionalDetails] = useState('');
  
  useEffect(() => {
    checkAppealStatus();
  }, []);
  
  const checkAppealStatus = async () => {
    setLoading(true);
    try {
      const response = await api.get('/appeals/me');
      setAppealStatus(response.data);
    } catch (error) {
      console.error('Failed to check appeal status:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleSubmit = async () => {
    if (!reason.trim()) {
      Alert.alert('Required', 'Please provide a reason for your appeal.');
      return;
    }
    
    if (reason.trim().length < 50) {
      Alert.alert('Too Short', 'Please provide a more detailed explanation (at least 50 characters).');
      return;
    }
    
    setSubmitting(true);
    try {
      await api.post('/appeals', {
        reason: reason.trim(),
        additional_details: additionalDetails.trim() || null,
      });
      
      Alert.alert(
        'Appeal Submitted',
        'Your appeal has been submitted and will be reviewed by our moderation team. You will be notified of the decision.',
        [{ text: 'OK', onPress: checkAppealStatus }]
      );
    } catch (error: any) {
      Alert.alert(
        'Error',
        error.response?.data?.detail || 'Failed to submit appeal. Please try again.'
      );
    } finally {
      setSubmitting(false);
    }
  };
  
  if (loading) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={Colors.accent} />
          <Text style={styles.loadingText}>Checking appeal status...</Text>
        </View>
      </SafeAreaView>
    );
  }
  
  // Show existing appeal status
  if (appealStatus?.has_appeal && appealStatus.appeal) {
    const appeal = appealStatus.appeal;
    const statusConfig = STATUS_CONFIG[appeal.status] || STATUS_CONFIG.pending;
    
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={styles.header}>
          <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
            <Ionicons name="arrow-back" size={24} color={Colors.text} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Appeal Status</Text>
          <View style={{ width: 40 }} />
        </View>
        
        <ScrollView contentContainerStyle={styles.scrollContent}>
          {/* Status Card */}
          <View style={[styles.statusCard, { borderColor: statusConfig.color }]}>
            <View style={[styles.statusIcon, { backgroundColor: statusConfig.color + '20' }]}>
              <Ionicons name={statusConfig.icon as any} size={32} color={statusConfig.color} />
            </View>
            <Text style={[styles.statusLabel, { color: statusConfig.color }]}>
              {statusConfig.label}
            </Text>
            <Text style={styles.statusDate}>
              Submitted: {new Date(appeal.created_at || '').toLocaleDateString()}
            </Text>
          </View>
          
          {/* Your Appeal */}
          <Card style={styles.section}>
            <Text style={styles.sectionTitle}>Your Appeal</Text>
            <Text style={styles.appealText}>{appeal.appeal_reason}</Text>
          </Card>
          
          {/* Decision (if made) */}
          {appeal.status === 'approved' && (
            <View style={styles.decisionCard}>
              <Ionicons name="checkmark-circle" size={48} color={Colors.success} />
              <Text style={styles.decisionTitle}>Appeal Approved!</Text>
              <Text style={styles.decisionText}>
                Your account has been restored. You can now access all features.
              </Text>
              {appeal.admin_notes && (
                <View style={styles.adminNotes}>
                  <Text style={styles.adminNotesLabel}>Admin Notes:</Text>
                  <Text style={styles.adminNotesText}>{appeal.admin_notes}</Text>
                </View>
              )}
              <Button
                title="Return to App"
                onPress={() => router.replace('/tabs')}
                style={styles.returnButton}
              />
            </View>
          )}
          
          {appeal.status === 'denied' && (
            <View style={[styles.decisionCard, styles.deniedCard]}>
              <Ionicons name="close-circle" size={48} color={Colors.error} />
              <Text style={[styles.decisionTitle, { color: Colors.error }]}>Appeal Denied</Text>
              <Text style={styles.decisionText}>
                After careful review, your appeal has been denied. The original moderation action remains in effect.
              </Text>
              {appeal.admin_notes && (
                <View style={styles.adminNotes}>
                  <Text style={styles.adminNotesLabel}>Admin Notes:</Text>
                  <Text style={styles.adminNotesText}>{appeal.admin_notes}</Text>
                </View>
              )}
            </View>
          )}
          
          {(appeal.status === 'pending' || appeal.status === 'under_review') && (
            <Card style={styles.infoCard}>
              <Ionicons name="information-circle" size={20} color={Colors.info} />
              <Text style={styles.infoText}>
                Appeals are typically reviewed within 3-5 business days. You will be notified once a decision is made.
              </Text>
            </Card>
          )}
        </ScrollView>
      </SafeAreaView>
    );
  }
  
  // Show appeal form
  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={{ flex: 1 }}
      >
        <View style={styles.header}>
          <TouchableOpacity style={styles.backButton} onPress={() => router.back()}>
            <Ionicons name="arrow-back" size={24} color={Colors.text} />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Submit Appeal</Text>
          <View style={{ width: 40 }} />
        </View>
        
        <ScrollView contentContainerStyle={styles.scrollContent}>
          {/* Info Banner */}
          <View style={styles.infoBanner}>
            <Ionicons name="shield-checkmark" size={24} color={Colors.accent} />
            <View style={styles.infoBannerContent}>
              <Text style={styles.infoBannerTitle}>Appeal Process</Text>
              <Text style={styles.infoBannerText}>
                Your appeal will be reviewed by our moderation team. Please provide a clear and honest explanation.
              </Text>
            </View>
          </View>
          
          {/* Current Status */}
          <Card style={styles.currentStatusCard}>
            <Text style={styles.currentStatusLabel}>Current Status:</Text>
            <Text style={styles.currentStatusValue}>
              {user?.moderation_status === 'banned' ? 'Account Banned' :
               user?.moderation_status === 'suspended' ? 'Account Suspended' :
               user?.moderation_status === 'restricted' ? 'Account Restricted' :
               'Account Warning'}
            </Text>
            {user?.ban_reason || user?.suspension_reason || user?.last_warning_reason ? (
              <Text style={styles.currentReasonText}>
                Reason: {user?.ban_reason || user?.suspension_reason || user?.last_warning_reason}
              </Text>
            ) : null}
          </Card>
          
          {/* Appeal Form */}
          <View style={styles.formSection}>
            <Text style={styles.label}>
              Why should we reconsider? <Text style={styles.required}>*</Text>
            </Text>
            <TextInput
              style={styles.textArea}
              placeholder="Explain why you believe this action was incorrect or why you should be given another chance. Be specific and honest."
              placeholderTextColor={Colors.textLight}
              multiline
              numberOfLines={6}
              value={reason}
              onChangeText={setReason}
              maxLength={1000}
            />
            <Text style={styles.charCount}>{reason.length}/1000 (minimum 50)</Text>
            
            <Text style={[styles.label, styles.optionalLabel]}>
              Additional Context (Optional)
            </Text>
            <TextInput
              style={[styles.textArea, styles.smallTextArea]}
              placeholder="Any additional information that might help your case..."
              placeholderTextColor={Colors.textLight}
              multiline
              numberOfLines={3}
              value={additionalDetails}
              onChangeText={setAdditionalDetails}
              maxLength={500}
            />
            <Text style={styles.charCount}>{additionalDetails.length}/500</Text>
          </View>
          
          {/* Guidelines Notice */}
          <View style={styles.guidelinesNotice}>
            <Ionicons name="warning" size={18} color={Colors.warning} />
            <Text style={styles.guidelinesText}>
              Submitting false or misleading information in your appeal may result in immediate denial and further action against your account.
            </Text>
          </View>
          
          {/* Submit Button */}
          <Button
            title={submitting ? 'Submitting...' : 'Submit Appeal'}
            onPress={handleSubmit}
            disabled={submitting || reason.trim().length < 50}
            loading={submitting}
            style={styles.submitButton}
          />
          
          <Text style={styles.reviewTimeNote}>
            Appeals are typically reviewed within 3-5 business days.
          </Text>
        </ScrollView>
      </KeyboardAvoidingView>
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
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: Spacing.md,
  },
  loadingText: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
  },
  scrollContent: {
    padding: Spacing.screenPadding,
    paddingBottom: Spacing.xxl,
  },
  statusCard: {
    alignItems: 'center',
    backgroundColor: Colors.cardBackground,
    borderRadius: 16,
    padding: Spacing.xl,
    borderWidth: 2,
    marginBottom: Spacing.lg,
  },
  statusIcon: {
    width: 64,
    height: 64,
    borderRadius: 32,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.md,
  },
  statusLabel: {
    fontSize: Typography.h3,
    fontWeight: Typography.bold,
    marginBottom: Spacing.xs,
  },
  statusDate: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
  },
  section: {
    marginBottom: Spacing.md,
  },
  sectionTitle: {
    fontSize: Typography.h4,
    fontWeight: Typography.semibold,
    color: Colors.text,
    marginBottom: Spacing.sm,
  },
  appealText: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
    lineHeight: 22,
  },
  decisionCard: {
    alignItems: 'center',
    backgroundColor: Colors.success + '15',
    borderRadius: 16,
    padding: Spacing.xl,
    marginTop: Spacing.md,
    gap: Spacing.sm,
  },
  deniedCard: {
    backgroundColor: Colors.error + '15',
  },
  decisionTitle: {
    fontSize: Typography.h3,
    fontWeight: Typography.bold,
    color: Colors.success,
  },
  decisionText: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 22,
  },
  adminNotes: {
    width: '100%',
    marginTop: Spacing.md,
    padding: Spacing.md,
    backgroundColor: Colors.backgroundSecondary,
    borderRadius: 8,
  },
  adminNotesLabel: {
    fontSize: Typography.bodySmall,
    fontWeight: Typography.semibold,
    color: Colors.text,
    marginBottom: Spacing.xs,
  },
  adminNotesText: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    fontStyle: 'italic',
  },
  returnButton: {
    marginTop: Spacing.lg,
    minWidth: 200,
  },
  infoCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: Colors.info + '15',
    borderWidth: 1,
    borderColor: Colors.info + '30',
    gap: Spacing.sm,
    marginTop: Spacing.md,
  },
  infoText: {
    flex: 1,
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    lineHeight: 20,
  },
  infoBanner: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: Colors.accent + '15',
    borderRadius: 12,
    padding: Spacing.md,
    gap: Spacing.md,
    marginBottom: Spacing.lg,
  },
  infoBannerContent: {
    flex: 1,
  },
  infoBannerTitle: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold,
    color: Colors.accent,
    marginBottom: Spacing.xs,
  },
  infoBannerText: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    lineHeight: 20,
  },
  currentStatusCard: {
    backgroundColor: Colors.error + '15',
    borderWidth: 1,
    borderColor: Colors.error + '30',
    marginBottom: Spacing.lg,
  },
  currentStatusLabel: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    marginBottom: Spacing.xs,
  },
  currentStatusValue: {
    fontSize: Typography.h4,
    fontWeight: Typography.semibold,
    color: Colors.error,
  },
  currentReasonText: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    marginTop: Spacing.sm,
    fontStyle: 'italic',
  },
  formSection: {
    marginBottom: Spacing.lg,
  },
  label: {
    fontSize: Typography.body,
    fontWeight: Typography.semibold,
    color: Colors.text,
    marginBottom: Spacing.sm,
  },
  optionalLabel: {
    marginTop: Spacing.lg,
  },
  required: {
    color: Colors.error,
  },
  textArea: {
    backgroundColor: Colors.cardBackground,
    borderRadius: 12,
    padding: Spacing.md,
    fontSize: Typography.body,
    color: Colors.text,
    minHeight: 150,
    textAlignVertical: 'top',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  smallTextArea: {
    minHeight: 80,
  },
  charCount: {
    fontSize: Typography.caption,
    color: Colors.textLight,
    textAlign: 'right',
    marginTop: Spacing.xs,
  },
  guidelinesNotice: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: Colors.warning + '15',
    borderRadius: 12,
    padding: Spacing.md,
    gap: Spacing.sm,
    marginBottom: Spacing.xl,
  },
  guidelinesText: {
    flex: 1,
    fontSize: Typography.caption,
    color: Colors.textSecondary,
    lineHeight: 18,
  },
  submitButton: {
    marginBottom: Spacing.md,
  },
  reviewTimeNote: {
    fontSize: Typography.caption,
    color: Colors.textLight,
    textAlign: 'center',
  },
});
