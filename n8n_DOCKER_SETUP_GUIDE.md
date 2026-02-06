# n8n Self-Hosted Setup Guide (Docker) - Windows

Complete step-by-step guide to set up n8n using Docker on Windows.

---

## 📋 Prerequisites

Before starting, ensure you have:

1. **Docker Desktop for Windows** installed
   - Download from: https://www.docker.com/products/docker-desktop
   - Install and start Docker Desktop
   - Verify installation: Open PowerShell and run:
     ```powershell
     docker --version
     docker-compose --version
     ```

2. **At least 2GB free disk space**
3. **Port 5678 available** (or choose a different port)

---

## 🚀 STEP 1: Create n8n Directory Structure

Create a dedicated folder for n8n:

```powershell
# Navigate to your project directory
cd "C:\Users\ManishReddy\OneDrive\Desktop\S Combinator _Central Agent Platform"

# Create n8n directory
mkdir n8n
cd n8n

# Create subdirectories for data persistence
mkdir data
mkdir .n8n
```

**Why these folders?**
- `data/` - Stores n8n workflow data, credentials, and settings
- `.n8n/` - Stores n8n configuration files

---

## 🐳 STEP 2: Create Docker Compose File (Recommended)

Using Docker Compose makes it easier to manage and configure n8n.

Create a file named `docker-compose.yml` in the `n8n` folder:

```yaml
version: '3.8'

services:
  n8n:
    image: n8nio/n8n:latest
    container_name: s-combinator-n8n
    restart: unless-stopped
    ports:
      - "5678:5678"
    environment:
      # Basic Configuration
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=admin123
      
      # Database (using SQLite by default, can be changed to PostgreSQL)
      - DB_TYPE=sqlite
      - DB_SQLITE_DATABASE=/home/node/.n8n/database.sqlite
      
      # Encryption key (IMPORTANT: Change this!)
      - N8N_ENCRYPTION_KEY=your-32-character-encryption-key-here
      
      # Timezone
      - GENERIC_TIMEZONE=UTC
      
      # Webhook URL (for production, use your domain)
      - WEBHOOK_URL=http://localhost:5678/
      
      # Execution settings
      - EXECUTIONS_PROCESS=main
      - EXECUTIONS_DATA_SAVE_ON_ERROR=all
      - EXECUTIONS_DATA_SAVE_ON_SUCCESS=all
      - EXECUTIONS_DATA_MAX_AGE=168  # 7 days
      
    volumes:
      # Persist n8n data
      - ./data:/home/node/.n8n
      # Mount workflows folder (optional)
      - ./workflows:/home/node/.n8n/workflows
      
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:5678/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

**Save this as:** `n8n/docker-compose.yml`

---

## 🔐 STEP 3: Generate Encryption Key

n8n requires a 32-character encryption key. Generate one:

**Option A: Using PowerShell**
```powershell
# Generate random 32-character key
-join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
```

**Option B: Using Online Tool**
- Visit: https://www.random.org/strings/
- Generate: 32 characters, alphanumeric
- Copy the key

**Option C: Using Python (if installed)**
```powershell
python -c "import secrets; print(secrets.token_urlsafe(32)[:32])"
```

**Example key:** `aB3dE5fG7hI9jK1lM3nO5pQ7rS9tU1`

**⚠️ IMPORTANT:** 
- Save this key securely
- Update `N8N_ENCRYPTION_KEY` in `docker-compose.yml`
- Don't lose this key (you'll need it to access encrypted credentials)

---

## 🚀 STEP 4: Start n8n with Docker Compose

**Method 1: Using Docker Compose (Recommended)**

```powershell
# Navigate to n8n directory
cd "C:\Users\ManishReddy\OneDrive\Desktop\S Combinator _Central Agent Platform\n8n"

