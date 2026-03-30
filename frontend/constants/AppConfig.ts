// Centralized app configuration
// Legal URLs use in-app screens served by the backend
const APP_DOMAIN = process.env.EXPO_PUBLIC_APP_DOMAIN || 'homestyleflowapp.com';

export const AppConfig = {
  app: {
    name: 'StyleFlow',
    version: '1.0.0',
    domain: APP_DOMAIN,
  },
  
  legal: {
    // These are in-app screens, not external URLs
    privacyPolicyPath: '/privacy',
    termsOfServicePath: '/terms',
    supportPath: '/support',
    supportEmail: `support@${APP_DOMAIN}`,
  },
  
  subscription: {
    productId: 'styleflow_pro_monthly',
    price: '$12.99',
    pricingPeriod: 'month',
    features: [
      'Unlimited clients',
      'Advanced analytics',
      'AI Assistant unlimited queries',
      'Priority support',
      'Before & after gallery',
      'Formula vault',
    ],
  },
  
  auth: {
    tokenKey: 'authToken',
    userDataKey: 'userData',
  },
};
