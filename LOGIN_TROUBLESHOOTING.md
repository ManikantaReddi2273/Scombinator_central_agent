# Login Troubleshooting Guide

## Issue: Cannot Login as Admin

If you're stuck on "Signing in..." or getting login errors, follow these steps:

---

## ✅ Step 1: Check if Backend is Running

### Check Backend Status

1. **Open a new terminal/PowerShell window**
2. **Navigate to backend folder:**
   ```powershell
   cd "C:\Users\ManishReddy\OneDrive\Desktop\S Combinator _Central Agent Platform\backend"
   ```

3. **Check if backend is running:**
   - Open browser: http://localhost:8000/health
   - Should return: `{"status": "healthy"}`
   - If you get "Connection refused" or "This site can't be reached" → **Backend is NOT running**

### Start Backend

If backend is not running:

```powershell
cd "C:\Users\ManishReddy\OneDrive\Desktop\S Combinator _Central Agent Platform\backend"
python main.py
```

**Expected output:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Keep this terminal open!** The backend must be running.

---

## ✅ Step 2: Check Database Connection

### Verify PostgreSQL is Running

1. **Check if PostgreSQL service is running:**
   ```powershell
   Get-Service -Name postgresql*
   ```
   Should show "Running"

2. **If not running, start it:**
   ```powershell
   Start-Service postgresql-x64-15  # Adjust version number if different
   ```

### Verify Database Exists

1. **Connect to PostgreSQL:**
   ```powershell
   psql -U postgres
   ```

2. **Check if database exists:**
   ```sql
   \l
   ```
   Look for `s_combinator` database

3. **If database doesn't exist, create it:**
   ```sql
   CREATE DATABASE s_combinator;
   \q
   ```

---

## ✅ Step 3: Initialize Database and Create Admin User

### Run Database Initialization

1. **In backend folder, run:**
   ```powershell
   cd "C:\Users\ManishReddy\OneDrive\Desktop\S Combinator _Central Agent Platform\backend"
   python init_db.py
   ```

2. **Expected output:**
   ```
   Initializing database...
   Database tables created
   [OK] Admin user created: reddimanikanta2005@gmail.com
      Password: R@ddi2273 (encrypted in database)
   Database initialization complete!
   ```

   OR if admin already exists:
   ```
   [OK] Admin user already exists: reddimanikanta2005@gmail.com
   ```

---

## ✅ Step 4: Verify Environment Variables

### Check .env File

1. **Location:** `backend/.env`
2. **Required variables:**
   ```env
   ADMIN_EMAIL=reddimanikanta2005@gmail.com
   ADMIN_PASSWORD=R@ddi2273
   DATABASE_URL=postgresql+asyncpg://postgres:reddi2273@localhost:5432/s_combinator
   JWT_SECRET_KEY=your-secret-key
   ENCRYPTION_KEY=your-encryption-key
   ```

3. **If .env is missing or incomplete:**
   - Run: `setup_env.bat` (Windows)
   - Or manually create `.env` file with required variables

---

## ✅ Step 5: Test Login

### Test Backend API Directly

1. **Open browser or use curl:**
   ```powershell
   curl -X POST http://localhost:8000/api/auth/login -H "Content-Type: application/json" -d '{\"email\":\"reddimanikanta2005@gmail.com\",\"password\":\"R@ddi2273\"}'
   ```

2. **Expected response:**
   ```json
   {
     "access_token": "eyJhbGci...",
     "token_type": "bearer",
     "admin_email": "reddimanikanta2005@gmail.com",
     "role": "ADMIN"
   }
   ```

3. **If you get an error:**
   - Check backend terminal for error messages
   - Verify database connection
   - Verify admin user exists

### Test Frontend Login

1. **Make sure backend is running** (Step 1)
2. **Open frontend:** http://localhost:3000/login
3. **Enter credentials:**
   - Email: `reddimanikanta2005@gmail.com`
   - Password: `R@ddi2273`
4. **Click "Sign In"**

---

## 🐛 Common Errors and Solutions

### Error: "Cannot connect to backend server"

**Cause:** Backend is not running

**Solution:**
1. Start backend: `python main.py` in backend folder
2. Verify it's running: http://localhost:8000/health
3. Try login again

---

### Error: "Incorrect email or password"

**Cause:** Admin user doesn't exist or password is wrong

**Solution:**
1. Run `python init_db.py` to create admin user
2. Verify credentials in `.env` file match:
   - Email: `reddimanikanta2005@gmail.com`
   - Password: `R@ddi2273`

---

### Error: "Account is inactive"

**Cause:** Admin user exists but `is_active = False`

**Solution:**
1. Connect to database:
   ```sql
   psql -U postgres -d s_combinator
   ```
2. Update admin:
   ```sql
   UPDATE admins SET is_active = true WHERE email = 'reddimanikanta2005@gmail.com';
   ```

---

### Error: "Network Error" or "ECONNREFUSED"

**Cause:** Backend not running or wrong URL

**Solution:**
1. Check backend is running on port 8000
2. Verify frontend `.env` has: `VITE_API_URL=http://localhost:8000`
3. Restart frontend dev server

---

### Error: CORS Error

**Cause:** CORS configuration issue

**Solution:**
- Backend already allows all origins (`allow_origins=["*"]`)
- If still getting CORS error, check backend is running and accessible

---

## 🔍 Debug Steps

### 1. Check Browser Console

1. Open browser DevTools (F12)
2. Go to **Console** tab
3. Look for error messages
4. Go to **Network** tab
5. Try login again
6. Check the `/api/auth/login` request:
   - Status code (should be 200)
   - Response body
   - Error messages

### 2. Check Backend Logs

1. Look at backend terminal output
2. Check for error messages or stack traces
3. Common issues:
   - Database connection errors
   - Missing environment variables
   - Import errors

### 3. Verify All Services

**Checklist:**
- [ ] PostgreSQL is running
- [ ] Database `s_combinator` exists
- [ ] Backend is running on port 8000
- [ ] Frontend is running on port 3000
- [ ] `.env` file exists in backend folder
- [ ] Admin user exists in database
- [ ] No firewall blocking ports 3000 or 8000

---

## 🚀 Quick Fix Commands

**Run these in order:**

```powershell
# 1. Navigate to backend
cd "C:\Users\ManishReddy\OneDrive\Desktop\S Combinator _Central Agent Platform\backend"

# 2. Check if backend is running (in another terminal)
# Open http://localhost:8000/health in browser

# 3. If not running, start backend
python main.py

# 4. In a new terminal, initialize database
cd "C:\Users\ManishReddy\OneDrive\Desktop\S Combinator _Central Agent Platform\backend"
python init_db.py

# 5. Test login via API
curl -X POST http://localhost:8000/api/auth/login -H "Content-Type: application/json" -d '{\"email\":\"reddimanikanta2005@gmail.com\",\"password\":\"R@ddi2273\"}'
```

---

## 📞 Still Having Issues?

1. **Check backend terminal** for error messages
2. **Check browser console** (F12) for frontend errors
3. **Verify all services are running:**
   - PostgreSQL
   - Backend (port 8000)
   - Frontend (port 3000)
4. **Check database connection:**
   - Can you connect to PostgreSQL?
   - Does `s_combinator` database exist?
   - Does `admins` table exist?
   - Is there a row with your email?

---

**Last Updated:** 2026-02-04

