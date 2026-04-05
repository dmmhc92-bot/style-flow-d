# StyleFlow - Premium Hairstylist Business App

## Overview
StyleFlow is a **production-ready, mobile-first iOS application** designed for professional hairstylists to manage their business, clients, appointments, and social presence. Built with Expo/React Native frontend and FastAPI/MongoDB backend.

---

## App Features

### 1. Authentication System
- **JWT-based authentication** with secure token management
- Email/password signup and login
- Forgot password with email reset (via Resend)
- Profile management
- Account deletion with subscription cancellation
- **Apple App Store Tester Bypass**: `appreview@apple.com` account has `is_tester=true` flag to bypass all paywalls

### 2. Dashboard (Home Tab)
- **4 Stat Cards**: Today's Appointments, Total Clients, VIP Clients, Followers
- **Quick Actions**: New Client, Book Appointment buttons
- **This Week Overview**: Weekly appointment summary
- AI Assistant sparkle icon in header

### 3. Client Management
- Full CRUD operations for clients
- Client profiles with:
  - Name, email, phone, photo
  - Hair goals and preferences
  - Notes and visit history
  - VIP status toggle
- **Smart Rebook Engine**: Tracks clients due for rebooking
- Client timeline with appointment history
- Formula history per client
- Photo gallery per client

### 4. Formula Vault
- Create and store hair color formulas
- Link formulas to specific clients
- Search and filter formulas
- Edit and delete formulas
- **Optimistic UI updates** for instant feedback

### 5. Appointments Calendar
- Full appointment scheduling system
- Calendar picker with time slots
- Service type and duration selection
- Notes field
- Status tracking (scheduled, completed, cancelled)
- No-show tracking

### 6. Social Feed (Engagement Hub)
- **3 Feed Tabs**: Trending, New, Following
- Create posts with up to 5 images
- Image upload via **Cloudinary CDN**
- Caption (500 chars max) and tags (5 max)
- Like, comment, save posts
- Report inappropriate content
- **Hashtag trends**: #balayage, #colortrend, #transformation, etc.

### 7. Discover (Stylist Hub)
- Search stylists by name, city, specialty
- Featured stylists section
- Follow/unfollow stylists
- View stylist profiles and portfolios

### 8. Portfolio & Gallery
- Portfolio: Showcase best work to public
- Gallery: Private image storage
- Upload images with Cloudinary
- Delete individual items
- **Optimistic UI updates**

### 9. AI Assistant (GPT-4o)
- Powered by **OpenAI GPT-4o** via Emergent LLM Key
- **6 Quick Actions**:
  - Formula Help
  - Rebook Script
  - Upsell Ideas
  - Caption Ideas
  - Retention Tips
  - Service Ideas
- Free-form chat interface

### 10. Subscription System (StyleFlow Pro)
- **RevenueCat** integration for iOS In-App Purchases
- **Trial System**: 3 free premium actions, then paywall
- Premium features unlock:
  - Unlimited clients
  - Unlimited formulas
  - AI Assistant
  - Full scheduling
  - Portfolio showcase
- Tester bypass for App Store review

### 11. Admin Moderation (Guardian Mode)
- Content reporting system
- Moderation queue for admins
- Strike system for violations
- User suspension/ban capabilities
- Appeal system for users
- Guardian action logs

### 12. Support & Legal
- Privacy Policy (full legal content)
- Terms of Service (full legal content)
- Community Guidelines
- Support/Help pages

---

## Technical Architecture

### Frontend Stack
```
Framework: Expo SDK 54 (React Native)
Router: Expo Router (file-based routing)
State Management: Zustand
Navigation: React Navigation 7
UI Components: Custom React Native components
Styling: StyleSheet.create()
HTTP Client: Axios
Image Handling: expo-image-picker + Cloudinary
```

### Backend Stack
```
Framework: FastAPI (Python)
Database: MongoDB
Authentication: JWT (PyJWT)
AI: OpenAI GPT-4o via Emergent Integrations
Email: Resend API
Image CDN: Cloudinary
```

