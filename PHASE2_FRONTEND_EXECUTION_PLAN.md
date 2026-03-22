# Phase 2 Frontend - Complete Implementation Plan

## CURRENT STATE: Backend 100% Ready, Frontend 15% Done

### ✅ WHAT EXISTS NOW:
- Backend APIs: All 50+ endpoints working
- Auth screens: Complete
- Settings: Complete
- Dashboard: Exists but needs refinement
- Clients/Appointments: Basic functionality
- Navigation structure: Tabs exist

### ❌ WHAT'S MISSING (CRITICAL):
All Phase 2 frontend screens and wiring to existing backend.

---

## IMPLEMENTATION EXECUTION ORDER

### BATCH 1: Profile System (CRITICAL - 4 hours)

**1. Profile Edit Screen** ✅ Backend Ready: PUT /api/auth/profile
```
File: /app/frontend/app/profile/edit.tsx
Lines: ~400

Required Features:
✅ Profile photo upload area
✅ Change photo action (library + camera)
✅ Remove photo action
✅ Full name input
✅ Bio textarea (multiline)
✅ Business/salon name input
✅ City input
✅ Specialties input
✅ Instagram handle input
✅ TikTok handle input
✅ Website URL input
✅ Save button
✅ Loading state during save
✅ Success feedback
✅ Error handling
✅ Validation (required fields)
✅ Keyboard handling
✅ Safe area handling
✅ Dark theme styling

Backend Connection:
- GET /api/auth/me (load current data)
- PUT /api/auth/profile (save changes)

State Management:
- Local form state
- Image state (base64)
- Loading state
- Error state

Photo Upload Flow:
- Request permissions (camera/library)
- Show action sheet
- Handle selection
- Convert to base64
- Upload to server
- Show preview
- Handle errors
```

**2. Photo Upload Component** ✅ Expo ImagePicker + Camera installed
```
Component: /app/frontend/components/PhotoUploader.tsx
Lines: ~250

Required Features:
✅ Action sheet (Take Photo / Choose from Library / Remove)
✅ Camera permission request
✅ Library permission request
✅ Permission denial handling
✅ Image compression (for performance)
✅ Base64 conversion
✅ Upload progress indicator
✅ Preview after upload
✅ Remove functionality
✅ Placeholder when empty
✅ Error states

Usage:
- Profile photo upload
- Portfolio photo upload
- Client photo upload

Integration:
- expo-image-picker
- expo-camera
- AsyncStorage for persistence
```

### BATCH 2: Discovery & Community (CRITICAL - 4 hours)

**3. Discovery/Search Screen** ✅ Backend Ready: GET /api/users/discover
```
File: /app/frontend/app/tabs/discover.tsx
Lines: ~350

Required Features:
✅ Search input (name, business, city, specialty)
✅ Search debouncing (300ms)
✅ User result cards
✅ User avatar/photo
✅ Name, business, city display
✅ Specialties tags
✅ Tap to open profile
✅ Pull to refresh
✅ Loading state
✅ Empty state with guidance
✅ No results state
✅ Error handling
✅ Smooth scrolling (FlatList)
✅ Dark theme styling

Backend Connection:
- GET /api/users/discover?search=query

Navigation:
- Tap user card → /discover/[id]

Empty State:
"Discover talented stylists in your area. Search by name, specialty, or city."
```

**4. User Profile View Screen** ✅ Backend Ready: GET /api/users/{id}/profile
```
File: /app/frontend/app/discover/[id].tsx
Lines: ~500

Required Features:
✅ Profile photo (large)
✅ Name & business name
✅ Bio text
✅ City display
✅ Specialties tags
✅ Social links (Instagram, TikTok, website) - tappable
✅ Follow/Unfollow button
✅ Connection status indicator
✅ Followers/Following counts
✅ Portfolio preview grid (if images exist)
✅ Back navigation
✅ Loading state
✅ Error handling (user not found, private profile)
✅ Dark theme styling

Backend Connection:
- GET /api/users/{id}/profile
- POST /api/users/{id}/follow
- DELETE /api/users/{id}/follow

Button States:
- Not following: "Follow" button (gold)
- Following: "Following" button (outlined) with unfollow action

Social Links:
- Validate URLs before opening
- Open in external browser (Linking.openURL)
- Handle errors gracefully

Portfolio Preview:
- Show first 6 images in grid
- Tap to view full portfolio (if implemented)
```

