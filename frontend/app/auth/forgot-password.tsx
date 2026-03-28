import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  TouchableOpacity,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import Input from '../../components/Input';
import Button from '../../components/Button';
import Colors from '../../constants/Colors';
import Spacing from '../../constants/Spacing';
import Typography from '../../constants/Typography';
import { useAuthStore } from '../../store/authStore';

export default function ForgotPasswordScreen() {
  const router = useRouter();
  const { forgotPassword } = useAuthStore();
  
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');
  
  const validateEmail = () => {
    if (!email) {
      setError('Email is required');
      return false;
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      setError('Please enter a valid email address');
      return false;
    }
    setError('');
    return true;
  };
  
  const handleSendReset = async () => {
    if (!validateEmail()) return;
    
    setLoading(true);
    try {
      await forgotPassword(email);
      setSubmitted(true);
    } catch (err: any) {
      // Still show success for security - don't reveal if email exists
      setSubmitted(true);
    } finally {
      setLoading(false);
    }
  };
  
  if (submitted) {
    return (
      <SafeAreaView style={styles.container} edges={['top']}>
        <View style={styles.successContainer}>
          <View style={styles.iconCircle}>
            <Ionicons name="mail" size={48} color={Colors.accent} />
          </View>
          
          <Text style={styles.successTitle}>Check Your Email</Text>
          
          <Text style={styles.successMessage}>
            If an account exists for{' '}
            <Text style={styles.emailHighlight}>{email}</Text>
            {', '}we've sent password reset instructions.
          </Text>
          
          <Text style={styles.successNote}>
            The link will expire in 1 hour for security reasons.
          </Text>
          
          <View style={styles.tipsContainer}>
            <Text style={styles.tipsTitle}>Didn't receive the email?</Text>
            <View style={styles.tipRow}>
              <Ionicons name="checkmark-circle" size={16} color={Colors.textSecondary} />
              <Text style={styles.tipText}>Check your spam or junk folder</Text>
            </View>
            <View style={styles.tipRow}>
              <Ionicons name="checkmark-circle" size={16} color={Colors.textSecondary} />
              <Text style={styles.tipText}>Make sure you entered the right email</Text>
            </View>
          </View>
          
          <Button
            title="Back to Login"
            onPress={() => router.replace('/auth/login')}
            style={styles.backButton}
          />
          
          <TouchableOpacity 
            style={styles.resendLink}
            onPress={() => setSubmitted(false)}
          >
            <Text style={styles.resendText}>Try a different email</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }
  
  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
        >
          <View style={styles.header}>
            <TouchableOpacity
              style={styles.backButton}
              onPress={() => router.back()}
            >
              <Ionicons name="arrow-back" size={24} color={Colors.text} />
            </TouchableOpacity>
            
            <View style={styles.iconCircle}>
              <Ionicons name="lock-open-outline" size={40} color={Colors.accent} />
            </View>
            
            <Text style={styles.title}>Forgot Password?</Text>
            <Text style={styles.subtitle}>
              No worries! Enter your email and we'll send you a link to reset your password.
            </Text>
          </View>
          
          <View style={styles.form}>
            <Input
              label="Email Address"
              value={email}
              onChangeText={(text) => {
                setEmail(text);
                if (error) setError('');
              }}
              placeholder="Enter your email"
              keyboardType="email-address"
              autoCapitalize="none"
              autoCorrect={false}
              autoComplete="email"
              error={error}
              icon={<Ionicons name="mail-outline" size={20} color={Colors.textSecondary} />}
            />
            
            <Button
              title={loading ? "Sending..." : "Send Reset Link"}
              onPress={handleSendReset}
              loading={loading}
              disabled={loading}
              style={styles.submitButton}
            />
            
            <TouchableOpacity
              style={styles.loginLink}
              onPress={() => router.replace('/auth/login')}
            >
              <Ionicons name="arrow-back" size={16} color={Colors.accent} />
              <Text style={styles.loginText}>Back to Login</Text>
            </TouchableOpacity>
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
    paddingHorizontal: Spacing.screenPadding,
    paddingVertical: Spacing.lg,
  },
  header: {
    marginBottom: Spacing.xxl,
    alignItems: 'center',
  },
  backButton: {
    alignSelf: 'flex-start',
    marginBottom: Spacing.lg,
    padding: Spacing.xs,
  },
  iconCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: Colors.accent + '20',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.lg,
  },
  title: {
    fontSize: Typography.h1,
    fontWeight: Typography.bold,
    color: Colors.text,
    marginBottom: Spacing.sm,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 22,
    paddingHorizontal: Spacing.md,
  },
  form: {
    flex: 1,
  },
  submitButton: {
    marginTop: Spacing.lg,
  },
  loginLink: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: Spacing.xl,
    padding: Spacing.sm,
  },
  loginText: {
    fontSize: Typography.body,
    color: Colors.accent,
    fontWeight: Typography.medium,
    marginLeft: Spacing.xs,
  },
  // Success state styles
  successContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: Spacing.screenPadding,
    paddingVertical: Spacing.xl,
  },
  successTitle: {
    fontSize: Typography.h1,
    fontWeight: Typography.bold,
    color: Colors.text,
    marginBottom: Spacing.md,
    textAlign: 'center',
  },
  successMessage: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: Spacing.sm,
    paddingHorizontal: Spacing.md,
  },
  emailHighlight: {
    color: Colors.accent,
    fontWeight: Typography.semibold,
  },
  successNote: {
    fontSize: Typography.bodySmall,
    color: Colors.textLight,
    textAlign: 'center',
    marginBottom: Spacing.xl,
  },
  tipsContainer: {
    backgroundColor: Colors.backgroundSecondary,
    borderRadius: 12,
    padding: Spacing.md,
    width: '100%',
    marginBottom: Spacing.xl,
  },
  tipsTitle: {
    fontSize: Typography.bodySmall,
    fontWeight: Typography.semibold,
    color: Colors.text,
    marginBottom: Spacing.sm,
  },
  tipRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: Spacing.xs,
  },
  tipText: {
    fontSize: Typography.bodySmall,
    color: Colors.textSecondary,
    marginLeft: Spacing.sm,
  },
  resendLink: {
    marginTop: Spacing.md,
    padding: Spacing.sm,
  },
  resendText: {
    fontSize: Typography.body,
    color: Colors.accent,
    fontWeight: Typography.medium,
  },
});
