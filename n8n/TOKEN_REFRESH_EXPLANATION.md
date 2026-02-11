# Token Refresh Mechanism - How It Works

## Overview
The system **automatically refreshes access tokens** when they expire or are about to expire. You don't need to see refresh tokens in n8n output - the refresh happens **automatically in the backend**.

## How Token Refresh Works

### 1. **Backend Token Manager Service** (`backend/services/token_manager.py`)

The `get_valid_token()` method automatically handles refresh:

```python
async def get_valid_token(self, db: AsyncSession, company_id: str) -> str:
    """Get valid access token, refreshing if needed"""
    
    # Check if token is expired or expiring soon (within 5 minutes)
    now = datetime.now(timezone.utc)
    expires_at = company.access_token_expires_at
    
    if not expires_at or (expires_at - now).total_seconds() < 300:
        # Token expired or expiring soon, refresh it
        await self._refresh_token(db, company)
        # Reload company to get new token
        await db.refresh(company)
    
    # Decrypt and return access token
    return self.encryption_service.decrypt(company.encrypted_access_token)
```

### 2. **Refresh Process** (`_refresh_token` method)

When a token needs refresh:

1. **Decrypts refresh token** from database (stored encrypted)
2. **Uses Google OAuth library** to refresh the access token
3. **Encrypts and stores** the new access token
4. **Updates expiration time** in database

```python
async def _refresh_token(self, db: AsyncSession, company: Company) -> None:
    """Refresh access token using refresh token"""
    # Decrypt refresh token
    refresh_token = self.encryption_service.decrypt(company.encrypted_refresh_token)
    
    # Get client_id and client_secret
    client_id, client_secret = self._get_google_credentials()
    
    # Create credentials object
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret
    )
    
    # Refresh the token (calls Google API)
    creds.refresh(Request())
    
    # Encrypt and store new token
    company.encrypted_access_token = self.encryption_service.encrypt(creds.token)
    company.access_token_expires_at = creds.expiry
    
    await db.commit()
```

### 3. **n8n Workflow Flow**

When n8n calls `/api/companies/{company_id}/gmail-token`:

1. **Backend checks** if token is expired or expiring soon (< 5 minutes)
2. **If expired**: Automatically refreshes using stored refresh_token
3. **Returns** valid access_token to n8n
4. **n8n uses** the access_token for Gmail API calls

### 4. **Why You Don't See Refresh Tokens in n8n**

- **Refresh tokens are stored encrypted** in the database (never sent to n8n)
- **Refresh happens automatically** in the backend before returning token
- **n8n only receives** the valid `access_token` (which is what it needs)
- **Security**: Refresh tokens are sensitive and should never leave the backend

## Token Storage

### In Database (Company Model):
- `encrypted_access_token` - Encrypted access token
- `encrypted_refresh_token` - Encrypted refresh token (used for refresh)
- `access_token_expires_at` - When the access token expires

### In n8n Output:
- `access_token` - Valid access token (ready to use)
- `expires_at` - When this token expires
- **NO refresh_token** - This is correct! Refresh tokens stay in backend

## Verification

To verify refresh is working:

1. **Check backend logs** when calling `/api/companies/{company_id}/gmail-token`
2. **Look for** "Refreshing token" messages (if logging is enabled)
3. **Check database** - `access_token_expires_at` should update after refresh
4. **Test with expired token** - Backend should automatically refresh it

## Summary

✅ **Refresh tokens ARE being used** - they're stored encrypted in the database  
✅ **Refresh happens automatically** - backend handles it before returning token  
✅ **n8n doesn't need refresh tokens** - it only needs valid access tokens  
✅ **This is the correct design** - refresh tokens should never leave the backend

The system is working correctly! The refresh happens transparently in the backend.

