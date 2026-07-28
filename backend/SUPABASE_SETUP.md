# 🗄️ Connect to Supabase - Quick Guide

## ✅ Step-by-Step Instructions

### 1. Create Supabase Account (2 minutes)

1. Go to: **https://supabase.com/**
2. Click **"Start your project"**
3. Sign up (FREE - no credit card needed!)

---

### 2. Create New Project (2 minutes)

1. Click **"New Project"** button
2. Fill in details:
   - **Organization:** Create new or use existing
   - **Project Name:** `stockit-db` (or any name you want)
   - **Database Password:** Choose a strong password
   
   ⚠️ **IMPORTANT:** Save this password! You'll need it.
   
   - **Region:** Choose closest to you (e.g., `US East`)
   - **Pricing Plan:** `Free` (perfect for development)

3. Click **"Create new project"**

⏳ Wait 1-2 minutes while Supabase creates your database...

---

### 3. Get Your Connection String (1 minute)

Once your project is ready:

1. Click **⚙️ Settings** (bottom left sidebar)
2. Click **"Database"** 
3. Scroll down to **"Connection string"** section
4. Select **"URI"** tab (NOT "Transaction pooler" or "Session")
5. You'll see:

```
postgresql://postgres.xxxxxx:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:5432/postgres
```

6. **Click "Copy"** button
7. Replace `[YOUR-PASSWORD]` with your actual database password

**Example:**
```
Before: postgresql://postgres.abc123:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:5432/postgres
After:  postgresql://postgres.abc123:MySecretPass123@aws-0-us-east-1.pooler.supabase.com:5432/postgres
```

---

### 4. Update .env File (30 seconds)

1. Open: `backend/.env`
2. Find this line:
```env
DATABASE_URL=postgresql://postgres.xxxxxx:YOUR-PASSWORD-HERE@...
```

3. Replace it with your Supabase connection string

**Example:**
```env
DATABASE_URL=postgresql://postgres.abc123:MySecretPass123@aws-0-us-east-1.pooler.supabase.com:5432/postgres
```

4. Save the file

✅ **Done!** Your backend is now connected to Supabase!

---

### 5. Test Connection (1 minute)

Start your backend server:

```bash
uvicorn app.main:app --reload
```

You should see:
```
🚀 Starting StockIT API v1.0.0
📊 Initializing database...
✅ Database initialized
INFO:     Uvicorn running on http://0.0.0.0:8000
```

If you see this - **SUCCESS!** 🎉

Open: http://localhost:8000/health

You should see:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "ai_services": "ready"
}
```

---

## 🔍 Visual Guide

### Finding Connection String in Supabase:

```
Supabase Dashboard
├── Your Project
│   └── ⚙️ Settings (left sidebar)
│       └── Database
│           └── Connection string
│               └── URI ← Click here!
│                   └── Copy the string
```

---

## ✅ Checklist

- [ ] Created Supabase account
- [ ] Created new project
- [ ] Saved database password
- [ ] Copied connection string (URI format)
- [ ] Replaced `[YOUR-PASSWORD]` with actual password
- [ ] Updated `backend/.env` file
- [ ] Started backend server
- [ ] Tested `/health` endpoint

---

## 🆘 Troubleshooting

### "Connection refused" or "Connection timeout"

**Check:**
1. ✅ Is your Supabase project active? (green dot in dashboard)
2. ✅ Did you replace `[YOUR-PASSWORD]` with the actual password?
3. ✅ Is the connection string in the correct format?
4. ✅ Are you connected to the internet?

### "Authentication failed"

**Fix:**
- Your password is wrong
- Get a new connection string from Supabase
- Make sure there are NO spaces in the password

### "Could not translate host name"

**Fix:**
- Your connection string is incorrect
- Copy it again from Supabase (URI format, not Transaction)

---

## 📸 Screenshot Guide

### Step 1: Find Settings
![Settings Location](https://supabase.com/docs/img/database-settings.png)
Look for ⚙️ icon in bottom left

### Step 2: Database Section
Click "Database" in settings menu

### Step 3: Connection String
Scroll to "Connection string" → Click "URI" tab → Click Copy

---

## 💡 Pro Tips

### Free Tier Limits (Supabase)
- ✅ 500 MB database storage
- ✅ Unlimited API requests
- ✅ Perfect for development
- ✅ No credit card required

### Security
- 🔒 Never commit `.env` to Git (already in `.gitignore`)
- 🔒 Keep your database password secret
- 🔒 Change password if accidentally exposed

### Using Multiple Environments

**Development (.env):**
```env
DATABASE_URL=postgresql://...supabase.com.../postgres
```

**Production (.env.production):**
```env
DATABASE_URL=postgresql://...production-db.../postgres
```

---

## 🎯 Next Steps

Once connected:

1. ✅ Start backend: `uvicorn app.main:app --reload`
2. ✅ Open Swagger docs: http://localhost:8000/docs
3. ✅ Create first user (register endpoint)
4. ✅ Login and get token
5. ✅ Test API endpoints
6. ✅ Connect mobile app

---

## 📞 Need Help?

**Supabase Docs:** https://supabase.com/docs/guides/database
**FastAPI Docs:** https://fastapi.tiangolo.com/

---

**You're almost there! Just copy-paste your connection string and you're done! 🚀**
