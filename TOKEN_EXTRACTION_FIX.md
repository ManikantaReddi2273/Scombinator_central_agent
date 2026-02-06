# Token Extraction Fix - n8n Workflow

## 🔴 Problem

Error in "Extract Tokens" node:
```
"OK"} [line 11]
Failed to get access token. Response: {"body":{"access_token":"...","expires_in":3599,...},"headers":{...},"statusCode":200,"statusMessage":"OK"}
```

## 🔍 Root Cause

The HTTP Request node was configured with `fullResponse: true`, which returns the **full HTTP response object**:
```json
{
  "body": {
    "access_token": "...",
    "refresh_token": "...",
    "expires_in": 3599
  },
  "headers": {...},
  "statusCode": 200,
  "statusMessage": "OK"
}
```

But the code was trying to access `tokenResponse.access_token` directly, when it should be `tokenResponse.body.access_token`.

## ✅ Fixes Applied

### 1. Changed fullResponse to false

**Before:**
```json
"options": {
  "response": {
    "response": {
      "responseFormat": "json",
      "fullResponse": true  // ❌ Returns full response object
    }
  }
}
```

**After:**
```json
"options": {
  "response": {
    "response": {
      "responseFormat": "json",
      "fullResponse": false  // ✅ Returns only JSON body
    }
  }
}
```

**Why:** With `fullResponse: false`, the HTTP Request node returns only the JSON body directly, so `tokenResponse.access_token` works correctly.

### 2. Simplified Extract Tokens Code

The code now directly accesses `tokenResponse.access_token` since the response is just the JSON body, not wrapped in a full response object.

## 🧪 Testing

After importing the updated workflow:

1. **Test OAuth Flow:**
   - Go to frontend: http://localhost:3000
   - Login → Companies → Add Company
   - Complete OAuth flow

2. **Check Node Execution:**
   - "Exchange Code for Tokens" → Should return JSON with access_token
   - "Extract Tokens" → Should successfully extract tokens
   - "Get User Email" → Should use token successfully

## 📝 Expected Response Structure

**With fullResponse: false (current fix):**
```json
{
  "access_token": "ya29.a0AUMWg_...",
  "refresh_token": "1//0gAELEJfVfBfrCgYIARAAGBASNwF-...",
  "expires_in": 3599,
  "scope": "https://www.googleapis.com/auth/...",
  "token_type": "Bearer"
}
```

**With fullResponse: true (old - caused error):**
```json
{
  "body": {
    "access_token": "ya29.a0AUMWg_...",
    "refresh_token": "1//0gAELEJfVfBfrCgYIARAAGBASNwF-...",
    "expires_in": 3599
  },
  "headers": {...},
  "statusCode": 200,
  "statusMessage": "OK"
}
```

## ✅ Summary

- **Fixed:** Changed `fullResponse: true` to `false` in HTTP Request node
- **Result:** Token response is now directly accessible as JSON
- **Impact:** Extract Tokens node can now correctly access `access_token`

The workflow should now work end-to-end! 🎉

