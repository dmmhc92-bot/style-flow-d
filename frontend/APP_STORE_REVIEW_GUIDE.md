# StyleFlow Studio AI - App Store Review Guide

## Overview
StyleFlow is a premium business management app for professional hairstylists. It features client management, formula vault, appointment scheduling, portfolio showcase, AI assistant, and a social discovery hub.

---

## 🔐 TEST CREDENTIALS

### Admin Account (Full Access)
```
Email: admin@styleflow.com
Password: Admin1234!
```
- Full admin/moderation privileges
- Access to Guardian Mode dashboard
- Can view reported content and take action

### Regular Test Account
```
Email: appreview@apple.com
Password: AppleTest123!
```
- Standard stylist account
- All user features enabled
- Pre-populated with sample data

---

## 📱 USER FEATURES (Regular Stylists)

### 1. Home Dashboard
**Location**: First tab after login
- Quick stats: Today's appointments, total clients, formulas
- Quick Actions:
  - **Add Client** → Creates new client profile
  - **Add Appointment** → Schedule new appointment
  - **Add Formula** → Save color/treatment formula
  - **Add Photo** → Upload to portfolio
- Upcoming appointments list
- AI Assistant quick access

### 2. Feed Tab
**Location**: Second tab
- Social feed showing posts from followed stylists
- **Floating "+" Button** → Create new post with image/text
- Like, comment, save posts
- **Report Button** (⚠️ icon) → Report inappropriate content
- Pull-to-refresh for new content

### 3. Clients Tab
**Location**: Third tab
- Complete client management system
- **Add Client**: Name, phone, email, notes, preferences
- **Client Profile** includes:
  - Contact information
  - Visit history
  - Formula history (linked)
  - Photos (before/after)
  - Notes and preferences
- Search and filter clients
- Tap client → View/Edit details
- Swipe to delete

### 4. Discover Tab (Social Hub)
**Location**: Fourth tab
- Discover other stylists
- **Search** by name, location, specialty
- **Featured Stylists** carousel
- Tap profile → View full portfolio
- **Follow/Unfollow** buttons
- View followers/following counts

### 5. More Tab (Settings & Tools)
**Location**: Fifth tab
- **Profile Settings** → Edit bio, photo, business info
- **My Connections** → View Following/Followers lists
- **StyleFlow Pro** → Subscription management ($12.99/month)
- **Formula Vault** → Saved color formulas
- **Portfolio** → Manage showcase images
- **Notifications** → Preferences
- **Privacy & Security**
- **Help & Support**
- **Logout**

### 6. Formula Vault
**Access**: More Tab → Formula Vault OR Client Profile
- Save custom color formulas
- Fields: Name, brand, formula details, processing time
- Link to specific clients
- Search formulas
- Duplicate/edit/delete

### 7. Appointments Calendar
**Access**: Home Quick Action OR More Tab
- Calendar view with appointments
- Create/edit/delete appointments
- Link to client
- Add notes, services, duration
- Reminder notifications

### 8. AI Assistant
**Access**: Home Dashboard OR dedicated button
- Ask hair-related questions
- Get formula recommendations
- Business advice
- Powered by GPT-4o
- Daily usage limits based on subscription

### 9. Portfolio
**Access**: More Tab → Portfolio OR Profile
- Showcase best work
- Upload before/after photos
- Add captions
- Grid display on public profile
- Delete/reorder images

---

## 👑 ADMIN FEATURES (Guardian Mode)

### Accessing Admin Panel
1. Login with admin account
2. Navigate to: **More Tab → Admin Dashboard**

### Guardian Mode Philosophy
- **Privacy-First**: Admin cannot browse all user content
- **Report-Based Only**: Admin only sees content that users have reported
- **Automated Strikes**: Background system handles warnings/suspensions

### Admin Dashboard Sections

#### 1. Moderation Queue
**Path**: Admin Dashboard → Moderation Queue
- View all reported content
- Each report shows:
  - Reporter info
  - Reported content (post/user)
  - Report reason
  - Timestamp