### Database Schema (MongoDB Collections)
| Collection | Description |
|------------|-------------|
| `users` | User accounts, profiles, subscription status |
| `clients` | Stylist's client records |
| `formulas` | Hair color formulas |
| `appointments` | Scheduled appointments |
| `posts` | Social feed posts |
| `post_likes` | Post like records |
| `post_comments` | Post comments |
| `post_saves` | Saved posts |
| `follows` | User follow relationships |
| `portfolio` | Public portfolio items |
| `gallery` | Private gallery items |

---

## Environment Configuration

### Backend (.env)
```
MONGO_URL="mongodb://localhost:27017"
DB_NAME="styleflow_production"
EMERGENT_LLM_KEY=sk-emergent-***
JWT_SECRET_KEY=styleflow_secret_key_***
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=599940
RESEND_API_KEY=re_***
APP_DOMAIN=homestyleflowapp.com
APPLE_TEAM_ID=NTZB3ZFKXK
CLOUDINARY_CLOUD_NAME=dqq3nmkgd
CLOUDINARY_API_KEY=***
CLOUDINARY_API_SECRET=***
CLOUDINARY_UPLOAD_PRESET=Emergent
CLOUDINARY_ASSET_FOLDER=styleflow_uploads
```

### Frontend (.env)
```
EXPO_TUNNEL_SUBDOMAIN=hairflow-app-1
EXPO_PACKAGER_HOSTNAME=https://hairflow-app-1.preview.emergentagent.com
EXPO_PACKAGER_PROXY_URL=https://hairflow-app-1.preview.emergentagent.com
EXPO_PUBLIC_BACKEND_URL=https://hairflow-app-1.preview.emergentagent.com
EXPO_PUBLIC_APP_DOMAIN=homestyleflowapp.com
EXPO_PUBLIC_REVENUECAT_KEY=appl_***
```

### Production Build (EAS)
```
EXPO_PUBLIC_BACKEND_URL=https://homestyleflowapp.com
EXPO_PUBLIC_APP_DOMAIN=homestyleflowapp.com
```

---

## API Endpoints Summary

### Authentication (`/api/auth`)
- `POST /signup` - Register new user
- `POST /login` - Login user
- `POST /logout` - Logout user
- `GET /me` - Get current user
- `PUT /profile` - Update profile
- `DELETE /account` - Delete account
- `POST /forgot-password` - Request reset
- `POST /reset-password` - Reset password

### Clients (`/api/clients`)
- `GET /` - List all clients
- `POST /` - Create client
- `GET /{id}` - Get client
- `PUT /{id}` - Update client
- `DELETE /{id}` - Delete client
- `GET /{id}/timeline` - Get visit history
- `GET /rebook/due` - Clients due for rebook

### Formulas (`/api/formulas`)
- `GET /` - List formulas
- `POST /` - Create formula
- `PUT /{id}` - Update formula
- `DELETE /{id}` - Delete formula

### Appointments (`/api/appointments`)
- `GET /` - List appointments
- `POST /` - Create appointment
- `GET /{id}` - Get appointment
- `PUT /{id}` - Update appointment
- `DELETE /{id}` - Delete appointment

### Posts/Feed (`/api/posts`)
- `GET /` - Get feed posts
- `POST /` - Create post
- `DELETE /{id}` - Delete post
- `POST /{id}/like` - Like post
- `DELETE /{id}/like` - Unlike post
- `POST /{id}/comment` - Comment on post
- `POST /{id}/save` - Save post
- `POST /{id}/report` - Report post

### Profiles (`/api/profiles`)
- `GET /me` - Get own profile
- `GET /discover` - Discover stylists

### Users (`/api/users`)
- `GET /following` - Users I follow
- `GET /followers` - My followers
- `POST /{id}/follow` - Follow user
- `DELETE /{id}/follow` - Unfollow user

