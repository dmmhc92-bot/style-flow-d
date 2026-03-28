import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import Input from '../../components/Input';
import Colors from '../../constants/Colors';
import Spacing from '../../constants/Spacing';
import Typography from '../../constants/Typography';
import { useAuthStore } from '../../store/authStore';

export default function SignupScreen() {
  const router = useRouter();
  const signup = useAuthStore((state) => state.signup);
  
  const [fullName, setFullName] = useState('');
  const [businessName, setBusinessName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<any>({});
  
  const validateForm = () => {
    const newErrors: any = {};
    
    if (!fullName) {
      newErrors.fullName = 'Full name is required';
    }
    
    if (!email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      newErrors.email = 'Email is invalid';
    }
    
    if (!password) {
      newErrors.password = 'Password is required';
    } else if (password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }
    
    if (password !== confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  
  const handleSignup = async () => {
    if (!validateForm()) return;
    
    setLoading(true);
    try {
      await signup(email, password, fullName, businessName || undefined);
      // Give time for the state to update and token to be cached
      await new Promise(resolve => setTimeout(resolve, 200));
      router.replace('/tabs');
    } catch (error: any) {
      setLoading(false);
      Alert.alert('Signup Failed', error.message);
    }
  };
  
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
            <Text style={styles.title}>Create Account</Text>
            <Text style={styles.subtitle}>Join StyleFlow today</Text>
          </View>
          
          <View style={styles.form}>
            <Input
              label="Full Name"
              value={fullName}
              onChangeText={setFullName}
              placeholder="John Doe"
              error={errors.fullName}
              icon={<Ionicons name="person-outline" size={20} color={Colors.textSecondary} />}
            />
            
            <Input
              label="Business Name (Optional)"
              value={businessName}
              onChangeText={setBusinessName}
              placeholder="Your Salon Name"
              icon={<Ionicons name="business-outline" size={20} color={Colors.textSecondary} />}
            />
            
            <Input
              label="Email"
              value={email}
              onChangeText={setEmail}
              placeholder="your@email.com"
              keyboardType="email-address"
              autoCapitalize="none"
              autoCorrect={false}
              error={errors.email}
              icon={<Ionicons name="mail-outline" size={20} color={Colors.textSecondary} />}
            />
            
            <Input
              label="Password"
              value={password}
              onChangeText={setPassword}
              placeholder="••••••••"
              secureTextEntry={!showPassword}
              error={errors.password}
              icon={<Ionicons name="lock-closed-outline" size={20} color={Colors.textSecondary} />}
            />
            
            <Input
              label="Confirm Password"
              value={confirmPassword}
              onChangeText={setConfirmPassword}
              placeholder="••••••••"
              secureTextEntry={!showPassword}
              error={errors.confirmPassword}
              icon={<Ionicons name="lock-closed-outline" size={20} color={Colors.textSecondary} />}
            />
            
            <TouchableOpacity
              style={[styles.signupButton, loading && styles.signupButtonDisabled]}
              onPress={handleSignup}
              disabled={loading}
              activeOpacity={0.8}
            >
              {loading ? (
                <ActivityIndicator color={Colors.buttonText || '#FFFFFF'} />
              ) : (
                <Text style={styles.signupButtonText}>Create Account</Text>
              )}
            </TouchableOpacity>
            
            <View style={styles.loginContainer}>
              <Text style={styles.loginText}>Already have an account? </Text>
              <TouchableOpacity onPress={() => router.back()}>
                <Text style={styles.loginLink}>Sign In</Text>
              </TouchableOpacity>
            </View>
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
    marginBottom: Spacing.xl,
  },
  backButton: {
    marginBottom: Spacing.md,
    width: 40,
  },
  title: {
    fontSize: Typography.h1,
    fontWeight: Typography.bold,
    color: Colors.text,
    marginBottom: Spacing.sm,
  },
  subtitle: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
  },
  form: {
    flex: 1,
  },
  signupButton: {
    marginTop: Spacing.md,
    marginBottom: Spacing.lg,
    backgroundColor: Colors.accent,
    paddingVertical: Spacing.md,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 50,
  },
  signupButtonDisabled: {
    opacity: 0.7,
  },
  signupButtonText: {
    color: Colors.buttonText || '#FFFFFF',
    fontSize: Typography.body,
    fontWeight: Typography.semibold,
  },
  loginContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
  },
  loginText: {
    fontSize: Typography.body,
    color: Colors.textSecondary,
  },
  loginLink: {
    fontSize: Typography.body,
    color: Colors.accent,
    fontWeight: Typography.semibold,
  },
});