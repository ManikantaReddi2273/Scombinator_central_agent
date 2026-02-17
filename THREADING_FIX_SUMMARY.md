# Email Threading Fix - Summary

## Problem Identified

**Issue:** Emails were not threading correctly on the recipient's side (customer's inbox), even though they appeared correctly threaded on the sender's side (company's inbox).

**Root Cause:** The raw email message sent via Gmail API was missing critical RFC 2822 threading headers:
- `In-Reply-To` header (references the original email's Message-ID)
- `References` header (chain of Message-IDs in the thread)
- `Message-ID` header (unique identifier for this email)

While Gmail API's `threadId` parameter threads emails correctly on the **sender's side**, email clients on the **recipient's side** rely on these RFC 2822 headers to properly thread conversations.

---

## Solution Implemented

### 1. Backend Changes

**File: `backend/schemas/email.py`**
- Added `gmail_message_id` field to `EmailResponse` schema
- This allows n8n workflow to access the original email's Gmail message ID

**File: `backend/routers/emails.py`**
- Updated `get_email()` endpoint to return `gmail_message_id` in response
- This provides the necessary data for fetching original message headers

### 2. n8n Workflow Changes

**File: `n8n/Send Approved Drafts.json`**

#### New Node: "Prepare Message Fetch"
- Checks if email is a reply (has `thread_id` and `gmail_message_id`)
- Prepares data for fetching original message from Gmail API
- Returns early if not a reply (new conversation)

#### New Node: "Get Original Message (for threading)"
- Fetches the original email from Gmail API using `gmail_message_id`
- Retrieves full message with headers (format=full)
- Extracts Message-ID header from original email
- Uses `continueOnFail: true` to gracefully handle errors

#### Updated Node: "Prepare Email Message"
- **Fetches original message data** from "Get Original Message" node
- **Extracts Message-ID** from original email's headers
- **Generates new Message-ID** for the reply (format: `<timestamp.random@domain>`)
- **Builds References header** (includes all Message-IDs in thread chain)
- **Adds threading headers** to raw email message:
  - `Message-ID: <new_message_id>`
  - `In-Reply-To: <original_message_id>` (if reply)
  - `References: <message_id_chain>` (if reply)
- **Ensures subject has "Re:" prefix** if it's a reply and doesn't already have it
- **Maintains RFC 2822 format** with proper header ordering

---

## How It Works

### Flow Diagram:

```
1. Get Email Info
   └─ Returns: email data including thread_id, gmail_message_id
   
2. Prepare Message Fetch
   └─ Checks if reply (has thread_id + gmail_message_id)
   └─ Prepares data for Gmail API call
   
3. Get Original Message (for threading)
   └─ Fetches original email from Gmail API
   └─ Extracts Message-ID header
   
4. Prepare Email Message
   └─ Gets original Message-ID from step 3
   └─ Generates new Message-ID for reply
   └─ Builds In-Reply-To and References headers
   └─ Adds all headers to raw email message
   └─ Encodes in base64url format
   
5. Prepare Gmail Request Body
   └─ Includes threadId (for sender-side threading)
   └─ Includes raw message (with threading headers for recipient-side threading)
   
6. Send Email via Gmail API
   └─ Sends with both threadId AND proper headers
   └─ ✅ Works on both sender and recipient sides!
```

---

## Key Technical Details

### RFC 2822 Threading Headers

1. **Message-ID**: Unique identifier for this email
   - Format: `<timestamp.random@domain>`
   - Example: `<1708123456789.abc123@resolvely.com>`

2. **In-Reply-To**: References the immediate parent email
   - Contains the Message-ID of the email being replied to
   - Example: `In-Reply-To: <1708123456789.abc123@resolvely.com>`

3. **References**: Chain of all Message-IDs in the thread
   - Contains all Message-IDs from the conversation history
   - Example: `References: <msg1@domain.com> <msg2@domain.com> <msg3@domain.com>`

### Subject Line Handling

- If `thread_id` exists and subject doesn't start with "Re:", automatically adds "Re:" prefix
- This ensures proper threading even if draft generator doesn't include it

### Error Handling

- `Get Original Message` node uses `continueOnFail: true`
- If fetching fails, email is still sent (just without threading headers)
- This prevents workflow failures for edge cases

---

## Testing

### What to Test:

1. **New Conversation:**
   - Send first email (no thread_id)
   - Should NOT include In-Reply-To or References headers
   - Should work normally

2. **Reply to Email:**
   - Reply to an existing email (has thread_id)
   - Should include:
     - `Message-ID` header
     - `In-Reply-To` header (original email's Message-ID)
     - `References` header (Message-ID chain)
     - Subject with "Re:" prefix

3. **Thread Continuity:**
   - Multiple replies in same thread
   - Each reply should reference previous Message-IDs
   - Thread should appear correctly on BOTH sides

### Verification:

**On Sender Side (Company Gmail):**
- ✅ Emails should appear in same thread (already working)

**On Recipient Side (Customer Gmail/Email Client):**
- ✅ Emails should now appear in same thread (FIXED!)
- ✅ Thread should be properly grouped
- ✅ Conversation history should be visible

---

## Files Modified

1. `backend/schemas/email.py` - Added `gmail_message_id` to EmailResponse
2. `backend/routers/emails.py` - Return `gmail_message_id` in response
3. `n8n/Send Approved Drafts.json` - Added threading header logic

---

## Next Steps

1. **Deploy changes** to backend
2. **Update n8n workflow** in n8n interface (import updated JSON)
3. **Test with real emails** to verify threading works on both sides
4. **Monitor logs** to ensure Message-ID fetching works correctly

---

## Notes

- This fix ensures **both** Gmail API's `threadId` (sender-side) AND RFC 2822 headers (recipient-side) are used
- The combination ensures threading works across all email clients (Gmail, Outlook, Apple Mail, etc.)
- Backward compatible: new conversations work normally, replies get proper threading

