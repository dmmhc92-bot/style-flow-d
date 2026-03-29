import React, { useEffect, useCallback, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Stack, useRouter, useRootNavigationState, useSegments } from 'expo-router';
import * as Linking from 'expo-linking';
import { useAuthStore } from '../store/authStore';
import { NetworkProvider } from '../contexts/NetworkContext';
import LoadingSpinner from '../components/LoadingSpinner';
import { syncService } from '../utils/syncService';

// Error Boundary Component for Auth Failures
function AuthErrorFallback({ onRetry }: { onRetry: () => void }) {
  return (
    <View style={errorStyles.container}>
      <Text style={errorStyles.title}>Session Error</Text>
      <Text style={errorStyles.message}>
        Unable to restore your session. Please log in again.
      </Text>
      <TouchableOpacity style={errorStyles.button} onPress={onRetry}>
        <Text style={errorStyles.buttonText}>Go to Login</Text>
      </TouchableOpacity>
    </View>
  );
}

const errorStyles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#0D0D0D',
    padding: 24,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 12,
  },
  message: {
    fontSize: 16,
    color: '#888888',
    textAlign: 'center',
    marginBottom: 24,
  },
  button: {
    backgroundColor: '#00D09E',
    paddingVertical: 14,
    paddingHorizontal: 32,
    borderRadius: 12,
  },
  buttonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default function RootLayout() {
  const { isLoading, isAuthenticated, loadUser } = useAuthStore();
  const router = useRouter();
  const segments = useSegments();
  const navigationState = useRootNavigationState();
  const [authError, setAuthError] = useState(false);

  // Initial auth check with error handling
  useEffect(() => {
    const initAuth = async () => {
      try {
        setAuthError(false);
        await loadUser();
        // Initialize sync service for offline-first functionality
        syncService.initialize();
      } catch (error) {
        console.error('[RootLayout] Auth initialization failed:', error);
        setAuthError(true);
      }
    };
    
    initAuth();
  }, []);

  // Handle auth state changes and redirect appropriately
  useEffect(() => {
    if (isLoading || !navigationState?.key || authError) return;

    const inAuthGroup = segments[0] === 'auth';
    const inTabsGroup = segments[0] === 'tabs';

    if (isAuthenticated && inAuthGroup) {
      // User is authenticated but in auth screens - redirect to tabs
      router.replace('/tabs');
    } else if (!isAuthenticated && inTabsGroup) {
      // User is not authenticated but in tabs - redirect to login
      router.replace('/auth/login');
    }
  }, [isAuthenticated, segments, isLoading, navigationState?.key, authError]);

  // Handle deep links for password reset - only when navigation is ready
  const handleDeepLink = useCallback((url: string) => {
    try {
      const parsed = Linking.parse(url);
      
      // Handle reset-password deep link
      // URL format: https://homestyleflowapp.com/reset-password?token=xxx
      // or styleflow://reset-password?token=xxx
      if (parsed.path === 'reset-password' || parsed.path?.includes('reset-password')) {
        const token = parsed.queryParams?.token;
        if (token) {
          router.replace({
            pathname: '/reset-password',
            params: { token: token as string },
          });
        }
      }
    } catch (error) {
      console.error('Error parsing deep link:', error);
    }
  }, [router]);

  useEffect(() => {
    // Only handle deep links when navigation is ready
    if (!navigationState?.key) return;

    // Handle initial URL (app opened from link)
    const handleInitialURL = async () => {
      const url = await Linking.getInitialURL();
      if (url) {
        handleDeepLink(url);
      }
    };

    // Handle URL when app is already open
    const subscription = Linking.addEventListener('url', (event) => {
      handleDeepLink(event.url);
    });

    handleInitialURL();

    return () => {
      subscription.remove();
    };
  }, [navigationState?.key, handleDeepLink]);

  // ERROR BOUNDARY: If auth check failed completely, show fallback
  if (authError) {
    return (
      <AuthErrorFallback 
        onRetry={() => {
          setAuthError(false);
          router.replace('/auth/login');
        }} 
      />
    );
  }

  // LOADING STATE: Show spinner while checking auth
  if (isLoading) {
    return <LoadingSpinner />;
  }

  return (
    <NetworkProvider>
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="index" />
        <Stack.Screen name="auth/login" />
        <Stack.Screen name="auth/signup" />
        <Stack.Screen name="auth/forgot-password" />
        <Stack.Screen name="reset-password" />
        <Stack.Screen name="tabs" />
      </Stack>
    </NetworkProvider>
  );
}
