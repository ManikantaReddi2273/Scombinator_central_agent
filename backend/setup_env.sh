#!/bin/bash
# Setup script for environment variables

# Generate encryption key
echo "Generating encryption key..."
python generate_encryption_key.py > .env_key.txt
ENCRYPTION_KEY=$(cat .env_key.txt | grep ENCRYPTION_KEY | cut -d'=' -f2)

# Create .env file
cat > .env << EOF
# Admin Credentials (will be stored encrypted in DB)
ADMIN_EMAIL=reddimanikanta2005@gmail.com
ADMIN_PASSWORD=R@ddi2273
ADMIN_ROLE=ADMIN

# PostgreSQL Credentials
POSTGRES_DB=s_combinator
POSTGRES_USER=postgres
POSTGRES_PASSWORD=reddi2273

# Database URLs
DATABASE_URL=postgresql+asyncpg://postgres:reddi2273@localhost:5432/s_combinator
DATABASE_URL_SYNC=postgresql://postgres:reddi2273@localhost:5432/s_combinator
LANGRAPH_CHECKPOINT_DB_URL=postgresql+asyncpg://postgres:reddi2273@localhost:5432/s_combinator

# JWT Secret
JWT_SECRET_KEY=MfuUwnPbuz5wymlkjQ-EMwypAOgpqxuXt-75kMi4gJU
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Encryption Key for Tokens
ENCRYPTION_KEY=${ENCRYPTION_KEY}

# Google OAuth (for reference, actual OAuth handled by n8n)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# OpenAI (for LangGraph)
OPENAI_API_KEY=your-openai-api-key

# n8n Webhook URL (for callbacks)
N8N_WEBHOOK_URL=http://localhost:5678/webhook

# App Settings
APP_NAME=S Combinator Central Agent Platform
APP_VERSION=1.0.0
DEBUG=True
EOF

echo "✅ .env file created!"
echo "⚠️  Don't forget to:"
echo "   1. Update OPENAI_API_KEY with your actual key"
echo "   2. Update GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET if needed"
rm .env_key.txt