# Start n8n
docker-compose up -d
```

**What this does:**
- `-d` flag runs in detached mode (background)
- Downloads n8n image if not present
- Creates and starts container
- Maps port 5678

**Check if it's running:**
```powershell
docker ps
```

You should see:
```
CONTAINER ID   IMAGE          STATUS         PORTS                    NAMES
abc123def456   n8nio/n8n     Up 2 minutes   0.0.0.0:5678->5678/tcp   s-combinator-n8n
```

---

## 🌐 STEP 5: Access n8n Web Interface

1. **Open browser** and go to:
   ```
   http://localhost:5678
   ```

2. **Login with:**
   - Username: `admin`
   - Password: `admin123`
   (These are set in docker-compose.yml)

3. **First-time setup:**
   - You'll see n8n welcome screen
   - Click "Get Started"
   - Set up your user account (optional, can skip)

---

## 📝 STEP 6: Configure n8n for S-Combinator

### 6.1: Set Up Google OAuth Credentials

1. **In n8n UI**, go to:
   ```
   Settings → Credentials → Add Credential
   ```

2. **Search for:** "Google OAuth2 API"

3. **Fill in:**
   ```
   Credential Name: S-Combinator Google App
   
   Client ID: [Your Google Cloud Client ID]
   Client Secret: [Your Google Cloud Client Secret]
   
   Scopes:
   - https://www.googleapis.com/auth/gmail
   - https://www.googleapis.com/auth/drive
   - https://www.googleapis.com/auth/drive.file
   ```

4. **Click "Save"**

**Note:** You'll need to create Google Cloud OAuth credentials first (see Google Cloud Setup section below).

---

## 🔧 STEP 7: Verify n8n is Working

### Test n8n Health:

```powershell
# Check container logs
docker logs s-combinator-n8n

# Check if port is listening
netstat -an | findstr 5678
```

**Expected output:**
```
Listening on port 5678
```

### Test in Browser:
- Visit: http://localhost:5678
- Should see n8n login page

---

## 🛠️ STEP 8: Useful Docker Commands

### Start n8n:
```powershell
docker-compose up -d
```

### Stop n8n:
```powershell
docker-compose down
```

### View logs:
```powershell
docker logs s-combinator-n8n
# Or follow logs in real-time:
docker logs -f s-combinator-n8n
```

### Restart n8n:
```powershell
docker-compose restart
```

### Update n8n to latest version:
```powershell
docker-compose pull
docker-compose up -d
```

### Remove everything (⚠️ deletes data):
```powershell
docker-compose down -v
```

---

## 📁 STEP 9: Directory Structure After Setup

Your `n8n` folder should look like:

```
n8n/
├── docker-compose.yml
├── data/
│   ├── database.sqlite
│   ├── credentials/
│   └── workflows/
└── workflows/ (optional)
```

**Data persistence:**
- All workflows, credentials, and settings are stored in `data/` folder
- If you delete the container, data remains safe
- Backup the `data/` folder regularly

---

## 🔒 STEP 10: Security Recommendations

### 1. Change Default Password

Edit `docker-compose.yml`:
```yaml
- N8N_BASIC_AUTH_PASSWORD=your-strong-password-here
```

Then restart:
```powershell
docker-compose down
docker-compose up -d
```

### 2. Use Environment File (Better Security)

Create `.env` file in `n8n/` folder:
```env
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=your-strong-password
N8N_ENCRYPTION_KEY=your-32-character-key
```

Update `docker-compose.yml`:
```yaml
env_file:
  - .env
```

### 3. For Production:

- Use HTTPS (reverse proxy with nginx/traefik)
- Use PostgreSQL instead of SQLite
- Set up proper firewall rules
- Use strong passwords
- Enable 2FA in n8n

---

## 🗄️ STEP 11: Optional - Use PostgreSQL (For Production)

If you want to use PostgreSQL instead of SQLite:

### Update `docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: n8n-postgres
    restart: unless-stopped
    environment:
      - POSTGRES_DB=n8n
      - POSTGRES_USER=n8n
      - POSTGRES_PASSWORD=n8n_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  n8n:
    image: n8nio/n8n:latest
    container_name: s-combinator-n8n
    restart: unless-stopped
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=admin123
      
      # PostgreSQL Configuration
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_DATABASE=n8n
      - DB_POSTGRESDB_USER=n8n
      - DB_POSTGRESDB_PASSWORD=n8n_password
      
      - N8N_ENCRYPTION_KEY=your-32-character-key
    volumes:
      - ./data:/home/node/.n8n
    depends_on:
      - postgres

