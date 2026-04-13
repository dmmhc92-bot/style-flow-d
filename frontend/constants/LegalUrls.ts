// Legal document URLs - hosted on GitHub
// StyleFlow App - DO NOT MIX WITH OTHER PROJECTS
// Apple Guideline Compliant - Opens as formatted webpages

const GITHUB_USERNAME = 'dmmhc92-bot';
const GITHUB_REPO = 'style-flow-d';
const GITHUB_BRANCH = 'main';

// GitHub blob URLs - These open as FORMATTED WEBPAGES (Apple Compliant)
export const LEGAL_URLS = {
  PRIVACY_POLICY: `https://github.com/${GITHUB_USERNAME}/${GITHUB_REPO}/blob/${GITHUB_BRANCH}/privacy-policy.md`,
  TERMS_OF_SERVICE: `https://github.com/${GITHUB_USERNAME}/${GITHUB_REPO}/blob/${GITHUB_BRANCH}/terms-of-service.md`,
};

// Support email for legal inquiries
export const SUPPORT_EMAIL = 'styleflowsupport@gmail.com';

// App Store Connect URLs (use these in App Store Connect)
export const APP_STORE_URLS = {
  PRIVACY_POLICY: LEGAL_URLS.PRIVACY_POLICY,
  TERMS_OF_SERVICE: LEGAL_URLS.TERMS_OF_SERVICE,
};

export default LEGAL_URLS;
