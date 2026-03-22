import React, { useEffect } from 'react';
import { useRouter, usePathname } from 'expo-router';
import { useAuthStore } from '../store/authStore';

/**
 * Hook to check user's moderation status and redirect to status screen if needed
 */
export function useModerationCheck() {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isAuthenticated } = useAuthStore();
  
  useEffect(() => {
    if (!isAuthenticated || !user) return;
    
    // Allow access to certain paths even for suspended/banned users
    const allowedPaths = [
      '/account/status',
      '/settings/guidelines',
      '/auth/login',
      '/',
    ];
    
    if (allowedPaths.some(path => pathname.startsWith(path))) return;
    
    const status = user.moderation_status;
    
    // Check if user needs to see the status screen
    if (status === 'banned' || status === 'suspended') {
      router.replace('/account/status');
    }
  }, [user, isAuthenticated, pathname]);
}

/**
 * Check if user has an active warning that should be shown
 */
export function useWarningBanner() {
  const { user } = useAuthStore();
  
  if (!user) return null;
  
  if (user.moderation_status === 'warned' && user.warnings_count && user.warnings_count > 0) {
    return {
      type: 'warning',
      title: 'Account Warning',
      message: user.last_warning_reason || 'Your account has received a warning for violating community guidelines.',
      count: user.warnings_count,
    };
  }
  
  if (user.moderation_status === 'restricted') {
    return {
      type: 'restricted',
      title: 'Account Restricted',
      message: 'Some features are temporarily limited due to policy violations.',
    };
  }
  
  return null;
}
