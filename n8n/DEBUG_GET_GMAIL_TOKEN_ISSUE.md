# Debugging "Get Gmail Token from Database" Node - No Output Issue

## Current Status

✅ **Working:**
- "Prepare Token Request" node is working correctly
- Outputs 2 items with `token_url` correctly
- Logs show: `URL: http://host.docker.internal:8000/api/companies/{company_id}/gmail-token`

❌ **Not Working:**
- "Get Gmail Token from Database" node shows "No output data"
- HTTP request might be failing silently

## Possible Causes

### 1. Backend Not Accessible from n8n Docker Container

**Issue**: n8n runs in Docker, and `host.docker.internal` might not resolve correctly.

**Solution**: Test the URL from within the n8n container:
```bash
# In n8n container or from host
curl http://host.docker.internal:8000/api/companies/{company_id}/gmail-token
```

**Alternative**: If `host.docker.internal` doesn't work, try:
- `http://172.17.0.1:8000` (Docker bridge IP)
- `http://localhost:8000` (if n8n and backend are on same host)
- Use the actual host IP address

### 2. Backend Not Running

**Check**: Is the backend running on port 8000?
```bash
# Check if backend is running
curl http://localhost:8000/health
```

### 3. CORS or Network Issue

**Check**: The backend might be blocking requests from n8n.

**Solution**: Check backend logs for any errors when n8n tries to connect.

### 4. URL Expression Issue

**Current**: `={{ $json.token_url }}`

**Test**: Try hardcoding the URL first to see if the node works:
```
http://host.docker.internal:8000/api/companies/5b10f95c-516b-4f10-90b4-0e574310c998/gmail-token
```

### 5. HTTP Request Node Configuration

The node might be configured incorrectly. Check:
- Method: GET ✅
- URL: `={{ $json.token_url }}` ✅
- Authentication: None ✅
- Response Format: JSON ✅

## Debugging Steps

### Step 1: Test Backend Endpoint Manually

```bash
# Replace {company_id} with actual company ID from logs
curl -X GET "http://localhost:8000/api/companies/5b10f95c-516b-4f10-90b4-0e574310c998/gmail-token"
```

**Expected Response:**
```json
{
  "company_id": "5b10f95c-516b-4f10-90b4-0e574310c998",
  "company_email": "rmanikanta932@gmail.com",
  "access_token": "ya29.a0AfH6SMC...",
  "expires_at": "2024-02-05T10:30:00Z"
}
```

### Step 2: Test from n8n Container

If n8n is running in Docker, test network connectivity:

```bash
# Get into n8n container
docker exec -it s-combinator-n8n sh

# Test backend connectivity
curl http://host.docker.internal:8000/health
curl http://host.docker.internal:8000/api/companies/5b10f95c-516b-4f10-90b4-0e574310c998/gmail-token
```

### Step 3: Check n8n Execution Logs

1. In n8n UI, click on "Get Gmail Token from Database" node
2. Check the "Execution" tab for any errors
3. Check browser console (F12) for HTTP errors

### Step 4: Add Debug Node

Add a Code node after "Prepare Token Request" to log the token_url:

```javascript
console.log('Token URL to call:', $json.token_url);
return $json;
```

### Step 5: Test with Hardcoded URL

Temporarily change the URL in "Get Gmail Token from Database" to a hardcoded value to test if the node works:

```
http://host.docker.internal:8000/api/companies/5b10f95c-516b-4f10-90b4-0e574310c998/gmail-token
```

## Common Solutions

### Solution 1: Fix Docker Network

If `host.docker.internal` doesn't work, update the URL in "Prepare Token Request":

```javascript
// Try different host options
const url = `http://172.17.0.1:8000/api/companies/${companyId}/gmail-token`;
// OR
const url = `http://localhost:8000/api/companies/${companyId}/gmail-token`;
// OR use environment variable
const backendHost = process.env.BACKEND_HOST || 'host.docker.internal';
const url = `http://${backendHost}:8000/api/companies/${companyId}/gmail-token`;
```

### Solution 2: Check Backend CORS Settings

Ensure backend allows requests from n8n. Check `backend/main.py` CORS settings.

### Solution 3: Check Backend Logs

Check backend logs when n8n tries to call the endpoint. Look for:
- 404 errors (company not found)
- 500 errors (server error)
- Connection refused errors

### Solution 4: Verify Company Has Valid Tokens

The endpoint might fail if the company doesn't have valid OAuth tokens. Check:
- Does the company have `encrypted_access_token` in database?
- Is the token expired and refresh failing?

## Next Steps

1. **Test backend endpoint manually** - Verify it works
2. **Test from n8n container** - Verify network connectivity
3. **Check n8n execution logs** - Look for HTTP errors
4. **Try hardcoded URL** - Isolate if it's a URL expression issue
5. **Check backend logs** - See if requests are reaching the backend

## Expected Flow After Fix

Once "Get Gmail Token from Database" works:

1. ✅ "Prepare Token Request" → outputs `token_url`
2. ✅ "Get Gmail Token from Database" → calls backend, gets `{access_token, company_id, company_email, expires_at}`
3. ✅ "Merge Token Data" → combines token + company metadata
4. ✅ "Check Gmail Inbox via API" → uses access_token to check Gmail
5. ✅ Rest of workflow continues...

