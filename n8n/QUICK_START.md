# n8n Quick Start Guide

## 🚀 Fastest Way to Get Started

### Option 1: Automated Setup (Recommended)

```powershell
cd n8n
.\setup_n8n.ps1
```

This script will:
- ✅ Check Docker installation
- ✅ Generate encryption key
- ✅ Set up password
- ✅ Start n8n automatically

### Option 2: Manual Setup

#### 1. Generate Encryption Key

```powershell
-join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
```

#### 2. Edit `docker-compose.yml`

Replace:
- `N8N_ENCRYPTION_KEY=CHANGE_THIS_TO_32_CHARACTER_KEY` with your generated key
- `N8N_BASIC_AUTH_PASSWORD=admin123` with your password

#### 3. Start n8n

```powershell
docker-compose up -d
```

#### 4. Access n8n

Open: http://localhost:5678

Login:
- Username: `admin`
- Password: (the one you set)

## ✅ Verify It's Working

```powershell
# Check if container is running
docker ps

# Check logs
docker logs s-combinator-n8n

# Test in browser
# Open: http://localhost:5678
```

## 🛑 Stop n8n

```powershell
docker-compose down
```

## 🔄 Restart n8n

```powershell
docker-compose restart
```

## 📝 Common Issues

**Port 5678 in use?**
- Change port in docker-compose.yml: `"5679:5678"`
- Or stop the service using port 5678

**Container won't start?**
- Check logs: `docker logs s-combinator-n8n`
- Ensure Docker Desktop is running
- Check encryption key is 32 characters

**Can't access UI?**
- Ensure container is running: `docker ps`
- Try: `http://127.0.0.1:5678`
- Check Windows Firewall

## 📚 Full Documentation

See `../n8n_DOCKER_SETUP_GUIDE.md` for complete details.

