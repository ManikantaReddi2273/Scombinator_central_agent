# CORS & 500 Error Fix - Complete Solution

## ✅ Issues Fixed

### 1. CORS Error
- **Problem**: `allow_credentials=True` cannot be used with `allow_origins=["*"]`
- **Fix**: Changed to specific origins: `http://localhost:3000`, `http://127.0.0.1:3000`

### 2. 500 Internal Server Error
- **Problem**: Database connection or other backend errors
- **Fix**: Added exception handlers that always send CORS headers, even on errors

---

## 🔧 Changes Made

### `backend/main.py`

1. **Fixed CORS Configuration**:
   ```python
   allow_origins=[
       "http://localhost:3000",
       "http://127.0.0.1:3000",
       "http://localhost:3001",
       "http://127.0.0.1:3001",
   ]
   ```

2. **Added Exception Handlers**:
   - Ensures CORS headers are sent even when errors occur
   - Better error logging

3. **Enhanced OPTIONS Handler**:
   - Properly handles CORS preflight requests

---

## 🚀 CRITICAL: Restart Backend

**You MUST restart the backend for these changes to take effect!**

### Step 1: Stop Backend

In the terminal where backend is running:
- Press `Ctrl+C` to stop

### Step 2: Restart Backend

```powershell
cd "C:\Users\ManishReddy\OneDrive\Desktop\S Combinator _Central Agent Platform\backend"
.\.venv\Scripts\Activate.ps1
uv run python main.py
```

### Step 3: Verify Backend is Running

1. **Check health endpoint**:
   - Open: http://localhost:8000/health
   - Should show: `{"status": "healthy"}`

2. **Check CORS endpoint**:
   - Open: http://localhost:8000/health/cors
   - Should show: `{"status": "healthy", "cors": "enabled", ...}`

---

## 🐛 If 500 Error Persists

The 500 error suggests a **database connection issue**. Check:

### Step 1: Check Database Connection

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uv run python check_db_connection.py
```

**If database connection fails:**
1. **Check PostgreSQL is running**:
   ```powershell
   Get-Service -Name postgresql*
   ```

2. **Start PostgreSQL if not running**:
   ```powershell
   Start-Service postgresql-x64-15  # Adjust version if different
   ```

3. **Verify database exists**:
   ```powershell
   psql -U postgres -c "\l" | Select-String "s_combinator"
   ```

4. **Create database if missing**:
   ```powershell
   psql -U postgres -c "CREATE DATABASE s_combinator;"
   ```

5. **Initialize database**:
   ```powershell
   cd backend
   .\.venv\Scripts\Activate.ps1
   uv run python init_db.py
   ```

### Step 2: Check Backend Logs

Look at your backend terminal for error messages:
- Database connection errors
- Import errors
- Configuration errors

---

## ✅ Testing After Restart

### Test 1: CORS Headers

1. Open browser DevTools (F12)
2. Go to **Network** tab
3. Try to load companies in frontend
4. Click on the `/api/companies/` request
5. Check **Response Headers**:
   - Should see: `Access-Control-Allow-Origin: http://localhost:3000`
   - Should see: `Access-Control-Allow-Methods: ...`
   - Should see: `Access-Control-Allow-Headers: *`

### Test 2: API Call

1. Go to: http://localhost:3000
2. Login as admin
3. Navigate to **Companies** page
4. Should load without CORS errors
5. If 500 error, check backend terminal for database errors

---

## 🔍 Debugging Steps

### If CORS Error Still Appears:

1. **Clear browser cache**:
   - `Ctrl+Shift+Delete` → Clear cache
   - Or use incognito/private window

2. **Check backend is actually restarted**:
   - Look for "Application startup complete" in backend terminal
   - Check if port 8000 is listening

3. **Test CORS directly**:
   ```powershell
   # Test from PowerShell
   $headers = @{
       "Origin" = "http://localhost:3000"
   }
   Invoke-WebRequest -Uri "http://localhost:8000/health/cors" -Headers $headers
   ```

### If 500 Error Appears:

1. **Check backend terminal** for error messages
2. **Check database connection** (use check_db_connection.py)
3. **Verify .env file** has correct database URL
4. **Check PostgreSQL** is running

---

## 📊 Expected Behavior

**After restart:**

✅ **CORS Headers Present**:
- `Access-Control-Allow-Origin: http://localhost:3000`
- `Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS, PATCH, HEAD`
- `Access-Control-Allow-Headers: *`

✅ **No CORS Errors** in browser console

✅ **API Calls Work**:
- Companies list loads
- No 500 errors (unless database issue)

---

## 🎯 Quick Fix Checklist

- [ ] Backend restarted (CRITICAL!)
- [ ] Backend is running on port 8000
- [ ] Database connection works (test with check_db_connection.py)
- [ ] CORS headers visible in Network tab
- [ ] No CORS errors in browser console
- [ ] Companies page loads data

---

**RESTART THE BACKEND NOW and the CORS error should be fixed!** 🚀

