# StyleFlow Production Deployment Guide

## Overview
This guide covers deploying the StyleFlow backend to production for App Store submission.

---

## Option 1: Railway Deployment (Recommended - Easiest)

### Step 1: Create Railway Account
1. Go to https://railway.app
2. Sign up with GitHub

### Step 2: Deploy from GitHub
1. Click "New Project" → "Deploy from GitHub repo"
2. Select `dmmhc92-bot/style-flow-d`
3. Choose the `/backend` folder as root directory

### Step 3: Configure Environment Variables
In Railway dashboard, add these variables:

```
MONGO_URL=mongodb+srv://<your-atlas-connection-string>
JWT_SECRET=<generate-a-secure-random-string>
CLOUDINARY_CLOUD_NAME=<your-cloudinary-name>
CLOUDINARY_API_KEY=<your-cloudinary-key>
CLOUDINARY_API_SECRET=<your-cloudinary-secret>
OPENAI_API_KEY=<your-openai-key>
RESEND_API_KEY=<your-resend-key>
REVENUECAT_API_KEY=<your-revenuecat-key>
```

### Step 4: Custom Domain
1. In Railway project settings → Domains
2. Add custom domain: `api.homestyleflowapp.com`
3. Configure DNS at your registrar:
   - Add CNAME record: `api` → Railway provided domain

### Step 5: Update EAS Config
Update `/app/frontend/eas.json` production env:
```json
"EXPO_PUBLIC_BACKEND_URL": "https://api.homestyleflowapp.com"
```

---

## Option 2: Vercel Deployment

### Note: Vercel is better for static sites, but can work for FastAPI

### Step 1: Install Vercel CLI
```bash
npm i -g vercel
```

### Step 2: Create vercel.json in /backend
```json
{
  "builds": [{ "src": "server.py", "use": "@vercel/python" }],
  "routes": [{ "src": "/(.*)", "dest": "server.py" }]
}
```

### Step 3: Deploy
```bash
cd /app/backend
vercel --prod
```

---

## Option 3: DigitalOcean App Platform

### Step 1: Create App
1. Go to DigitalOcean → Apps
2. Connect GitHub repo
3. Select `/backend` as source directory

### Step 2: Configure
- Python version: 3.11
- Run command: `uvicorn server:app --host 0.0.0.0 --port 8080`
- Add environment variables

### Step 3: Domain
- Add custom domain in App settings

---

## MongoDB Atlas Setup (Required for all options)

### Step 1: Create Cluster
1. Go to https://cloud.mongodb.com
2. Create free M0 cluster
3. Choose closest region to your users

### Step 2: Database User
1. Security → Database Access
2. Add new user with read/write permissions
3. Save the password securely

### Step 3: Network Access
1. Security → Network Access
2. Add `0.0.0.0/0` to allow all IPs (or specific IPs for production)

### Step 4: Connection String
1. Clusters → Connect → Connect your application
2. Copy connection string
3. Replace `<password>` with your database user password
4. Replace `<dbname>` with `styleflow_production`

Example:
```
mongodb+srv://styleflow:YourPassword@cluster0.xxxxx.mongodb.net/styleflow_production?retryWrites=true&w=majority
```

---

## DNS Configuration for homestyleflowapp.com

### For API subdomain (recommended):
| Type | Name | Value |
|------|------|-------|
| CNAME | api | your-railway-app.railway.app |

### For root domain (if using for API):
| Type | Name | Value |
|------|------|-------|
| A | @ | Railway/Vercel IP |

---

## After Deployment Checklist

1. [ ] Backend responds at `https://api.homestyleflowapp.com/api/health`
2. [ ] Test login: `POST /api/auth/login`
3. [ ] Test signup: `POST /api/auth/signup`
4. [ ] Update EAS config with production URL
5. [ ] Trigger new EAS build
6. [ ] Test on TestFlight with production backend

---

## Quick Test Commands

```bash
# Health check
curl https://api.homestyleflowapp.com/api/health

# Test login
curl -X POST https://api.homestyleflowapp.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"appreview@apple.com","password":"TestPass123!"}'
```

---

## Tester Accounts (Already created in local DB)

You'll need to recreate these in your production MongoDB:

| Email | Password | Flags |
|-------|----------|-------|
| admin@styleflow.com | TestPass123! | is_admin=true |
| appreview@apple.com | TestPass123! | is_tester=true |

Use this script after deploying:
```python
# Run this against your production MongoDB
from motor.motor_asyncio import AsyncIOMotorClient
import bcrypt
import asyncio

MONGO_URL = "your-production-mongodb-url"
client = AsyncIOMotorClient(MONGO_URL)
db = client['styleflow_production']

async def create_accounts():
    password = bcrypt.hashpw("TestPass123!".encode(), bcrypt.gensalt()).decode()
    
    await db.users.update_one(
        {"email": "admin@styleflow.com"},
        {"$set": {
            "email": "admin@styleflow.com",
            "password": password,
            "full_name": "StyleFlow Admin",
            "is_admin": True,
            "is_tester": True,
            "is_premium": True,
            "subscription_status": "active"
        }},
        upsert=True
    )
    
    await db.users.update_one(
        {"email": "appreview@apple.com"},
        {"$set": {
            "email": "appreview@apple.com",
            "password": password,
            "full_name": "App Store Reviewer",
            "is_admin": False,
            "is_tester": True,
            "is_premium": True,
            "subscription_status": "active"
        }},
        upsert=True
    )
    
    print("Accounts created!")

asyncio.run(create_accounts())
```
