import React, { useEffect } from 'react';
import { Stack } from 'expo-router';
import { useAuthStore } from '../store/authStore';
import { NetworkProvider } from '../contexts/NetworkContext';
import LoadingSpinner from '../components/LoadingSpinner';

export default function RootLayout() {
  const { isLoading, loadUser } = useAuthStore();

  useEffect(() => {
    loadUser();
  }, []);

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
        <Stack.Screen name="tabs" />
      </Stack>
    </NetworkProvider>
  );
}
