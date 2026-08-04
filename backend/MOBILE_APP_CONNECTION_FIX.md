# Mobile App Connection Issue - Fix Guide

## Problem
Mobile app shows "No Tickets Available" even though:
- ✅ Jira connection works
- ✅ Backend is running
- ✅ `/tickets` endpoint returns data

## Root Cause
**Network connectivity issue** between mobile app and backend server.

---

## Your Current Setup

### Backend Server
- **Status**: ✅ Running
- **Address**: `http://0.0.0.0:8000` (listening on all interfaces)
- **Test URL**: `http://localhost:8000/tickets`

### Your Computer's IP Addresses
- **Wi-Fi**: `172.18.221.31` ← **Use this one!**
- VMware NAT: `192.168.37.1`
- VMware Host-only: `192.168.93.1`
- WSL: `172.26.176.1`

### Mobile App Configuration
- **Current config**: `http://192.168.1.16:8000` (might be outdated)
- **Should be**: `http://172.18.221.31:8000` (your current Wi-Fi IP)

---

## Fix #1: Update Mobile App IP Address

### Method A: Using Environment Variable (Recommended)

1. **Create `.env` file in mobile directory**:
   ```bash
   cd mobile
   echo "EXPO_PUBLIC_API_URL=http://172.18.221.31:8000" > .env
   ```

2. **Restart Expo**:
   ```bash
   npm start
   # Then press 'r' to reload
   ```

### Method B: Hardcode in config (Quick Test)

1. **Edit `mobile/constants/config.ts`**:
   ```typescript
   export const API_BASE_URL: string = "http://172.18.221.31:8000";
   ```

2. **Restart mobile app**

---

## Fix #2: Verify Network Connectivity

### Test from Your Computer
```bash
# Test if backend is accessible
curl http://172.18.221.31:8000/health

# Test tickets endpoint
curl http://172.18.221.31:8000/tickets
```

### Test from Mobile Device

**Option A: Using Mobile Browser**
1. Open Safari/Chrome on your phone
2. Navigate to: `http://172.18.221.31:8000/health`
3. You should see: `{"status":"healthy",...}`

**Option B: Check Expo DevTools**
1. Look at the Expo DevTools console
2. Check for network errors when fetching tickets

---

## Fix #3: Firewall Configuration

### Windows Firewall Might Block External Connections

**Allow Python through Firewall**:

```powershell
# Run as Administrator
New-NetFirewallRule -DisplayName "Python FastAPI" -Direction Inbound -Program "C:\Users\USER\AppData\Local\Programs\Python\Python311\python.exe" -Action Allow
```

Or manually:
1. Windows Security → Firewall & network protection
2. Allow an app through firewall
3. Find "Python" and check both Private and Public

---

## Fix #4: Check Mobile App is Making Requests

### Add Debug Logging

The mobile app already has HTTP logging in `mobile/api/axios.ts`. Check the logs for:

```
[http] REQUEST: GET http://172.18.221.31:8000/tickets
[http] RESPONSE ERROR: Network Error / Timeout
```

**Common errors**:
- `Network Error` → Mobile can't reach backend (wrong IP or firewall)
- `401 Unauthorized` → Authentication issue (already fixed)
- `503 Service Unavailable` → Jira not configured (not your case)

---

## Quick Verification Steps

### Step 1: Check Backend is Running
```bash
curl http://localhost:8000/health
```
**Expected**: `{"status":"healthy",...}`

### Step 2: Check Backend is Accessible from Network
```bash
curl http://172.18.221.31:8000/health
```
**Expected**: Same response as above

### Step 3: Test Tickets Endpoint
```bash
curl http://172.18.221.31:8000/tickets
```
**Expected**: Array of tickets from Jira (might be empty if no "Open" tickets)

### Step 4: Update Mobile App IP
Edit `mobile/.env`:
```
EXPO_PUBLIC_API_URL=http://172.18.221.31:8000
```

### Step 5: Restart Mobile App
```bash
cd mobile
npm start
# Press 'r' to reload
```

### Step 6: Test Login
1. Open app
2. Login with: `admin@stockit.local` / `admin123`
3. Navigate to Stock Entry → All Tickets tab
4. Should see tickets now!

---

## Still Not Working?

### Check These:

1. **Mobile and Computer on Same Wi-Fi?**
   - Phone must be on same network as computer
   - Corporate networks might block device-to-device communication

2. **VPN Active?**
   - Disable VPN on computer or phone
   - VPN can change routing

3. **IP Address Changed?**
   - Run `ipconfig` and check your current IP
   - Update mobile config if IP changed

4. **Backend Logs**
   - Check terminal where backend is running
   - Look for incoming requests from mobile IP

5. **Port 8000 Blocked?**
   - Try different port: `--port 8080`
   - Update mobile config accordingly

---

## Alternative: Use Expo Tunnel (If Network Issues Persist)

If direct IP connection doesn't work (corporate network restrictions):

```bash
cd mobile
npx expo start --tunnel
```

This creates a public URL that works from anywhere.

---

## Testing Checklist

- [ ] Backend running on `http://0.0.0.0:8000`
- [ ] Health check works: `curl http://localhost:8000/health`
- [ ] Network health check works: `curl http://172.18.221.31:8000/health`
- [ ] Tickets endpoint works: `curl http://172.18.221.31:8000/tickets`
- [ ] Mobile `.env` has correct IP
- [ ] Mobile app restarted
- [ ] Login works
- [ ] Tickets load in "All Tickets" tab

---

## Success Looks Like:

### Mobile App Console:
```
[http] REQUEST: GET http://172.18.221.31:8000/tickets
[http] RESPONSE: 200
[http] RESPONSE BODY: [{jira_key: "SD-235533", title: "Display issue", ...}]
```

### Backend Console:
```
INFO:     172.18.221.25:54321 - "GET /tickets HTTP/1.1" 200 OK
```

### Mobile App UI:
- **All Tickets tab** shows list of tickets from Jira
- **AI Recommendation** button works
- No "No Tickets Available" error

---

## Quick Command Reference

```bash
# Find your IP
ipconfig | findstr "IPv4"

# Start backend
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Test locally
curl http://localhost:8000/tickets

# Test from network
curl http://172.18.221.31:8000/tickets

# Update mobile config
cd mobile
echo "EXPO_PUBLIC_API_URL=http://172.18.221.31:8000" > .env

# Restart mobile
npm start
```

---

**TL;DR**: Update mobile app to use `http://172.18.221.31:8000` instead of `http://192.168.1.16:8000`
