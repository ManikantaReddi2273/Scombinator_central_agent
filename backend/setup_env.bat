@echo off
REM Setup script for environment variables (Windows)

echo Generating encryption key...
python generate_encryption_key.py > .env_key.txt
for /f "tokens=2 delims==" %%a in ('findstr ENCRYPTION_KEY .env_key.txt') do set ENCRYPTION_KEY=%%a

REM Create .env file
(
echo # Admin Credentials (will be stored encrypted in DB)
echo ADMIN_EMAIL=reddimanikanta2005@gmail.com
echo ADMIN_PASSWORD=R@ddi2273
echo ADMIN_ROLE=ADMIN
echo.
echo # PostgreSQL Credentials
echo POSTGRES_DB=s_combinator
echo POSTGRES_USER=postgres
echo POSTGRES_PASSWORD=reddi2273
echo.
echo # Database URLs
echo DATABASE_URL=postgresql+asyncpg://postgres:reddi2273@localhost:5432/s_combinator
echo DATABASE_URL_SYNC=postgresql://postgres:reddi2273@localhost:5432/s_combinator
echo LANGRAPH_CHECKPOINT_DB_URL=postgresql+asyncpg://postgres:reddi2273@localhost:5432/s_combinator
echo.
echo # JWT Secret
echo JWT_SECRET_KEY=MfuUwnPbuz5wymlkjQ-EMwypAOgpqxuXt-75kMi4gJU
echo JWT_ALGORITHM=HS256
echo JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
echo.
echo # Encryption Key for Tokens
echo ENCRYPTION_KEY=%ENCRYPTION_KEY%
echo.
echo # Google OAuth (for reference, actual OAuth handled by n8n)
echo GOOGLE_CLIENT_ID=your-google-client-id
echo GOOGLE_CLIENT_SECRET=your-google-client-secret
echo.
echo # OpenAI (for LangGraph)
echo OPENAI_API_KEY=your-openai-api-key
echo.
echo # n8n Webhook URL (for callbacks)
echo N8N_WEBHOOK_URL=http://localhost:5678/webhook
echo.
echo # App Settings
echo APP_NAME=S Combinator Central Agent Platform
echo APP_VERSION=1.0.0
echo DEBUG=True
) > .env

echo ✅ .env file created!
echo ⚠️  Don't forget to:
echo    1. Update OPENAI_API_KEY with your actual key
echo    2. Update GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET if needed
del .env_key.txt