volumes:
  postgres_data:
```

---

## 🧪 STEP 12: Test n8n Setup

### Create a Simple Test Workflow:

1. **In n8n UI**, click "Add workflow"
2. **Add nodes:**
   - Trigger: "Manual Trigger"
   - Action: "HTTP Request"
3. **Configure HTTP Request:**
   - Method: GET
   - URL: https://api.github.com/users/n8n-io
4. **Click "Execute Workflow"**
5. **Check output** - should see GitHub user data

If this works, n8n is set up correctly!

---

## 🐛 Troubleshooting

### Issue 1: Port 5678 already in use

**Solution:**
```powershell
# Find what's using port 5678
netstat -ano | findstr :5678

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F

# Or change port in docker-compose.yml:
ports:
  - "5679:5678"  # Use 5679 instead
```

### Issue 2: Container won't start

**Check logs:**
```powershell
docker logs s-combinator-n8n
```

**Common issues:**
- Wrong encryption key format (must be 32 characters)
- Port conflict
- Insufficient disk space

### Issue 3: Can't access n8n UI

**Check:**
1. Is Docker Desktop running?
2. Is container running? (`docker ps`)
3. Try: `http://127.0.0.1:5678` instead of `localhost`
4. Check Windows Firewall

### Issue 4: Data not persisting

**Solution:**
- Ensure volumes are properly mounted
- Check `data/` folder permissions
- Verify paths in docker-compose.yml

---

## 📊 STEP 13: Monitor n8n

### View Resource Usage:
```powershell
docker stats s-combinator-n8n
```

### Check Disk Usage:
```powershell
docker system df
```

### View All Containers:
```powershell
docker ps -a
```

---

## 🔄 STEP 14: Backup n8n Data

### Backup Command:
```powershell
# Stop n8n
docker-compose down

# Copy data folder
Copy-Item -Path ".\data" -Destination ".\backup\data_$(Get-Date -Format 'yyyyMMdd_HHmmss')" -Recurse

# Start n8n
docker-compose up -d
```

### Restore Backup:
```powershell
# Stop n8n
docker-compose down

# Restore data
Copy-Item -Path ".\backup\data_20240204_120000\*" -Destination ".\data\" -Recurse

# Start n8n
docker-compose up -d
```

---

## ✅ Verification Checklist

After setup, verify:

- [ ] Docker Desktop is running
- [ ] Container is running (`docker ps`)
- [ ] Can access http://localhost:5678
- [ ] Can login with admin credentials
- [ ] Can create a test workflow
- [ ] Data folder exists and has files
- [ ] Logs show no errors

---

## 🎯 Next Steps

After n8n is set up:

1. **Configure Google OAuth credentials** in n8n
2. **Create the "Company Onboarding" workflow** (see workflow guide)
3. **Test the OAuth flow** with a test Google account
4. **Set up email monitoring workflows**

---

## 📚 Additional Resources

- n8n Documentation: https://docs.n8n.io/
- n8n Docker Hub: https://hub.docker.com/r/n8nio/n8n
- n8n Community: https://community.n8n.io/

---

## 💡 Quick Reference

**Start n8n:**
```powershell
cd n8n
docker-compose up -d
```

**Stop n8n:**
```powershell
docker-compose down
```

**View logs:**
```powershell
docker logs -f s-combinator-n8n
```

**Access UI:**
```
http://localhost:5678
```

**Default Login:**
- Username: `admin`
- Password: `admin123` (change this!)

---

## 🎉 Success!

If you can access n8n at http://localhost:5678 and login, you're all set!

Next: Configure Google OAuth credentials and create workflows.

