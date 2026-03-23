import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import Input from '../components/Input';
import Button from '../components/Button';
import Colors from '../constants/Colors';
import Spacing from '../constants/Spacing';
import Typography from '../constants/Typography';
import api from '../utils/api';
import LoadingSpinner from '../components/LoadingSpinner';

export default function ResetPasswordScreen() {
  const router = useRouter();
  const { token } = useLocalSearchParams<{ token: string }>();
  
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [verifying, setVerifying] = useState(true);
  const [tokenValid, setTokenValid] = useState(false);
  const [maskedEmail, setMaskedEmail] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  
  // Verify token on mount
  useEffect(() => {
    if (token) {
      verifyToken();
    } else {
      setVerifying(false);
      setError('Invalid reset link. Please request a new password reset.');
    }
  }, [token]);
  
  const verifyToken = async () => {
    try {
      const response = await api.get(`/auth/verify-reset-token/${token}`);
      setTokenValid(true);
      setMaskedEmail(response.data.email);
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Invalid or expired reset link';
      setError(message);
    } finally {
      setVerifying(false);
    }
  };
  
  const handleResetPassword = async () => {
    if (!newPassword || !confirmPassword) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }
    
    if (newPassword.length < 8) {
      Alert.alert('Error', 'Password must be at least 8 characters');
      return;
    }
    
    if (newPassword !== confirmPassword) {
      Alert.alert('Error', 'Passwords do not match');
      return;
    }
    
    setLoading(true);
    try {
      await api.post('/auth/reset-password', {
        token,
        new_password: newPassword,
      });
      
      setSuccess(true);
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Failed to reset password';
      Alert.alert('Error', message);
    } finally {
      setLoading(false);
    }
  };
  
  if (verifying) {
    return <LoadingSpinner />;
  }
  
  if (success) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.successContainer}>
          <View style={styles.successIcon}>
            <Ionicons name="checkmark-circle" size={80} color={Colors.success} />
          </View>
          <Text style={styles.successTitle}>Password Reset!</Text>
          <Text style={styles.successMessage}>
            Your password has been successfully reset. You can now log in with your new password.
          </Text>
          <Button
            title="Go to Login"
            onPress={() => router.replace('/auth/login')}
            style={styles.loginButton}
          />
        </View>
      </SafeAreaView>
    );
  }
  
  if (error && !tokenValid) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.errorContainer}>
          <View style={styles.errorIcon}>
            <Ionicons name="alert-circle" size={80} color={Colors.error} />
          </View>
          <Text style={styles.errorTitle}>Link Expired</Text>
          <Text style={styles.errorMessage}>{error}</Text>
          <Button
            title="Request New Link"
            onPress={() => router.replace('/auth/forgot-password')}
            style={styles.loginButton}
          />
          <Button
            title="Back to Login"
            onPress={() => router.replace('/auth/login')}
            variant="outline"
            style={styles.backButton}
          />
        </View>
      </SafeAreaView>
    );
  }
  
  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
        >
          <View style={styles.header}>
            <View style={styles.iconContainer}>
              <Ionicons name="lock-closed" size={40} color={Colors.accent} />
            </View>
            <Text style={styles.title}>Create New Password</Text>
            <Text style={styles.subtitle}>
              Enter a new password for {maskedEmail}
            </Text>
          </View>
          
          <View style={styles.form}>
            <Input
              label="New Password"
              value={newPassword}
              onChangeText={setNewPassword}
              placeholder="Enter new password"
              secureTextEntry
              autoCapitalize="none"
            />
            
            <Input
              label="Confirm Password"
              value={confirmPassword}
              onChangeText={setConfirmPassword}
              placeholder="Confirm new password"
              secureTextEntry
              autoCapitalize="none"
            />
            
            <View style={styles.requirements}>
              <Text style={styles.requirementsTitle}>Password requirements:</Text>
              <View style={styles.requirementRow}>
                <Ionicons
                  name={newPassword.length >= 8 ? 'checkmark-circle' : 'ellipse-outline'}
                  size={16}
                  color={newPassword.length >= 8 ? Colors.success : Colors.textSecondary}
                />
                <Text style={[
                  styles.requirementText,
                  newPassword.length >= 8 && styles.requirementMet
                ]}>
                  At least 8 characters
                </Text>
              </View>
              <View style={styles.requirementRow}>
                <Ionicons
                  name={newPassword === confirmPassword && newPassword.length > 0 ? 'checkmark-circle' : 'ellipse-outline'}
                  size={16}
                  color={newPassword === confirmPassword && newPassword.length > 0 ? Colors.success : Colors.textSecondary}
                />
                <Text style={[
                  styles.requirementText,
                  newPassword === confirmPassword && newPassword.length > 0 && styles.requirementMet
                ]}>
                  Passwords match
                </Text>
              </View>
            </View>
            
            <Button
              title={loading ? 'Resetting...' : 'Reset Password'}
              onPress={handleResetPassword}
              disabled={loading || newPassword.length < 8 || newPassword !== confirmPassword}
              style={styles.resetButton}
            />
          </View>
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
  keyboardView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    padding: Spacing.screenPadding,
    justifyContent: 'center',
  },
  header: {
    alignItems: 'center',
    marginBottom: Spacing.xl,
  },
  iconContainer: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: Colors.accent + '20',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.md,
  },
  title: {
    fontSize: Typography.h2,
    fontWeight: Typography.bold,
    color: Colors.text,
    marginBottom: Spacing.sm,
  },
  subtitle: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
    textAlign: 'center',
  },
  form: {
    marginBottom: Spacing.xl,
  },
  requirements: {
    backgroundColor: Colors.backgroundSecondary,
    padding: Spacing.md,
    borderRadius: 12,
    marginBottom: Spacing.lg,
  },
  requirementsTitle: {
    fontSize: Typography.bodySmall,
    fontWeight: Typography.semibold,
    color: Colors.textSecondary,
    marginBottom: Spacing.sm,
  },
  requirementRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: Spacing.xs,
  },
  requirementText: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    marginLeft: Spacing.xs,
  },
  requirementMet: {
    color: Colors.success,
  },
  resetButton: {
    marginTop: Spacing.md,
  },
  successContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: Spacing.screenPadding,
  },
  successIcon: {
    marginBottom: Spacing.lg,
  },
  successTitle: {
    fontSize: Typography.h2,
    fontWeight: Typography.bold,
    color: Colors.text,
    marginBottom: Spacing.md,
  },
  successMessage: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginBottom: Spacing.xl,
  },
  loginButton: {
    width: '100%',
  },
  errorContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: Spacing.screenPadding,
  },
  errorIcon: {
    marginBottom: Spacing.lg,
  },
  errorTitle: {
    fontSize: Typography.h2,
    fontWeight: Typography.bold,
    color: Colors.text,
    marginBottom: Spacing.md,
  },
  errorMessage: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginBottom: Spacing.xl,
  },
  backButton: {
    width: '100%',
    marginTop: Spacing.md,
  },
});
