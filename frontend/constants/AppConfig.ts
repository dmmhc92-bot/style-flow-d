// Centralized app configuration
export const AppConfig = {
  app: {
    name: 'StyleFlow',
    version: '1.0.0',
  },
  
  legal: {
    privacyPolicyUrl: 'https://styleflow.app/privacy',
    termsOfServiceUrl: 'https://styleflow.app/terms',
    supportUrl: 'https://styleflow.app/support',
    supportEmail: 'support@styleflow.app',
  },
  
  subscription: {
    productId: 'styleflow_pro_monthly',
    price: '$29.99',
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
