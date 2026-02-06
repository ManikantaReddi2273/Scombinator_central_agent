# Fix 500 Internal Server Error

## 🔍 Issue

Getting `500 Internal Server Error` when accessing `/api/companies/`

**Possible Causes:**
1. Database connection failure
2. Database tables don't exist
3. Admin user doesn't exist
4. Authentication token issue
5. Database query error

---

## 🚀 Quick Fix Steps

### Step 1: Check Backend Terminal

**Look at your backend terminal** (where `uv run python main.py` is running) for error messages.

**Common errors you might see:**
- `Database connection error`
- `relation "admins" does not exist`
- `relation "companies" does not exist`
- `Admin not found`
- `Connection refused`

### Step 2: Test Database Connection

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uv run python check_db_connection.py
```

**Expected output:**
- ✅ `Database connection successful!` → Database is working
- ❌ `Database connection failed` → Need to fix database

### Step 3: Initialize Database

**If database connection fails or tables don't exist:**

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uv run python init_db.py
```

**This will:**
- Create all database tables
- Create admin user
- Set up the database

### Step 4: Test Backend Endpoints

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uv run python test_endpoint.py
```

This will test:
- Health endpoint
- CORS endpoint
- Login endpoint
- Companies endpoint

---

## 🐛 Common Issues & Solutions

### Issue 1: "relation 'admins' does not exist"

**Solution:**
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uv run python init_db.py
```

### Issue 2: "Database connection error"

**Check PostgreSQL:**
```powershell
# Check if PostgreSQL is running
Get-Service -Name postgresql*

# If not running, start it
Start-Service postgresql-x64-15  # Adjust version if different
```

**Check database exists:**
```powershell
psql -U postgres -c "\l" | Select-String "s_combinator"
```

**Create database if missing:**
```powershell
psql -U postgres -c "CREATE DATABASE s_combinator;"
```

### Issue 3: "Admin not found"

**Solution:**
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uv run python init_db.py
```

This creates the admin user:
- Email: `reddimanikanta2005@gmail.com`
- Password: `R@ddi2273`

### Issue 4: Authentication Token Invalid

**Solution:**
1. Logout from frontend
2. Clear browser localStorage
3. Login again
4. Get fresh token

---

## ✅ Verification Steps

### 1. Check Backend is Running
- Open: http://localhost:8000/health
- Should show: `{"status": "healthy"}`

### 2. Check Database Connection
- Open: http://localhost:8000/health/db
- Should show: `{"status": "healthy", "database": "connected"}`

### 3. Test Login
- Go to: http://localhost:3000/login
- Login with: `reddimanikanta2005@gmail.com` / `R@ddi2273`
- Should redirect to dashboard

### 4. Test Companies Endpoint
- After login, go to Companies page
- Should load without 500 error

---

## 🔧 If Still Getting 500 Error

### Check Backend Logs

**Look at backend terminal for:**
1. **Error messages** - What exact error is shown?
2. **Stack traces** - Full error details
3. **Database errors** - Connection issues?

### Common Error Messages:

**"Database connection error"**
→ Fix: Check PostgreSQL is running, database exists

**"relation 'admins' does not exist"**
→ Fix: Run `python init_db.py`

**"Admin not found"**
→ Fix: Run `python init_db.py` to create admin

**"Connection refused"**
→ Fix: Check PostgreSQL service is running

---

## 📊 Diagnostic Commands

### Test Database Connection
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uv run python check_db_connection.py
```

### Test All Endpoints
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uv run python test_endpoint.py
```

### Check PostgreSQL
```powershell
# Check service status
Get-Service -Name postgresql*

# Check if database exists
psql -U postgres -c "\l" | Select-String "s_combinator"

# Connect to database
psql -U postgres -d s_combinator -c "\dt"  # List tables
```

---

## 🎯 Most Likely Solution

**The 500 error is most likely because:**
1. Database tables don't exist
2. Admin user doesn't exist

**Quick fix:**
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uv run python init_db.py
```

**Then restart backend:**
1. Stop backend (Ctrl+C)
2. Restart: `uv run python main.py`

---

## ✅ After Fixing

**Expected behavior:**
- ✅ Health endpoint works
- ✅ Database health check works
- ✅ Login works
- ✅ Companies endpoint returns 200 (or empty list)
- ✅ No 500 errors

**Test it:**
1. Go to: http://localhost:3000
2. Login
3. Navigate to Companies page
4. Should load successfully (even if empty)

---

**Run `python init_db.py` first, then restart backend!** 🚀

