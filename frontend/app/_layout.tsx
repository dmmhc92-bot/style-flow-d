import React, { useEffect } from 'react';
import { Stack, useRouter } from 'expo-router';
import * as Linking from 'expo-linking';
import { useAuthStore } from '../store/authStore';
import { NetworkProvider } from '../contexts/NetworkContext';
import LoadingSpinner from '../components/LoadingSpinner';

export default function RootLayout() {
  const { isLoading, loadUser } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    loadUser();
  }, []);

  // Handle deep links for password reset
  useEffect(() => {
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
  }, []);

  const handleDeepLink = (url: string) => {
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
  };

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
