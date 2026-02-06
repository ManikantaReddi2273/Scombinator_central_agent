# n8n Setup Script for S Combinator Platform
# This script helps you set up n8n with Docker

Write-Host ""
Write-Host "=== n8n Setup Script ===" -ForegroundColor Cyan
Write-Host "This will help you set up n8n for S Combinator Platform" -ForegroundColor Yellow
Write-Host ""

# Check if Docker is installed
Write-Host "Step 1: Checking Docker installation..." -ForegroundColor Green
try {
    $dockerVersion = docker --version
    Write-Host "Docker found: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "Docker is not installed or not running!" -ForegroundColor Red
    Write-Host "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# Check if Docker is running
Write-Host ""
Write-Host "Step 2: Checking if Docker is running..." -ForegroundColor Green
try {
    docker ps | Out-Null
    Write-Host "Docker is running" -ForegroundColor Green
} catch {
    Write-Host "Docker is not running!" -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again." -ForegroundColor Yellow
    exit 1
}

# Generate encryption key
Write-Host ""
Write-Host "Step 3: Generating encryption key..." -ForegroundColor Green
$encryptionKey = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
Write-Host "Generated encryption key: $encryptionKey" -ForegroundColor Green
Write-Host "IMPORTANT: Save this key! You will need it to access encrypted credentials." -ForegroundColor Red

# Update docker-compose.yml with encryption key
Write-Host ""
Write-Host "Step 4: Updating docker-compose.yml..." -ForegroundColor Green
$composeFile = "docker-compose.yml"
if (Test-Path $composeFile) {
    $content = Get-Content $composeFile -Raw
    $content = $content -replace 'N8N_ENCRYPTION_KEY=CHANGE_THIS_TO_32_CHARACTER_KEY', "N8N_ENCRYPTION_KEY=$encryptionKey"
    Set-Content -Path $composeFile -Value $content
    Write-Host "Updated docker-compose.yml with encryption key" -ForegroundColor Green
} else {
    Write-Host "docker-compose.yml not found!" -ForegroundColor Red
    exit 1
}

# Ask for password
Write-Host ""
Write-Host "Step 5: Setting up authentication..." -ForegroundColor Green
$password = Read-Host "Enter a password for n8n admin (or press Enter for default 'admin123')"
if ([string]::IsNullOrWhiteSpace($password)) {
    $password = "admin123"
    Write-Host "Using default password: admin123" -ForegroundColor Yellow
    Write-Host "WARNING: Change this password after first login!" -ForegroundColor Red
} else {
    Write-Host "Password set" -ForegroundColor Green
}

# Update password in docker-compose.yml
$content = Get-Content $composeFile -Raw
$content = $content -replace 'N8N_BASIC_AUTH_PASSWORD=admin123', "N8N_BASIC_AUTH_PASSWORD=$password"
Set-Content -Path $composeFile -Value $content

# Create data directory if it doesn't exist
Write-Host ""
Write-Host "Step 6: Creating data directory..." -ForegroundColor Green
if (-not (Test-Path "data")) {
    New-Item -ItemType Directory -Path "data" | Out-Null
    Write-Host "Created data directory" -ForegroundColor Green
} else {
    Write-Host "Data directory already exists" -ForegroundColor Green
}

# Check if port 5678 is available
Write-Host ""
Write-Host "Step 7: Checking port 5678..." -ForegroundColor Green
$portCheck = netstat -an | Select-String ":5678"
if ($portCheck) {
    Write-Host "Port 5678 is already in use!" -ForegroundColor Yellow
    Write-Host "You may need to stop the existing service or change the port." -ForegroundColor Yellow
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y") {
        exit 1
    }
} else {
    Write-Host "Port 5678 is available" -ForegroundColor Green
}

# Start n8n
Write-Host ""
Write-Host "Step 8: Starting n8n..." -ForegroundColor Green
Write-Host "This may take a few minutes on first run (downloading image)..." -ForegroundColor Yellow

try {
    docker-compose up -d
    Write-Host "n8n is starting..." -ForegroundColor Green
    Write-Host ""
    Write-Host "Waiting for n8n to be ready..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    # Check if container is running
    $container = docker ps --filter "name=s-combinator-n8n" --format "{{.Names}}"
    if ($container -eq "s-combinator-n8n") {
        Write-Host "n8n container is running!" -ForegroundColor Green
    } else {
        Write-Host "Container may still be starting. Check with: docker ps" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Error starting n8n!" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}

# Display summary
Write-Host ""
Write-Host "=== Setup Complete! ===" -ForegroundColor Green
Write-Host ""
Write-Host "Access n8n at: http://localhost:5678" -ForegroundColor Cyan
Write-Host "Username: admin" -ForegroundColor Cyan
Write-Host "Password: $password" -ForegroundColor Cyan
Write-Host ""
Write-Host "Encryption Key (SAVE THIS!): $encryptionKey" -ForegroundColor Red
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Yellow
Write-Host "  Start:   docker-compose up -d" -ForegroundColor White
Write-Host "  Stop:    docker-compose down" -ForegroundColor White
Write-Host "  Logs:    docker logs -f s-combinator-n8n" -ForegroundColor White
Write-Host "  Restart: docker-compose restart" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Open http://localhost:5678 in your browser" -ForegroundColor White
Write-Host "  2. Login with the credentials above" -ForegroundColor White
Write-Host "  3. Configure Google OAuth credentials" -ForegroundColor White
Write-Host "  4. Create Company Onboarding workflow" -ForegroundColor White
