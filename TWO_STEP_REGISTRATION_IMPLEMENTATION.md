# Two-Step Company Registration - Implementation Complete

## Overview

Successfully implemented two-step company registration that aligns with the architecture principle:
- **n8n**: Handles "When? In what order? What to call next?" (orchestration)
- **Code**: Handles "What does this mean? What should we do? What should we say?" (business logic)

---

## Changes Implemented

### Backend Changes

#### 1. Company Model (`backend/models/company.py`)
- Made `encrypted_access_token` and `encrypted_refresh_token` nullable
- Companies can now exist without OAuth tokens initially

#### 2. Schemas (`backend/schemas/company.py`)
- Added `OAuthConnectRequest` schema for Step 2
- Updated `CompanyResponse` with `has_oauth_connected: bool` field
- Kept `CompanyCreate` schema (name + email only)
- Kept `CompanyRegisterRequest` (backward compatibility)

#### 3. New Endpoints (`backend/routers/companies.py`)
- **Step 1**: `POST /api/companies/` - Create company without OAuth (admin only)
- **Step 2**: `POST /api/companies/{company_id}/connect-oauth` - Connect OAuth to existing company (called by n8n)
- Updated all `CompanyResponse` instances to include `has_oauth_connected`

#### 4. Tenant Service (`backend/services/tenant.py`)
- Added `create_company_without_tokens()` - Step 1 method
- Added `connect_oauth_to_company()` - Step 2 method
- Kept `create_company()` for backward compatibility

#### 5. Database Migration (`backend/migrate_token_fields_nullable.py`)
- Created migration script to make token fields nullable
- Safe to run on existing databases

---

### Frontend Changes

#### 6. API Client (`frontend/src/lib/api.ts`)
- Added `companiesAPI.create()` for Step 1
- Added `companiesAPI.connectOAuth()` for Step 2

#### 7. AddCompanyModal (`frontend/src/components/AddCompanyModal.tsx`)
- **Step 1 Implementation**: Simple form with Name + Email fields
- Removed OAuth redirect logic from initial submit
- Calls `POST /api/companies/` directly
- Shows success message and closes modal
- Added error handling

#### 8. Companies Page (`frontend/src/pages/Companies.tsx`)
- Displays OAuth connection status for each company
- Shows "Connect Gmail & Drive" button for companies without OAuth
- Button triggers OAuth flow with `company_id` in state parameter
- Updated empty state message

---

### n8n Workflow

#### 9. New Simplified Workflow (`Company OAuth Connection.json`)
- **Purpose**: Connect OAuth to existing company (Step 2 only)
- **Flow**:
  1. Webhook receives OAuth callback (with `company_id` in state)
  2. Extract OAuth code and company_id
  3. Get credentials (client_id, client_secret)
  4. Exchange code for tokens (orchestration)
  5. Extract tokens
  6. Call backend: `POST /api/companies/{company_id}/connect-oauth`
  7. Redirect to frontend success page
- **n8n Responsibility**: Orchestration only (when, in what order, what to call)
- **No Business Logic**: No email extraction, no data preparation - just orchestration

---

## Architecture Alignment

### Step 1: Register Company
```
Frontend → Backend API → Company Created
```
- **n8n**: Not involved
- **Backend**: Business logic (validation, duplicate check, creation)
- ✅ Aligned: Business logic in code

### Step 2: Connect OAuth
```
Frontend → n8n OAuth → Google → n8n Callback → Backend (connect tokens)
```
- **n8n**: Orchestration (when, in what order, what to call)
- **Backend**: Business logic (validate tokens, encrypt, store)
- ✅ Aligned: Clear separation of concerns

---

## Migration Steps

### 1. Run Database Migration
```bash
cd backend
python migrate_token_fields_nullable.py
```

### 2. Import n8n Workflow
- Go to n8n: http://localhost:5678
- Import `Company OAuth Connection.json`
- Activate the workflow

### 3. Update Google Cloud Console
- Add redirect URI: `http://localhost:5678/webhook/oauth-connect`
- Keep existing redirect URIs for backward compatibility

### 4. Test Step 1
- Go to frontend: http://localhost:3000
- Login → Companies → Add Company
- Enter name + email
- Company should be created immediately

### 5. Test Step 2
- Click "Connect Gmail & Drive" on a company without OAuth
- Complete OAuth flow
- Company should be updated with tokens

---

## Benefits Achieved

1. ✅ **Clear Separation**: n8n = orchestration, Code = business logic
2. ✅ **Simpler**: Fewer nodes, fewer failure points
3. ✅ **Flexible**: Register companies anytime, connect OAuth when ready
4. ✅ **Maintainable**: Business rules in code, not workflows
5. ✅ **Testable**: Each step can be tested independently

---

## Backward Compatibility

- Existing `/api/companies/register` endpoint still works
- Existing companies with tokens continue to function
- Both registration approaches can coexist
- No breaking changes to existing workflows

---

## Next Steps

1. Run database migration
2. Import new n8n workflow
3. Test Step 1 (direct registration)
4. Test Step 2 (OAuth connection)
5. Update Google Cloud Console with new redirect URI

---

## Files Modified

### Backend
- `backend/models/company.py`
- `backend/schemas/company.py`
- `backend/routers/companies.py`
- `backend/services/tenant.py`
- `backend/migrate_token_fields_nullable.py` (new)

### Frontend
- `frontend/src/lib/api.ts`
- `frontend/src/components/AddCompanyModal.tsx`
- `frontend/src/pages/Companies.tsx`

### n8n
- `Company OAuth Connection.json` (new)

---

## Testing Checklist

- [ ] Step 1: Create company with name + email
- [ ] Step 1: Verify duplicate email prevention
- [ ] Step 1: Verify admin authentication required
- [ ] Step 2: Connect OAuth to existing company
- [ ] Step 2: Verify tokens encrypted and stored
- [ ] Step 2: Verify company updated correctly
- [ ] Step 2: Verify error handling for invalid company_id
- [ ] Backward compatibility: Existing register endpoint still works