- **Actions**:
  - **Dismiss** → Mark as not violating
  - **Warn User** → Issue warning (1 strike)
  - **Remove Content** → Delete the post
  - **Suspend User** → Temporary ban

#### 2. Guardian Actions Log
**Path**: Admin Dashboard → Guardian Actions
- Complete audit trail of all moderation actions
- Shows who took action, when, and what action
- Filterable by date, action type

#### 3. Active Suspensions
**Path**: Admin Dashboard → Active Suspensions
- List of currently suspended users
- Suspension duration remaining
- **Lift Suspension** button to restore access early

#### 4. Appeals Queue
**Path**: Admin Dashboard → Appeals
- Users can appeal suspensions
- View appeal reason
- **Approve** → Lift suspension
- **Deny** → Maintain suspension

#### 5. Moderation Stats
- Total reports processed
- Actions taken breakdown
- Active warnings count
- Current suspensions count

### Strike System (Automated)
The background "Strike Engine" enforces rules automatically:

| Strikes | Consequence |
|---------|-------------|
| 1 | Warning notification |
| 2 | 24-hour suspension |
| 3 | 72-hour suspension |
| 4+ | Permanent review required |

---

## 🔄 KEY USER FLOWS TO TEST

### Flow 1: New User Onboarding
1. Open app → Tap "Sign Up"
2. Enter name, email, password, business name
3. Complete profile setup
4. Explore dashboard

### Flow 2: Client Management
1. Home → "Add Client"
2. Fill client details → Save
3. Go to Clients tab → Find client
4. Add formula to client
5. Schedule appointment for client

### Flow 3: Social Engagement
1. Go to Discover tab
2. Search for a stylist
3. Tap profile → View portfolio
4. Tap "Follow"
5. Go to Feed → See their posts
6. Go to More → My Connections → Verify in Following list

### Flow 4: Content Reporting (User)
1. Go to Feed tab
2. Find any post
3. Tap ⚠️ Report icon
4. Select reason → Submit
5. Confirmation appears

### Flow 5: Moderation (Admin)
1. Login as admin@styleflow.com
2. Go to More → Admin Dashboard
3. Tap Moderation Queue
4. View reported content
5. Take action (Warn/Remove/Suspend)
6. Check Guardian Actions for audit log

### Flow 6: Subscription
1. More Tab → StyleFlow Pro
2. View features and pricing ($12.99/month)
3. Tap "Subscribe Now"
4. (Sandbox) Complete purchase
5. Verify Pro badge appears

### Flow 7: AI Assistant
1. Home Dashboard → AI Assistant
2. Ask: "What's a good formula for covering gray?"
3. Receive AI response
4. Ask follow-up question

---

## ⚙️ TECHNICAL NOTES

### Authentication
- JWT-based authentication
- 9999-hour token expiration (persistent login)
- Stored in secure AsyncStorage
- Auto-login on app restart

### Data Persistence
- All data synced to cloud
- Offline-capable for viewing
- Auto-sync when connection restored

### Subscription (RevenueCat)
- Product ID: `styleflow_pro_monthly`
- Price: $12.99/month
- Auto-renewable subscription
- Restore purchases available

### Deep Links
- Scheme: `styleflow://`
- Password reset: `styleflow://reset-password?token=xxx`
- Profile: `styleflow://hub/{userId}`

---

## 🚫 CONTENT GUIDELINES

The app enforces community guidelines through Guardian Mode:
- No harassment or hate speech
- No spam or misleading content
- No inappropriate images
- Professional conduct expected

Users can report violations, and the admin reviews only reported content (no surveillance).

---

## 📞 SUPPORT

For any testing issues:
- In-app: More → Help & Support
- Email: support@styleflowapp.com

---

## VERSION INFO

- App Version: 1.0.0
- Build: 4
- Bundle ID: com.styleflow.app
- Minimum iOS: 13.4
