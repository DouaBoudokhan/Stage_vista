# Testing Jira Connection

This directory contains test scripts to verify your Jira integration works correctly.

---

## Prerequisites

1. **Jira Account** with API access
2. **API Token** generated from: https://id.atlassian.com/manage-profile/security/api-tokens
3. **Environment Variables** configured in `.env`

### Required Environment Variables

```bash
# In backend/.env
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_USER_EMAIL=your-email@domain.com
JIRA_API_TOKEN=your-jira-api-token
JIRA_PROJECT_KEY=IT
```

---

## Test Scripts

### 1. `test_jira_raw.py` - Quick Raw API Test

**Purpose**: Makes direct API calls to Jira and shows raw responses.

**What it does**:
- ✅ Tests authentication with Jira
- ✅ Fetches open tickets from your project
- ✅ Displays tickets in terminal
- ✅ Saves raw JSON response to `jira_raw_response.json`

**Run**:
```bash
cd backend
python test_jira_raw.py
```

**Expected Output**:
```
================================================================================
  Raw Jira API Test
================================================================================

Configuration:
  JIRA_BASE_URL: https://your-domain.atlassian.net
  JIRA_USER_EMAIL: your-email@domain.com
  JIRA_API_TOKEN: ***1234
  JIRA_PROJECT_KEY: IT

================================================================================
Test 1: Authenticating with Jira
================================================================================

✅ Authentication successful!

User Info:
  Name: John Doe
  Email: john.doe@domain.com
  Account ID: 5b10ac8d82e05b22cc7d4ef5
  Active: True

================================================================================
Test 2: Fetching Open Tickets
================================================================================

JQL Query: project = IT AND status = Open ORDER BY created DESC
URL: https://your-domain.atlassian.net/rest/api/3/search

✅ Query successful!
Total matching tickets: 5
Tickets returned: 5

================================================================================
Tickets (showing 5)
================================================================================

Ticket 1: IT-123
────────────────────────────────────────────────────────────────────────────────
  Summary: New laptop request for developer
  Status: Open
  Priority: High
  Labels: hardware, laptop
  Quantity: 1
  Cost Center: DEV-TEAM
  Component: Tunis Office
  Created: 2026-08-01T10:30:00.000+0000
  Updated: 2026-08-04T14:22:00.000+0000
  Description: Requesting a new MacBook Pro for development work...

...

================================================================================
✅ Raw response saved to: jira_raw_response.json
================================================================================
```

---

### 2. `test_jira_connection.py` - Full Service Test

**Purpose**: Tests the complete JiraService implementation with formatted output.

**What it does**:
- ✅ Validates configuration
- ✅ Tests direct API connection
- ✅ Tests JiraService class
- ✅ Displays formatted ticket details
- ✅ Shows summary statistics
- ✅ Exports to `jira_tickets_export.json`

**Run**:
```bash
cd backend
python test_jira_connection.py
```

**Expected Output**:
```
================================================================================
  StockIT - Jira Connection Test
================================================================================

================================================================================
  Jira Configuration
================================================================================

✅ JIRA_BASE_URL           = https://your-domain.atlassian.net
✅ JIRA_USER_EMAIL         = your-email@domain.com
✅ JIRA_API_TOKEN          = ***1234
✅ JIRA_PROJECT_KEY        = IT
✅ JIRA_ISSUE_TYPE         = Hardware request
✅ JIRA_COST_CENTER        = TEST-STOCKIT-PFE
✅ JIRA_COMPONENT          = ETX Tunis

================================================================================
  Testing Direct Jira API Connection
================================================================================

Testing connection to: https://your-domain.atlassian.net
Using email: your-email@domain.com
Calling endpoint: https://your-domain.atlassian.net/rest/api/3/myself

✅ Connection successful!
   Authenticated as: John Doe
   Email: john.doe@domain.com
   Account ID: 5b10ac8d82e05b22cc7d4ef5

================================================================================
  Testing JiraService
================================================================================

✅ JiraService initialized successfully

Fetching open tickets from Jira...
✅ Successfully fetched 5 open ticket(s)

================================================================================
  Open Tickets (5 total)
================================================================================

Ticket 1/5:
┌─ IT-123 ──────────────────────────────────────────────────────────────────
│ Title: New laptop request for developer
│ Status: Open
│ Priority: High
│ Category: Laptop
│ Requested Quantity: 1
│ Cost Center: DEV-TEAM
│ Created: 2026-08-01 10:30:00
│ Updated: 2026-08-04 14:22:00
│ Description: Requesting a new MacBook Pro for development work. Current laptop is 5 years old...
└──────────────────────────────────────────────────────────────────────────────

...

================================================================================
  Summary
================================================================================

Total Tickets: 5

By Status:
  • Open: 5

By Priority:
  • High: 2
  • Medium: 2
  • Low: 1

By Category:
  • Laptop: 2
  • Headset: 1
  • Mouse: 1
  • Monitor: 1

================================================================================
  Export
================================================================================

✅ Exported 5 ticket(s) to: jira_tickets_export.json

================================================================================
  ✅ Test completed successfully!
================================================================================
```

---

## Troubleshooting

### Problem: "❌ Missing required Jira configuration!"

**Cause**: Environment variables not set.

