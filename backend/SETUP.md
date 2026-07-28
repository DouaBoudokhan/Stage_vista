# 🚀 Quick Setup Guide - StockIT Backend

Follow these steps to get your backend running in **10 minutes**!

---

## Step 1: Install Python

**Check if installed:**
```bash
python --version
```

If not installed, download Python 3.11+ from: https://www.python.org/downloads/

✅ Check "Add Python to PATH" during installation

---

## Step 2: Create Virtual Environment

```bash
cd backend
python -m venv venv
```

**Activate it:**

Windows:
```bash
venv\Scripts\activate
```

Mac/Linux:
```bash
source venv/bin/activate
```

You should see `(venv)` in your terminal.

---

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This will take 2-3 minutes. ☕

---

## Step 4: Setup Supabase (Free Database)

### Option A: Use Supabase (Recommended)

1. Go to https://supabase.com/
2. Sign up (free)
3. Create new project
4. Go to **Settings** → **Database**
5. Copy **Connection String** (URI format)
6. Replace `[YOUR-PASSWORD]` with your password

Example:
```
postgresql://postgres.abc123:your-password@aws-0-us-east-1.pooler.supabase.com:5432/postgres
```

### Option B: Use SQLite (Quick Start)

For testing, use SQLite instead:

In `.env`:
```
DATABASE_URL=sqlite:///./stockit.db
```

---

## Step 5: Configure .env File

Create `.env` file in `backend/` folder:

```env
# Database (use your Supabase connection string)
DATABASE_URL=postgresql://user:password@host:port/database

# JWT Secret (generate with command below)
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI Models
YOLO_MODEL_PATH=models_ai/best.pt

# App
DEBUG=True
ALLOWED_ORIGINS=http://localhost:3000,exp://192.168.*
```

**Generate SECRET_KEY:**
```bash
# Windows PowerShell
python -c "import secrets; print(secrets.token_hex(32))"

# Mac/Linux
openssl rand -hex 32
```

Copy the output and paste as your `SECRET_KEY`.

---

## Step 6: Start the Server! 🎉

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or double-click: `start.bat` (Windows) / `start.sh` (Mac/Linux)

You should see:
```
🚀 Starting StockIT API v1.0.0
📊 Initializing database...
✅ Database initialized
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## Step 7: Test the API

Open browser: http://localhost:8000/docs

You'll see **Swagger UI** with all API endpoints! 🎊

---

## Step 8: Create First User

Click on `POST /api/v1/auth/register` in Swagger UI:

```json
{
  "email": "admin@stockit.com",
  "name": "Admin User",
  "password": "password123",
  "role": "admin"
}
```

Click **Execute**

---

## Step 9: Login

Click on `POST /api/v1/auth/login`:

```json
{
  "email": "admin@stockit.com",
  "password": "password123"
}
```

Copy the `access_token` from response.

---

## Step 10: Authorize in Swagger

1. Click **🔒 Authorize** button (top right)
2. Paste your token
3. Click **Authorize**
4. Now you can test all protected endpoints!

---

## 🎯 Connect to Mobile App

Find your computer's IP address:

**Windows:**
```bash
ipconfig
```
Look for **IPv4 Address** (e.g., 192.168.1.100)

**Mac/Linux:**
```bash
ifconfig
```

Update mobile app config:

File: `mobile/constants/config.ts`
```typescript
export const API_BASE_URL = 'http://192.168.1.100:8000/api/v1';
```

**Important:** Use your actual IP, not localhost!

---

## ✅ You're Done!

Backend is running! Your mobile app can now:
- ✅ Login users
- ✅ Manage products
- ✅ Track inventory
- ✅ Scan items (when AI is configured)

---

## 🔧 Optional: AI Features

### YOLO Object Detection

1. Train or download a YOLO model
2. Place `best.pt` in `backend/models_ai/`
3. Restart server

Default YOLOv8 will auto-download if no model found.

### Tesseract OCR

**Windows:**
1. Download: https://github.com/UB-Mannheim/tesseract/wiki
2. Install
3. Add to PATH

**Mac:**
```bash
brew install tesseract
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

---

## 🆘 Need Help?

**Server won't start?**
- Check if Python is in PATH
- Make sure port 8000 is free
- Check `.env` file exists

**Database error?**
- Verify Supabase connection string
- Check password is correct
- Try SQLite for quick testing

**Can't connect from mobile?**
- Use your computer's IP, not localhost
- Make sure firewall allows port 8000
- Ensure both devices on same WiFi

---

**🎉 Happy coding!**
