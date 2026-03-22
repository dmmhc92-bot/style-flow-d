import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TouchableOpacity,
  ScrollView,
  TextInput,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import Colors from '../constants/Colors';
import Spacing from '../constants/Spacing';
import Typography from '../constants/Typography';
import { Button } from './Button';
import api from '../utils/api';

interface ReportModalProps {
  visible: boolean;
  onClose: () => void;
  reportedUserId: string;
  reportedUserName?: string;
  contentType?: 'profile' | 'portfolio' | 'gallery';
  contentId?: string;
}

const REPORT_REASONS = [
  { id: 'harassment', label: 'Harassment or Bullying', icon: 'warning-outline' },
  { id: 'inappropriate', label: 'Inappropriate Content', icon: 'eye-off-outline' },
  { id: 'spam', label: 'Spam or Scam', icon: 'mail-unread-outline' },
  { id: 'hate_speech', label: 'Hate Speech', icon: 'megaphone-outline' },
  { id: 'sexual_content', label: 'Sexual Content', icon: 'ban-outline' },
  { id: 'illegal', label: 'Illegal Activity', icon: 'alert-circle-outline' },
  { id: 'impersonation', label: 'Impersonation', icon: 'person-outline' },
  { id: 'other', label: 'Other', icon: 'ellipsis-horizontal-outline' },
];

