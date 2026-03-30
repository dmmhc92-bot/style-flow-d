# StyleFlow - Automated Apple Deployment Setup

⚠️ **PROJECT SCOPE**: This configuration is for **StyleFlow ONLY** (com.styleflow.app)
Do NOT use these credentials for AgentRouteAI or any other project.

## App Store Connect Configuration

| Setting | Value |
|---------|-------|
| **App Name** | StyleFlow Studio AI |
| **Bundle ID** | com.styleflow.app |
| **SKU** | styleflow001 |
| **Apple ID** | 6761026979 |
| **Team ID** | NTZB3ZFKXK |

## GitHub Repository Secrets Required

Add these secrets to your GitHub repository (`dmmhc92-bot/style-flow-d`):

### Navigate to: Settings → Secrets and variables → Actions → New repository secret

| Secret Name | Value |
|-------------|-------|
| `EXPO_TOKEN` | `SzgHQ1XsrkiHt-jWFpYD2v20Oj22kXnJzj_QGMmp` |
| `APPLE_API_KEY_P8` | The full contents of your .p8 key file (see below) |

### APPLE_API_KEY_P8 Value:
```
-----BEGIN PRIVATE KEY-----
MIGTAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBHkwdwIBAQQgG6ZHj/GvJ0TXpPI4
MPCXOEnZGjKN5/WozvBdrp/+3P6gCgYIKoZIzj0DAQehRANCAAS0eiMI9yer/Ajy
Ckin6D2uQRlONtiELYkgSPLldyyVYYtOIUKMQvQ43RMcEzsfYBN7gU5cUV9a8wIl
AW2nEfgw
-----END PRIVATE KEY-----
```

## Apple API Key Details (Hardcoded in eas.json)

These are already configured in the project:
- **Key ID**: `7H48ZU4AD2`
- **Issuer ID**: `e05d02ae-8a38-478e-a195-ffe1d868ef44`
- **Key Path**: `./keys/AuthKey_7H48ZU4AD2.p8`

## System Separation Verification

The workflow includes a verification step that checks:
```yaml
- name: Verify StyleFlow Project
  run: |
    BUNDLE_ID=$(cat app.json | jq -r '.expo.ios.bundleIdentifier')
    if [ "$BUNDLE_ID" != "com.styleflow.app" ]; then
      echo "ERROR: This workflow is for StyleFlow only"
      exit 1
    fi
```

## Workflow Triggers

The GitHub Action will automatically:
- **On Push to main**: Build iOS and submit to TestFlight
- **Manual Trigger**: Go to Actions → "EAS Build & Submit to TestFlight" → Run workflow

## Manual Build Commands (Alternative)

If you prefer to run builds manually:

```bash
cd frontend

# Login to EAS with StyleFlow token
EXPO_TOKEN=SzgHQ1XsrkiHt-jWFpYD2v20Oj22kXnJzj_QGMmp npx eas whoami

# Build for TestFlight
npx eas build --profile testflight --platform ios

# Submit to TestFlight (uses API key from eas.json)
npx eas submit --profile testflight --platform ios --latest
```

## Files Created/Modified

- `/.github/workflows/eas-build-submit.yml` - GitHub Actions workflow (StyleFlow-specific)
- `/keys/AuthKey_7H48ZU4AD2.p8` - Apple API key (local only, gitignored)
- `/eas.json` - Updated with complete API key configuration for build & submit

## Certificate Generation

The Apple API Key bypasses 2FA and enables automated:
- Certificate generation
- Provisioning profile creation  
- App signing
- TestFlight submission