**5. Follow System UI** ✅ Backend Ready
```
Integration in:
- User Profile View (/discover/[id].tsx)
- Following List (if created)

Features:
✅ Follow button with loading state
✅ Unfollow confirmation dialog
✅ Instant UI update
✅ Follower count update
✅ Following count update
✅ Error handling
✅ No duplicate requests

State Management:
- Track local following status
- Update counts immediately
- Refresh from server if needed
```

### BATCH 3: Portfolio (HIGH - 3 hours)

**6. Portfolio Management Screen** ✅ Backend Ready: POST/GET/DELETE /api/portfolio
```
File: /app/frontend/app/portfolio/index.tsx
Lines: ~400

Required Features:
✅ Add photo button (prominent)
✅ Photo grid display (2-3 columns)
✅ Image thumbnails
✅ Tap to preview (modal or new screen)
✅ Long press to delete
✅ Delete confirmation
✅ Caption support (optional)
✅ Pull to refresh
✅ Loading state
✅ Empty state with guidance
✅ Upload progress
✅ Error handling
✅ Dark theme styling

Backend Connection:
- GET /api/portfolio (load user's portfolio)
- POST /api/portfolio (upload image)
- DELETE /api/portfolio/{id} (remove image)

Photo Upload:
- Same PhotoUploader component
- Camera + library support
- Base64 conversion
- Upload to server

Empty State:
"Showcase your best work. Upload before & after photos to build your portfolio."

Grid Layout:
- 2-3 columns
- Equal height items
- Smooth scrolling
- Image optimization
```

### BATCH 4: Navigation & Integration (MEDIUM - 2 hours)

**7. Navigation Updates**
```
Files to Update:
- /app/frontend/app/tabs/_layout.tsx (add Discover tab)
- /app/frontend/app/tabs/more.tsx (add Profile & Portfolio links)
- /app/frontend/app/settings/index.tsx (add Privacy Settings link)

Changes:
✅ Add Discover tab to bottom navigation
✅ Profile menu item in More tab
✅ Portfolio menu item in More tab
✅ Privacy Settings in Settings
✅ Connections in Settings (if implemented)
✅ Blocked Users in Settings (if implemented)

Tab Order:
1. Dashboard
2. Clients
3. Appointments
4. Discover ← NEW
5. More
```

**8. Privacy Settings Screen** ✅ Backend Ready: GET/PUT /api/privacy/settings
```
File: /app/frontend/app/settings/privacy.tsx
Lines: ~300

Required Features:
✅ Profile Visibility toggle (Public/Private)
✅ Nearby Discovery toggle (OFF by default)
✅ Contacts Discovery toggle (OFF by default)
✅ Explanation text for each setting
✅ Warning messages
✅ Save button
✅ Loading state
✅ Success feedback
✅ Error handling
✅ Dark theme styling

Backend Connection:
- GET /api/privacy/settings (load current settings)
- PUT /api/privacy/settings (save changes)

Warnings:
- Private profile: "Only connections can view your full profile"
- Nearby: "Share your general area with nearby stylists"
- Contacts: "Find stylists from your phone contacts"
```

