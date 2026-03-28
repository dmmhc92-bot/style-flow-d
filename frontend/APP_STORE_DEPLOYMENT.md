# StyleFlow App Store Deployment Guide
## PREPARE_APP_STORE_DEPLOYMENT - Complete Configuration

---

## 📱 Apple Developer Credentials (Configured)

| Setting | Value |
|---------|-------|
| **Bundle ID** | `com.styleflow.app` |
| **Apple ID (App ID)** | `6761026979` |
| **Team ID** | `NTZB3ZFKXK` |
| **SKU** | `styleflow001` |
| **Apple ID Email** | `DMMHC92@gmail.com` |

---

## 🔧 Configuration Files Updated

### eas.json
- ✅ TestFlight profile configured
- ✅ Production profile configured  
- ✅ Apple credentials in submit section
- ✅ Auto-increment build numbers enabled

### app.json
- ✅ Bundle identifier: `com.styleflow.app`
- ✅ Associated domains for deep linking
- ✅ Privacy manifest for App Store compliance
- ✅ Info.plist permissions with user-friendly descriptions
- ✅ App Store URL linked

---

## 🚀 Build Commands

### Step 1: Login to Expo (if not already)
```bash
npx eas login
# Enter your Expo account credentials
```

### Step 2: Configure Apple Credentials
```bash
cd /app/frontend
npx eas credentials
# Select: iOS > Production > Set up new credentials
# Follow prompts to authenticate with Apple Developer account
```

### Step 3: Build for TestFlight
```bash
npx eas build --profile testflight --platform ios
```

### Step 4: Submit to TestFlight
```bash
npx eas submit --platform ios --latest
```

---

## 📋 Pre-Submission Checklist

### App Store Connect Setup
- [ ] App created in App Store Connect with App ID: `6761026979`
- [ ] App name: "StyleFlow"
- [ ] Primary category: Lifestyle or Business
- [ ] Age rating: 4+ (no objectionable content)

### Required Assets
- [ ] App icon (1024x1024 PNG, no transparency)
- [ ] Screenshots for iPhone 6.7" (1290x2796)
- [ ] Screenshots for iPhone 6.5" (1284x2778)
- [ ] Screenshots for iPad 12.9" (2048x2732) - if supporting tablets
- [ ] App preview video (optional)

### App Store Metadata
- [ ] App description (4000 chars max)
- [ ] Keywords (100 chars max)
- [ ] Support URL
- [ ] Privacy Policy URL
- [ ] Marketing URL (optional)

### Review Information
- [ ] Demo account credentials for reviewer:
  - Email: `appreview@apple.com` or `tester@styleflow.com`
  - Password: (auto-generated with full access)
  - Note: These accounts have `isTester: true` flag - bypasses paywall

---

## 🔐 Privacy & Compliance

### Data Collection (configured in app.json)
- **Camera**: "Capture before & after transformations"
- **Photo Library**: "Upload stunning client photos to your portfolio"
- **Face ID**: "Secure login with Face ID"

### Privacy Manifest
- UserDefaults API declared for app preferences

### Export Compliance
- `ITSAppUsesNonExemptEncryption: false` (no custom encryption)

---

## 🧪 TestFlight Testing

### Internal Testing
1. Build completes → automatically available to team
2. Add internal testers in App Store Connect

### External Testing (Beta)
1. Submit for Beta App Review
2. Add external testers (up to 10,000)
3. Share public TestFlight link

---

## 📊 Post-Submission Monitoring

### Expected Timeline
- Build processing: 5-30 minutes
- Beta App Review: 24-48 hours
- App Store Review: 24-72 hours

### Common Rejection Reasons to Avoid
- ✅ All buttons functional (no dead buttons)
- ✅ Demo content available for reviewers
- ✅ Clear subscription terms
- ✅ Privacy policy linked
- ✅ No placeholder content

---

## 🎯 Quick Reference

```bash
# Full deployment sequence
cd /app/frontend
npx eas login
npx eas build --profile testflight --platform ios
npx eas submit --platform ios --latest
```

**Support**: styleflowsupport@gmail.com
