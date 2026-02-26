# n8n Setup for S Combinator Platform

This directory contains the Docker setup for n8n workflow automation.

## Quick Start

### 1. Generate Encryption Key

```powershell
# Run this in PowerShell to generate a 32-character encryption key
-join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
```

Copy the generated key.

### 2. Update docker-compose.yml

Open `docker-compose.yml` and replace:
```yaml
- N8N_ENCRYPTION_KEY=CHANGE_THIS_TO_32_CHARACTER_KEY
```

With your generated key:
```yaml
- N8N_ENCRYPTION_KEY=your-generated-key-here
```

Also change the default password:
```yaml
- N8N_BASIC_AUTH_PASSWORD=your-strong-password
```

### 3. Start n8n

```powershell
cd n8n
docker-compose up -d
```

### 4. Access n8n

Open browser: http://localhost:5678

Login:
- Username: `admin`
- Password: (the one you set in docker-compose.yml)

## Commands

**Start:**
```powershell
docker-compose up -d
```

**Stop:**
```powershell
docker-compose down
```

**View logs:**
```powershell
docker logs -f s-combinator-n8n
```

**Restart:**
```powershell
docker-compose restart
```

## Directory Structure

```
n8n/
├── docker-compose.yml    # Docker configuration
├── data/                 # n8n data (workflows, credentials)
└── README.md            # This file
```

## Update CRM After Send (API key)

The **Update CRM After Send** workflow node needs an API key to call the backend. Env access is allowed so the node can read `$env.N8N_SERVICE_API_KEY`.

**What you need to do:**

1. **Backend** – In `backend/.env`, add (use a long random string, e.g. 32+ chars):
   ```env
   N8N_SERVICE_API_KEY=your-secret-key-here
   ```
   Restart the backend after changing `.env`.

2. **n8n** – In the **n8n** folder, create a file named `.env` (copy from `.env.example` if needed) and set the **same** value:
   ```env
   N8N_SERVICE_API_KEY=your-secret-key-here
   ```
   Use the exact same value as in `backend/.env`.

3. **Restart n8n** so it picks up the new env:
   ```powershell
   cd n8n
   docker-compose down
   docker-compose up -d
   ```

If `N8N_SERVICE_API_KEY` is not set in n8n’s env, the container will start with a placeholder and the **Update CRM After Send** node will get 403 until you set it and restart.

## Important Notes

1. **Encryption Key**: Never lose this key! You need it to access encrypted credentials.
2. **Password**: Change the default password immediately.
3. **Backup**: Regularly backup the `data/` folder.
4. **Port**: Make sure port 5678 is available.

## Next Steps

1. Configure Google OAuth credentials in n8n
2. Create "Company Onboarding" workflow
3. Test OAuth flow

See `../n8n_DOCKER_SETUP_GUIDE.md` for detailed instructions.