**9. Connections List Screen** ✅ Backend Ready: GET /api/connections, DELETE /api/connections/{id}
```
File: /app/frontend/app/connections/index.tsx
Lines: ~300

Required Features:
✅ List all connections
✅ User cards with avatar, name, city
✅ Tap to view profile
✅ Swipe to remove (or menu)
✅ Remove confirmation
✅ Pull to refresh
✅ Empty state
✅ Loading state
✅ Error handling
✅ Dark theme styling

Backend Connection:
- GET /api/connections
- DELETE /api/connections/{id}

Empty State:
"Connect with other stylists to share ideas and grow together."

Remove Flow:
1. Swipe left or tap menu
2. Confirm: "Remove [Name] from connections?"
3. Delete from server
4. Remove from list immediately
```

### BATCH 5: Visual Polish (LOW - 2 hours)

**10. Apply Dark Theme Consistently**
```
Files to Update:
- Dashboard (refine)
- Clients screens
- Appointments screens
- Gallery
- AI Chat
- All forms and inputs

Changes:
✅ Use Colors.background (#0A0A0A)
✅ Use Colors.backgroundCard (#1C1C1C)
✅ Use Colors.accent (#C9A86A)
✅ Use Colors.text (#FFFFFF)
✅ Consistent shadows
✅ Consistent spacing
✅ Consistent typography
✅ Premium feel throughout
```

**11. Empty States**
```
Replace all with EmptyState component:
✅ Clients: "Build your client base"
✅ Appointments: "Stay fully booked"
✅ Gallery: "Showcase your work"
✅ Discovery: "Find talented stylists"
✅ Connections: "Connect with stylists"
✅ Portfolio: "Build your portfolio"
```

### BATCH 6: Testing & QA (CRITICAL - 2 hours)

**12. Comprehensive Testing**
```
Test All 13 Flows:
1. ✅ Open edit profile screen
2. ✅ Upload/change/remove profile photo
3. ✅ Save profile updates
4. ✅ Profile persists after logout/login
5. ✅ Open discovery screen
6. ✅ Search returns users
7. ✅ Tap user opens profile
8. ✅ Follow/unfollow works
9. ✅ Open portfolio
10. ✅ Upload/remove portfolio images
11. ✅ All navigation works
12. ✅ No dead buttons/placeholders
13. ✅ Mobile layout works correctly

Bug Fixes:
- Fix any navigation issues
- Fix any state issues
- Fix any rendering issues
- Fix any permission issues
```

---

## IMPLEMENTATION SUMMARY

**Total Work Required: ~17 hours**
- Profile System: 4 hours
- Discovery & Community: 4 hours
- Portfolio: 3 hours
- Navigation: 2 hours
- Visual Polish: 2 hours
- Testing & QA: 2 hours

**Files to Create: ~10**
- profile/edit.tsx
- tabs/discover.tsx
- discover/[id].tsx
- portfolio/index.tsx
- settings/privacy.tsx
- connections/index.tsx
- components/PhotoUploader.tsx
- Plus navigation updates

**Backend Connection Points: ~15 APIs**
- All already exist and tested
- Just need frontend wiring

**Current Completion: 15%**
**After This Work: 100%**

---

## SUCCESS CRITERIA

**Must Have:**
1. All 10 screens built and functional
2. All navigation wiring complete
3. All backend endpoints connected
4. Photo upload working (camera + library)
5. All 13 QA flows passing
6. Zero dead buttons
7. Zero placeholders
8. Zero broken routes
9. Premium dark theme throughout
10. Mobile-optimized layouts

**Quality Bar:**
- Production-ready code
- Proper error handling
- Loading states everywhere
- Success feedback
- No silent failures
- Clean navigation
- Professional UI
- Performant on mobile

---

## NEXT STEPS

**Immediate Action:**
Start with Profile Edit Screen (highest impact, unlocks profile system)

**Then:**
Discovery Screen (unlocks community)

**Then:**
User Profile View (completes discovery flow)

**Then:**
Portfolio (completes creator showcase)

**Then:**
Navigation & Polish

**Finally:**
Testing & QA

**Estimated Delivery:**
2-3 focused work sessions to complete all Phase 2 frontend.

**No Blockers:**
All backend APIs exist and work. Just need to build UI screens.
