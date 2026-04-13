// Centralized app configuration
// Legal URLs use GitHub Pages for Apple App Store compliance
const APP_DOMAIN = process.env.EXPO_PUBLIC_APP_DOMAIN || 'homestyleflowapp.com';

export const AppConfig = {
  app: {
    name: 'StyleFlow',
    version: '1.0.0',
    domain: APP_DOMAIN,
  },
  
  legal: {
    // LIVE GitHub Pages URLs - Apple Guideline Compliant
    // These open in external browser as properly formatted HTML webpages
    privacyPolicyUrl: 'https://dmmhc92-bot.github.io/style-flow-d/privacy-policy.html',
    termsOfServiceUrl: 'https://dmmhc92-bot.github.io/style-flow-d/terms-of-service.html',
    supportUrl: `mailto:styleflowsupport@gmail.com?subject=StyleFlow Support`,
    supportEmail: 'styleflowsupport@gmail.com',
    // In-app fallback paths
    privacyPolicyPath: '/privacy',
    termsOfServicePath: '/terms',
    supportPath: '/support',
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
