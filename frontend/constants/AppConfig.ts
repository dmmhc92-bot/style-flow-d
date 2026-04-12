// Centralized app configuration
// Legal URLs use GitHub-hosted markdown files for App Store compliance
const APP_DOMAIN = process.env.EXPO_PUBLIC_APP_DOMAIN || 'homestyleflowapp.com';

// GitHub repo for legal documents - DO NOT MIX WITH OTHER PROJECTS
const GITHUB_USERNAME = 'dmmhc92-bot';
const GITHUB_REPO = 'style-flow-d';
const GITHUB_BRANCH = 'main';

export const AppConfig = {
  app: {
    name: 'StyleFlow',
    version: '1.0.0',
    domain: APP_DOMAIN,
  },
  
  legal: {
    // External GitHub URLs for App Store compliance
    privacyPolicyUrl: `https://raw.githubusercontent.com/${GITHUB_USERNAME}/${GITHUB_REPO}/${GITHUB_BRANCH}/privacy-policy.md`,
    termsOfServiceUrl: `https://raw.githubusercontent.com/${GITHUB_USERNAME}/${GITHUB_REPO}/${GITHUB_BRANCH}/terms-of-service.md`,
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