### Portfolio/Gallery (`/api/portfolio`, `/api/gallery`)
- `GET /` - List items
- `POST /` - Add item
- `DELETE /{id}` - Delete item

### AI Assistant (`/api/ai`)
- `POST /chat` - Chat with AI

### Dashboard (`/api/dashboard`)
- `GET /stats` - Dashboard statistics

### Admin/Moderation (`/api/admin`)
- Various moderation endpoints
- Guardian Mode actions
- Appeals system

---

## App Store Configuration

### iOS App Store Connect
- **Apple ID**: DMMHC92@gmail.com
- **App Store App ID**: 6761026979
- **Apple Team ID**: NTZB3ZFKXK
- **SKU**: styleflow001
- **Bundle ID**: com.styleflow.app

### EAS Build Profiles
- `development` - Development builds with simulator
- `preview` - Internal testing builds
- `testflight` - TestFlight distribution
- `production` - App Store distribution

---

## Test Accounts

| Account | Email | Password | Role |
|---------|-------|----------|------|
| Admin | admin@styleflow.com | Admin1234! | Full admin access |
| Apple Tester | appreview@apple.com | AppleTest123! | Bypasses all paywalls |

---

## 3rd Party Integrations

| Service | Purpose | Key Location |
|---------|---------|--------------|
| OpenAI GPT-4o | AI Assistant | Emergent LLM Key |
| RevenueCat | Subscriptions/IAP | Frontend .env |
| Resend | Email delivery | Backend .env |
| Cloudinary | Image CDN/storage | Backend .env |

---

## Trial/Paywall System

### How It Works
1. **Free users** get 3 premium actions (creating clients, formulas, appointments, posts)
2. **4th action** triggers PaywallModal - must subscribe to continue
3. **Premium subscribers** have unlimited access
4. **Apple testers** (`is_tester=true`) bypass all paywalls automatically

### Tracked Actions
- `clientsCreated` - Creating new clients
- `formulasCreated` - Creating new formulas
- `appointmentsCreated` - Creating new appointments
- `postsCreated` - Creating new posts
- `aiChatsUsed` - AI assistant usage

---

## File Structure

```
/app
├── backend/
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── security.py
│   │   └── strike_engine.py
│   ├── models/
│   │   └── *.py
│   ├── routes/
│   │   ├── admin.py
│   │   ├── ai.py
│   │   ├── appointments.py
│   │   ├── auth.py
│   │   ├── business.py
│   │   ├── clients.py
│   │   ├── dashboard.py
│   │   ├── posts.py
│   │   ├── profiles.py
│   │   └── users.py
│   ├── server.py
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   ├── app/
│   │   ├── tabs/ (main 5 tabs)
│   │   ├── auth/ (login, signup)
│   │   ├── client/ (client screens)
│   │   ├── appointment/ (appointment screens)
│   │   ├── post/ (post screens)
│   │   ├── settings/ (settings screens)
│   │   ├── admin/ (admin screens)
│   │   └── *.tsx (other screens)
│   ├── components/
│   ├── constants/
│   ├── store/
│   │   ├── authStore.ts
│   │   ├── subscriptionStore.ts
│   │   └── trialStore.ts
│   ├── utils/
│   ├── app.json
│   ├── eas.json
│   ├── package.json
│   └── .env
│
└── STYLEFLOW_APP_DOCUMENTATION.md
```

---

## Production Deployment

### Current Status
- **Database**: `styleflow_production` (MongoDB)
- **Backend URL**: https://homestyleflowapp.com
- **EAS Build**: Configured for iOS App Store
- **RevenueCat**: Configured with app entitlements

### Verification Checklist
- [x] All 12+ API endpoints returning 200
- [x] All 5 navigation tabs working
- [x] All forms and buttons functional
- [x] Privacy Policy and Terms pages
- [x] AI Assistant working
- [x] Image uploads via Cloudinary
- [x] Trial/paywall system
- [x] Apple tester bypass
- [x] No console errors

---

*Last Updated: April 2026*
*Version: 1.0.0*
