import React, { useEffect, useCallback } from 'react';
import { Stack, useRouter, useRootNavigationState, useSegments } from 'expo-router';
import * as Linking from 'expo-linking';
import { useAuthStore } from '../store/authStore';
import { NetworkProvider } from '../contexts/NetworkContext';
import LoadingSpinner from '../components/LoadingSpinner';
import { syncService } from '../utils/syncService';

export default function RootLayout() {
  const { isLoading, isAuthenticated, loadUser } = useAuthStore();
  const router = useRouter();
  const segments = useSegments();
  const navigationState = useRootNavigationState();

  useEffect(() => {
    loadUser();
    // Initialize sync service for offline-first functionality
    syncService.initialize();
  }, []);

  // Handle auth state changes and redirect appropriately
  useEffect(() => {
    if (isLoading || !navigationState?.key) return;

    const inAuthGroup = segments[0] === 'auth';
    const inTabsGroup = segments[0] === 'tabs';

    if (isAuthenticated && inAuthGroup) {
      // User is authenticated but in auth screens - redirect to tabs
      router.replace('/tabs');
    } else if (!isAuthenticated && inTabsGroup) {
      // User is not authenticated but in tabs - redirect to login
      router.replace('/auth/login');
    }
  }, [isAuthenticated, segments, isLoading, navigationState?.key]);

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
