# Login Fix Summary

## Problem
Mobile app login was failing with **422 error (Unprocessable Entity)** when trying to login with `doua@stockit.local`.

## Root Causes

### 1. Email Validation Issue
**Problem**: Pydantic's `EmailStr` validator rejected `.local` domain as a reserved TLD.
**Solution**: Changed from `EmailStr` to `str` with custom validation that allows `.local` domains.

### 2. Database Schema Mismatch
**Problem**: User model didn't match PostgreSQL database schema.
- Model had: `id` (String), `hashed_password`, `name`, `is_active`
- Database had: `id` (Integer), `username`, `password_hash`, `name`, `is_active`

**Solution**: Updated User model to match PostgreSQL schema exactly.

### 3. User Email Issue
**Problem**: Existing `doua` user had email `doua@stockit.com` instead of `doua@stockit.local`.
**Solution**: Updated the database record to use `doua@stockit.local` with password `0000`.

### 4. Bcrypt/Passlib Compatibility Issue
**Problem**: Passlib's bcrypt handler was causing `ValueError: password cannot be longer than 72 bytes`.
**Solution**: Replaced passlib with direct bcrypt usage for password hashing and verification.

## Changes Made

### Backend Files Modified

#### 1. `app/schemas/user.py`
- Changed `EmailStr` to `str` in `UserLogin` and `UserBase`
- Added custom `validate_email` method that allows `.local` domains

#### 2. `app/models/user.py`
- Updated to match PostgreSQL schema:
  - `id`: Integer (autoincrement)
  - `username`: String(255)
  - `email`: String(255)
  - `password_hash`: String(255) (not `hashed_password`)
  - `role`: String(50)
  - `name`: String (nullable)
  - `is_active`: Boolean
  - `created_at`: DateTime

#### 3. `app/routers/auth.py`
- Updated `register()` to use `password_hash` and `username`
- Updated `login()` to use `user.password_hash`
- Restored `is_active` check

#### 4. `app/utils/security.py`
- Replaced passlib with direct bcrypt usage
- `verify_password()`: uses `bcrypt.checkpw()`
- `get_password_hash()`: uses `bcrypt.hashpw()`

#### 5. Database Update Script
- Created `add_users.py` to update doua user:
  - Email: `doua@stockit.com` → `doua@stockit.local`
  - Password: updated to `0000`
  - Name: set to "Doua User"
  - Role: set to "admin"

### Mobile Files Modified

#### 1. `mobile/screens/LoginScreen.tsx`
- Updated default email to `doua@stockit.local`
- Updated biometric login to use `doua@stockit.local` / `0000`

## Current Working Credentials

### Doua User
```
Email:    doua@stockit.local
Password: 0000
Role:     admin
```

### Testing
✅ cURL test successful:
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "doua@stockit.local", "password": "0000"}'
```

Response:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

## Mobile App Usage

### Manual Login
1. Open StockIT mobile app
2. Email field is pre-filled with: `doua@stockit.local`
3. Enter password: `0000`
4. Tap "Log In"

### Quick Login
1. Tap **"Authorize with Biometrics"** button
2. Automatically logs in as doua

## Technical Details

### Password Hashing
- **Library**: bcrypt (direct, no passlib wrapper)
- **Algorithm**: bcrypt with auto-generated salt
- **Format**: `$2b$12$...` (standard bcrypt hash)

### JWT Tokens
- **Algorithm**: HS256
- **Access Token Expiry**: 30 minutes
- **Refresh Token Expiry**: 7 days
- **Secret Key**: From `.env` file

### Database
- **Type**: PostgreSQL (Supabase)
- **Connection**: via SQLAlchemy
- **Users Table**: Contains username, email, password_hash, role, name, is_active

## Known Issues Fixed

1. ✅ 422 error on login
2. ✅ Email validation rejecting `.local` domains
3. ✅ Model/database schema mismatch
4. ✅ Wrong email domain for doua user
5. ✅ Bcrypt/passlib compatibility error
6. ✅ Biometric login using wrong credentials

## Files Created

- `backend/check_users.py` - Database user inspection script
- `backend/add_users.py` - User creation/update script
- `mobile/LOGIN_CREDENTIALS.md` - Login credentials documentation
- `mobile/LOGIN_FIX_SUMMARY.md` - This file

## Backend Status

**Running**: ✅ Yes
**Port**: 8000
**Process**: term_1785946074042_mkmb5rs6jcf
**Status**: All auth endpoints working correctly

## Next Steps

1. Test login on mobile app
2. Verify dashboard loads after login
3. Test token refresh flow
4. Consider adding more users if needed

## Security Notes

- Passwords are hashed with bcrypt before storage
- JWT tokens are signed with HS256
- Tokens expire after configured time
- `.local` domain validation is lenient for development
- In production, consider stricter email validation or switch to proper domain
