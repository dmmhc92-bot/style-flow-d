// Legal document URLs - hosted on GitHub
// StyleFlow App - DO NOT MIX WITH OTHER PROJECTS

const GITHUB_USERNAME = 'dmmhc92-bot';
const GITHUB_REPO = 'style-flow-d';
const GITHUB_BRANCH = 'main';

// Raw GitHub URLs for markdown files
export const LEGAL_URLS = {
  PRIVACY_POLICY: `https://raw.githubusercontent.com/${GITHUB_USERNAME}/${GITHUB_REPO}/${GITHUB_BRANCH}/privacy-policy.md`,
  TERMS_OF_SERVICE: `https://raw.githubusercontent.com/${GITHUB_USERNAME}/${GITHUB_REPO}/${GITHUB_BRANCH}/terms-of-service.md`,
  
  // GitHub Pages URLs (prettier HTML versions - if you enable GitHub Pages)
  PRIVACY_POLICY_WEB: `https://${GITHUB_USERNAME}.github.io/${GITHUB_REPO}/privacy-policy`,
  TERMS_OF_SERVICE_WEB: `https://${GITHUB_USERNAME}.github.io/${GITHUB_REPO}/terms-of-service`,
};

// Support email for legal inquiries
export const SUPPORT_EMAIL = 'styleflowsupport@gmail.com';

// App Store Connect URLs (use these in App Store Connect)
export const APP_STORE_URLS = {
  PRIVACY_POLICY: LEGAL_URLS.PRIVACY_POLICY,
  TERMS_OF_SERVICE: LEGAL_URLS.TERMS_OF_SERVICE,
};

export default LEGAL_URLS;