**Solution**:
```bash
# Create or edit backend/.env
nano backend/.env

# Add these lines:
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_USER_EMAIL=your-email@domain.com
JIRA_API_TOKEN=your-api-token
JIRA_PROJECT_KEY=IT
```

---

### Problem: "❌ Authentication failed! Status: 401"

**Cause**: Invalid credentials or API token.

**Solution**:
1. Verify your email is correct
2. Generate a new API token: https://id.atlassian.com/manage-profile/security/api-tokens
3. Copy the token immediately (you can't view it again)
4. Update `.env` with new token
5. Restart the test

**Test credentials manually**:
```bash
# Test with curl
curl -X GET "https://your-domain.atlassian.net/rest/api/3/myself" \
  -H "Authorization: Basic $(echo -n 'your-email@domain.com:your-api-token' | base64)" \
  -H "Content-Type: application/json"
```

---

### Problem: "❌ Authentication failed! Status: 403"

**Cause**: Account doesn't have permission to access the API.

**Solution**:
- Ask your Jira administrator to grant you API access
- Verify your account is not restricted
- Check if your organization allows API access

---

### Problem: "⚠️ No open tickets found in project"

**Cause**: No tickets match the search criteria.

**Possible reasons**:
1. Wrong project key (check `JIRA_PROJECT_KEY`)
2. No tickets with status "Open"
3. You don't have permission to view tickets

**Solution**:
1. Verify project key:
   ```bash
   # List all projects
   curl -X GET "https://your-domain.atlassian.net/rest/api/3/project" \
     -H "Authorization: Basic $(echo -n 'email:token' | base64)"
   ```

2. Check for tickets with any status:
   ```bash
   # Modify JQL in test script temporarily
   jql = f"project = {settings.JIRA_PROJECT_KEY} ORDER BY created DESC"
   ```

3. Verify permissions in Jira web UI

---

### Problem: "requests.exceptions.ConnectionError"

**Cause**: Cannot reach Jira server.

**Solutions**:
- Check your internet connection
- Verify `JIRA_BASE_URL` is correct (no trailing slash)
- Try accessing the URL in your browser
- Check if behind a corporate firewall/proxy

---

### Problem: Custom fields show as "N/A"

**Cause**: Custom field IDs don't match your Jira instance.

**Solution**:
1. Find your custom field IDs in Jira:
   - Go to Jira Settings → Issues → Custom fields
   - Note the field IDs (e.g., customfield_10037)

2. Update the field mapping in `app/services/jira_service.py`:
   ```python
   quantity = fields.get('customfield_XXXXX')  # Replace XXXXX with your ID
   ```

3. Or use the Jira API to discover fields:
   ```bash
   curl "https://your-domain.atlassian.net/rest/api/3/field" \
     -H "Authorization: Basic $(echo -n 'email:token' | base64)"
   ```

---

## Testing Workflow

### Step 1: Quick Test (Raw)
```bash
python test_jira_raw.py
```
- If this fails, fix Jira credentials first
- If successful, you'll see authentication + tickets

### Step 2: Full Test (Service)
```bash
python test_jira_connection.py
```
- Tests the actual JiraService used by the backend
- Verifies ticket parsing and formatting
- Exports tickets for inspection

### Step 3: Check Exported Data
```bash
# View raw JSON response
cat jira_raw_response.json | python -m json.tool

# View parsed tickets
cat jira_tickets_export.json | python -m json.tool
```

### Step 4: Test in Backend
```bash
# Start backend
uvicorn app.main:app --reload

# Test ticket endpoint
curl http://localhost:8000/tickets
```

### Step 5: Test in Mobile App
1. Start mobile app
2. Login with admin credentials
3. Navigate to Stock Entry workflow
4. Check "All Tickets" tab
5. Verify tickets appear

---

## Output Files

### `jira_raw_response.json`
Raw JSON response from Jira API (includes all fields and metadata).

**Use for**:
- Debugging API responses
- Finding custom field IDs
- Understanding Jira data structure

### `jira_tickets_export.json`
Parsed ticket data in StockIT format (after processing by JiraService).

**Use for**:
- Verifying ticket parsing logic
- Checking field mappings
- Testing AI recommendation inputs

---

## Next Steps After Successful Tests

1. ✅ Jira connection works
2. ✅ Tickets fetched successfully
3. ✅ Data parsed correctly

**Now test the full integration**:

```bash
# Terminal 1: Start backend
cd backend
uvicorn app.main:app --reload

# Terminal 2: Test authentication
cd backend
python test_auth_flow.py

# Terminal 3: Start mobile app
cd mobile
npm start

# Mobile: Login and test Stock Entry workflow
# Email: admin@stockit.local
# Password: admin123
```

---

## Additional Resources

- **Jira REST API Docs**: https://developer.atlassian.com/cloud/jira/platform/rest/v3/
- **Generate API Token**: https://id.atlassian.com/manage-profile/security/api-tokens
- **JQL Guide**: https://www.atlassian.com/software/jira/guides/expand-jira/jql
- **Atlassian Document Format**: https://developer.atlassian.com/cloud/jira/platform/apis/document/structure/

---

**Need Help?**

If tests are still failing after following troubleshooting steps:
1. Check `jira_raw_response.json` for error details
2. Verify Jira web UI access with same credentials
3. Contact Jira administrator for API access
4. Review Jira audit logs for failed authentication attempts