export function ReportModal({
  visible,
  onClose,
  reportedUserId,
  reportedUserName,
  contentType = 'profile',
  contentId,
}: ReportModalProps) {
  const [selectedReason, setSelectedReason] = useState<string | null>(null);
  const [details, setDetails] = useState('');
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState<'reason' | 'details'>('reason');

  const handleSubmit = async () => {
    if (!selectedReason) return;

    setLoading(true);
    try {
      await api.post('/report', {
        reported_user_id: reportedUserId,
        content_type: contentType,
        content_id: contentId,
        reason: selectedReason,
        details: details.trim() || null,
      });

      Alert.alert(
        'Report Submitted',
        'Thank you for helping keep our community safe. We will review this report within 24-48 hours.',
        [{ text: 'OK', onPress: handleClose }]
      );
    } catch (error: any) {
      Alert.alert(
        'Error',
        error.response?.data?.detail || 'Failed to submit report. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setSelectedReason(null);
    setDetails('');
    setStep('reason');
    onClose();
  };

  const handleReasonSelect = (reasonId: string) => {
    setSelectedReason(reasonId);
    setStep('details');
  };

  const handleBack = () => {
    setStep('reason');
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      transparent={true}
      onRequestClose={handleClose}
    >
      <View style={styles.overlay}>
        <View style={styles.container}>
          {/* Header */}
          <View style={styles.header}>
            {step === 'details' && (
              <TouchableOpacity onPress={handleBack} style={styles.backButton}>
                <Ionicons name="arrow-back" size={24} color={Colors.text} />
              </TouchableOpacity>
            )}
            <Text style={styles.title}>
              {step === 'reason' ? 'Report' : 'Additional Details'}
            </Text>
            <TouchableOpacity onPress={handleClose} style={styles.closeButton}>
              <Ionicons name="close" size={24} color={Colors.textSecondary} />
            </TouchableOpacity>
          </View>

          {step === 'reason' ? (
            <>
              {/* Info */}
              <View style={styles.infoSection}>
                <Ionicons name="shield-checkmark" size={32} color={Colors.accent} />
                <Text style={styles.infoText}>
                  Help us keep StyleFlow safe. Select a reason for reporting
                  {reportedUserName ? ` ${reportedUserName}` : ''}.
                </Text>
              </View>

              {/* Reasons List */}
              <ScrollView style={styles.reasonsList}>
                {REPORT_REASONS.map((reason) => (
                  <TouchableOpacity
                    key={reason.id}
                    style={[
                      styles.reasonItem,
                      selectedReason === reason.id && styles.reasonItemSelected,
                    ]}
                    onPress={() => handleReasonSelect(reason.id)}
                  >
                    <View style={styles.reasonIcon}>
                      <Ionicons
                        name={reason.icon as any}
                        size={24}
                        color={Colors.accent}
                      />
                    </View>
                    <Text style={styles.reasonLabel}>{reason.label}</Text>
                    <Ionicons
                      name="chevron-forward"
                      size={20}
                      color={Colors.textSecondary}
                    />
                  </TouchableOpacity>
                ))}
              </ScrollView>
            </>
          ) : (
            <>
              {/* Selected Reason */}
              <View style={styles.selectedReasonBadge}>
                <Text style={styles.selectedReasonText}>
                  {REPORT_REASONS.find((r) => r.id === selectedReason)?.label}
                </Text>
              </View>

              {/* Details Input */}
              <View style={styles.detailsSection}>
                <Text style={styles.detailsLabel}>
                  Please provide additional details (optional)
                </Text>
                <TextInput
                  style={styles.detailsInput}
                  placeholder="Describe what happened..."
                  placeholderTextColor={Colors.textLight}
                  multiline
                  numberOfLines={4}
                  value={details}
                  onChangeText={setDetails}
                  maxLength={500}
                />
                <Text style={styles.charCount}>{details.length}/500</Text>
              </View>

              {/* Community Guidelines */}
              <View style={styles.guidelinesSection}>
                <Ionicons name="information-circle" size={20} color={Colors.info} />
                <Text style={styles.guidelinesText}>
                  False reports may result in action against your account. Only report
                  genuine violations of our community guidelines.
                </Text>
              </View>

              {/* Submit Button */}
              <View style={styles.submitSection}>
                <Button
                  title={loading ? 'Submitting...' : 'Submit Report'}
                  onPress={handleSubmit}
                  disabled={loading}
                />
              </View>
            </>
          )}
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: Colors.overlay,
    justifyContent: 'flex-end',
  },
  container: {
    backgroundColor: Colors.background,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    maxHeight: '90%',
    paddingBottom: Spacing.xxl,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: Spacing.md,
    paddingHorizontal: Spacing.screenPadding,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  backButton: {
    position: 'absolute',
    left: Spacing.screenPadding,
    padding: Spacing.xs,
  },
  closeButton: {
    position: 'absolute',
    right: Spacing.screenPadding,
    padding: Spacing.xs,
  },
  title: {
    fontSize: Typography.h4,
    fontWeight: Typography.semibold,
    color: Colors.text,
  },
  infoSection: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: Spacing.screenPadding,
    backgroundColor: Colors.backgroundSecondary,
    marginHorizontal: Spacing.screenPadding,
    marginTop: Spacing.md,
    borderRadius: 12,
    gap: Spacing.md,
  },
  infoText: {
    flex: 1,
    fontSize: Typography.body,
    color: Colors.textSecondary,
    lineHeight: 22,
  },
  reasonsList: {
    marginTop: Spacing.md,
    paddingHorizontal: Spacing.screenPadding,
  },
  reasonItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: Spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border,
  },
  reasonItemSelected: {
    backgroundColor: Colors.accent + '10',
  },
  reasonIcon: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: Colors.accent + '15',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: Spacing.md,
  },
  reasonLabel: {
    flex: 1,
    fontSize: Typography.body,
    color: Colors.text,
    fontWeight: Typography.medium,
  },
  selectedReasonBadge: {
    backgroundColor: Colors.accent + '20',
    paddingVertical: Spacing.sm,
    paddingHorizontal: Spacing.md,
    borderRadius: 20,
    alignSelf: 'flex-start',
    marginHorizontal: Spacing.screenPadding,
    marginTop: Spacing.md,
  },
  selectedReasonText: {
    fontSize: Typography.bodySmall,
    color: Colors.accent,
    fontWeight: Typography.semibold,
  },
  detailsSection: {
    padding: Spacing.screenPadding,
  },
  detailsLabel: {
    fontSize: Typography.body,
    color: Colors.text,
    marginBottom: Spacing.sm,
  },
  detailsInput: {
    backgroundColor: Colors.backgroundSecondary,
    borderRadius: 12,
    padding: Spacing.md,
    fontSize: Typography.body,
    color: Colors.text,
    height: 120,
    textAlignVertical: 'top',
  },
  charCount: {
    fontSize: Typography.caption,
    color: Colors.textLight,
    textAlign: 'right',
    marginTop: Spacing.xs,
  },
  guidelinesSection: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    padding: Spacing.screenPadding,
    paddingTop: 0,
    gap: Spacing.sm,
  },
  guidelinesText: {
    flex: 1,
    fontSize: Typography.caption,
    color: Colors.textSecondary,
    lineHeight: 18,
  },
  submitSection: {
    paddingHorizontal: Spacing.screenPadding,
    marginTop: Spacing.md,
  },
});
