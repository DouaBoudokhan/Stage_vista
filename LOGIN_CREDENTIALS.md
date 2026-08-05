# StockIT Login Credentials

## Mobile App Login

### Method 1: Manual Login
1. Open the StockIT mobile app
2. Enter credentials:
   - **Email**: `doua@stockit.local` or `admin@stockit.local`
   - **Password**: `0000` (for doua) or `admin123` (for admin)
3. Tap "Log In"

### Method 2: Quick Biometric Login
1. Tap **"Authorize with Biometrics"** button
2. Automatically logs in as admin

---

## Available User Accounts

### Doua User (Your Account)
```
Email:    doua@stockit.local
Username: doua
Password: 0000
Role:     admin
```

### Admin User (Default)
```
Email:    admin@stockit.local
Username: admin
Password: admin123
Role:     admin
```

---

## Backend API

**Base URL**: `http://localhost:8000`

**Auth Endpoint**: `POST /auth/login`

**Request Body**:
```json
{
  "email": "doua@stockit.local",
  "password": "0000"
}
```

**Response**:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

---

## Database Access

**Database File**: `c:\Users\USER\Downloads\stockit\backend\stockit.db`

**Users Table Query**:
```sql
SELECT username, email, role FROM users;
```

Expected Results:
```
username | email                | role
---------|---------------------|------
doua     | doua@stockit.local  | admin
admin    | admin@stockit.local | admin
```

---

## Troubleshooting

### "Incorrect email or password"
- Make sure you're using the correct email domain: `@stockit.local`
- Password for doua is `0000` (four zeros)
- Password for admin is `admin123`

### "User not found"
- The backend server must be running on port 8000
- Check backend logs for user seeding confirmation
- Users are auto-created on first backend startup

### Backend not running
Start the backend:
```bash
cd c:\Users\USER\Downloads\stockit\backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Reset password
To change a password, use the backend API or update directly in database:
```python
from app.utils.security import get_password_hash
new_hash = get_password_hash("new_password")
# Update database: UPDATE users SET password_hash = new_hash WHERE email = 'doua@stockit.local'
```

---

## Security Notes

- Default passwords should be changed in production
- Passwords are hashed using bcrypt
- JWT tokens are used for authentication
- Tokens expire after configured time (default: 30 minutes for access token)

---

## Files Modified

### Mobile App
- `mobile/screens/LoginScreen.tsx`
  - Updated default email to `admin@stockit.local`
  - Updated biometric login to use admin credentials

### Backend
- `backend/app/database.py`
  - Added user seeding on database initialization
  - Creates both admin and doua users automatically
- `backend/app/routers/auth.py`
  - Fixed to match User model schema (password_hash instead of hashed_password)
  - Removed is_active check (column doesn't exist)

---

## Quick Reference

**Current Working Credentials:**
- doua@stockit.local / 0000 ✅
- admin@stockit.local / admin123 ✅

**Backend Status**: Running on http://localhost:8000 ✅
**User Seeding**: Automatic on startup ✅
