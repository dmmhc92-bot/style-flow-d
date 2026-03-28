import React, { useEffect } from 'react';
import { Redirect, useRouter } from 'expo-router';
import { useAuthStore } from '../store/authStore';
import LoadingSpinner from '../components/LoadingSpinner';

export default function Index() {
  const { isAuthenticated, isLoading } = useAuthStore();
  const router = useRouter();

  // Effect to handle navigation when auth state changes
  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace('/tabs');
    }
  }, [isAuthenticated, isLoading]);

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (isAuthenticated) {
    return <Redirect href="/tabs" />;
  }

  return <Redirect href="/auth/login" />;
}
