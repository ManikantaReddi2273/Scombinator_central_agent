# Fix: ECONNREFUSED - n8n Can't Connect to Backend

## 🔍 The Problem

Error: `ECONNREFUSED ::1:8000`

n8n (running in Docker) is trying to connect to `localhost:8000`, but Docker containers can't access `localhost` on the host machine.

---

## ✅ Solution: Use `host.docker.internal`

On Windows/Mac, Docker containers can access the host machine using `host.docker.internal` instead of `localhost`.

---

## 📋 Fix Steps

### Step 1: Update the Workflow in n8n

**Option A: Re-import the Updated Workflow (Easiest)**

1. Open n8n: `http://localhost:5678`
2. Go to **Workflows**
3. Find **"Company OAuth Connection"**
4. **Delete it** (or deactivate it first)
5. Go to **Import from File**
6. Select: `Company OAuth Connection.json` (the updated file)
7. **Import it**
8. **Activate it** (toggle ON)
9. **Save** (Ctrl+S)

**Option B: Manually Edit in n8n UI**

1. Open **"Company OAuth Connection"** workflow in n8n
2. Click on **"Connect OAuth to Company"** node
3. In the **URL** field, change:
   - From: `http://localhost:8000/api/companies/{{ $json.company_id }}/connect-oauth`
   - To: `http://host.docker.internal:8000/api/companies/{{ $json.company_id }}/connect-oauth`
4. **Save the node**
5. **Save the workflow** (Ctrl+S)

---

### Step 2: Make Sure Backend is Running

1. **Check if backend is running**:
   ```powershell
   # In PowerShell
   Test-NetConnection -ComputerName localhost -Port 8000
   ```
   
   Or open: `http://localhost:8000/health` in browser
   
   Should return: `{"status":"ok"}`

2. **If backend is NOT running**, start it:
   ```powershell
   cd backend
   uv run python main.py
   ```
   
   Or if using different method:
   ```powershell
   cd backend
   python main.py
   ```

3. **Keep the backend running** in a terminal window

---

### Step 3: Test the Connection

1. **In n8n**, go to **"Company OAuth Connection"** workflow
2. Click **"Execute workflow"** button (bottom right)
3. Or try connecting OAuth from frontend again
4. **Check the execution** - should now succeed!

---

## 🔧 Alternative: Use Host Network Mode (Advanced)

If `host.docker.internal` doesn't work, you can modify `n8n/docker-compose.yml`:

```yaml
services:
  n8n:
    # ... existing config ...
    network_mode: "host"  # Add this line
```

Then restart n8n:
```powershell
cd n8n
docker-compose down
docker-compose up -d
```

**Note**: This makes n8n use the host's network directly, so `localhost:8000` will work.

---

## ✅ Verification

After fixing, when you connect OAuth:

1. ✅ **n8n workflow executes successfully**
2. ✅ **"Connect OAuth to Company" node shows green** (success)
3. ✅ **Backend receives the request** (check backend terminal logs)
4. ✅ **Company OAuth is connected** (check frontend)

---

## 🐛 Still Not Working?

**Check 1: Backend is actually running**
- Open: `http://localhost:8000/health`
- Should return JSON, not connection error

**Check 2: Backend is listening on correct port**
- Check backend terminal for: `Uvicorn running on http://0.0.0.0:8000`
- If it says `127.0.0.1:8000`, change it to `0.0.0.0:8000` in `backend/main.py`

**Check 3: Firewall blocking**
- Windows Firewall might block Docker → Host connections
- Try temporarily disabling firewall to test

**Check 4: Docker Desktop settings**
- Make sure Docker Desktop is running
- Check Docker Desktop → Settings → Resources → Network
- Ensure "Use WSL 2 based engine" is enabled (if using WSL)

---

## 📝 Summary

**The Fix:**
- Changed `localhost:8000` → `host.docker.internal:8000` in workflow
- This allows Docker container to access host machine's services

**Files Updated:**
- ✅ `Company OAuth Connection.json` - Updated URL
- ✅ `Company Onboarding.json` - Updated URL (for consistency)

**Next Steps:**
1. Re-import workflow in n8n OR manually update the URL
2. Make sure backend is running
3. Test OAuth connection again

