# Test Scripts Overview

All test scripts are located in the `backend/` directory.

---

## 🎯 Quick Reference

| Script | Purpose | Run Time | Output |
|--------|---------|----------|--------|
| `test_jira_raw.py` | Test Jira API connection | ~5 sec | Terminal + JSON file |
| `test_jira_connection.py` | Test JiraService class | ~10 sec | Terminal + JSON file |
| `test_auth_flow.py` | Test authentication endpoints | ~3 sec | Terminal only |

---

## 📋 Recommended Testing Order

### 1. Configure Jira (Required)
```bash
# Edit backend/.env
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_USER_EMAIL=your@email.com
JIRA_API_TOKEN=your-token
JIRA_PROJECT_KEY=IT
```

### 2. Test Jira Connection
```bash
python test_jira_raw.py
```
**What it tests**: Jira credentials, API access, ticket fetching  
**Output**: Tickets in terminal + `jira_raw_response.json`  
**If fails**: See `TESTING_JIRA.md` troubleshooting section

### 3. Test JiraService
```bash
python test_jira_connection.py
```
**What it tests**: JiraService class, ticket parsing, ADF decoding  
**Output**: Formatted tickets + statistics + `jira_tickets_export.json`  
**If fails**: Check JiraService implementation

### 4. Test Authentication
```bash
python test_auth_flow.py
```
**What it tests**: Login, JWT generation, token validation  
**Output**: Test results for 5 authentication scenarios  
**If fails**: Check database has admin user seeded

### 5. Start Backend
```bash
uvicorn app.main:app --reload
```
**What it does**: Starts FastAPI server with hot reload  
**Expected**: "✅ Database initialization completed successfully"

### 6. Test Mobile App
```bash
# In mobile directory
npm start
```
**What to test**:
- Login with `admin@stockit.local` / `admin123`
- Navigate to Stock Entry workflow
- View "All Tickets" tab
- Scan product and get AI recommendation

---

## 🔍 Script Details

### 1. test_jira_raw.py

**Purpose**: Quick Jira connection test with raw API calls.

**What it does**:
1. ✅ Validates Jira configuration
2. ✅ Tests authentication (`GET /rest/api/3/myself`)
3. ✅ Fetches open tickets (`GET /rest/api/3/search`)
4. ✅ Displays tickets in terminal
5. ✅ Saves raw JSON to `jira_raw_response.json`

**Use when**:
- First time setting up Jira
- Debugging authentication issues
- Checking if Jira is accessible
- Finding custom field IDs

**Output files**:
- `jira_raw_response.json` - Raw Jira API response

**Example output**:
```
Test 1: Authenticating with Jira
✅ Authentication successful!

Test 2: Fetching Open Tickets
✅ Query successful!
Total matching tickets: 5

Ticket 1: IT-123
  Summary: New laptop request
  Status: Open
  Priority: High
  ...
```

---

### 2. test_jira_connection.py

**Purpose**: Comprehensive test of JiraService implementation.

**What it does**:
1. ✅ Shows Jira configuration
2. ✅ Tests direct API connection
3. ✅ Initializes JiraService
4. ✅ Fetches tickets via JiraService
5. ✅ Displays formatted ticket details
6. ✅ Shows summary statistics
7. ✅ Exports to JSON

**Use when**:
- Testing JiraService changes
- Verifying ticket parsing logic
- Checking ADF description extraction
- Generating test data for AI

**Output files**:
- `jira_tickets_export.json` - Parsed tickets in StockIT format

**Example output**:
```
Jira Configuration
✅ JIRA_BASE_URL           = https://domain.atlassian.net
✅ JIRA_USER_EMAIL         = email@domain.com
✅ JIRA_API_TOKEN          = ***1234
✅ JIRA_PROJECT_KEY        = IT

Testing JiraService
✅ JiraService initialized successfully
✅ Successfully fetched 5 open ticket(s)

Open Tickets (5 total)
┌─ IT-123 ──────────────────────────────────────
│ Title: New laptop request
│ Status: Open
│ Priority: High
│ Category: Laptop
│ Requested Quantity: 1
│ Cost Center: DEV-TEAM
│ Created: 2026-08-01 10:30:00
│ Updated: 2026-08-04 14:22:00
│ Description: Requesting MacBook Pro...
└────────────────────────────────────────────────

Summary
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
```

---

### 3. test_auth_flow.py

**Purpose**: Test authentication endpoints and JWT flow.

**What it does**:
1. ✅ Health check
2. ✅ Login with default admin
3. ✅ Get tickets without auth
4. ✅ Get tickets with auth
5. ✅ Test invalid token handling

**Use when**:
- Testing auth changes
- Verifying JWT generation
- Checking token validation
- Testing mobile login flow

**No output files** (terminal only)

**Example output**:
```
Test Summary
✅ PASS  Health Check
✅ PASS  Login
✅ PASS  Tickets (No Auth)
✅ PASS  Tickets (With Auth)
✅ PASS  Invalid Token

Total: 5/5 tests passed

🎉 All tests passed!
```

---

## 📂 Output Files

### jira_raw_response.json
- Raw JSON response from Jira API
- Includes all fields and metadata
- Used for debugging API issues
- Shows custom field IDs

**Structure**:
```json
{
  "startAt": 0,
  "maxResults": 50,
  "total": 5,
  "issues": [
    {
      "key": "IT-123",
      "fields": {
        "summary": "...",
        "status": {...},
        "priority": {...},
        "customfield_10037": 1,
        ...
      }
    }
  ]
}
```

### jira_tickets_export.json
- Parsed tickets in StockIT format
- After processing by JiraService
- Ready for AI recommendation
- Includes extracted text from ADF

**Structure**:
```json
[
  {
    "id": "123",
    "jira_key": "IT-123",
    "title": "New laptop request",
    "description": "Plain text description",
    "status": "Open",
    "priority": "High",
    "category": "Laptop",
    "requested_quantity": 1,
    "cost_center": "DEV-TEAM",
    "component": "Tunis Office",
    "created_at": "2026-08-01T10:30:00+00:00",
    "jira_last_updated": "2026-08-04T14:22:00+00:00"
  }
]
```

---

## 🐛 Troubleshooting

### All tests fail with connection error
```bash
# Check if backend is running
curl http://localhost:8000/health
```

### test_jira_raw.py fails with 401
→ Invalid credentials in `.env`  
→ Generate new API token: https://id.atlassian.com/manage-profile/security/api-tokens

### test_jira_connection.py shows no tickets
→ No open tickets in project  
→ Wrong `JIRA_PROJECT_KEY`  
→ Create test ticket in Jira

### test_auth_flow.py fails on login
→ Database not initialized  
→ Run: `uvicorn app.main:app` to trigger migration  
→ Check for "✅ Default admin user seeded" message

---

## 📖 Documentation Links

- **Jira Test Guide**: `TESTING_JIRA.md`
- **Quick Start**: `QUICK_START_JIRA_TEST.md`
- **Auth Flow**: `AUTHENTICATION_FLOW_FIXED.md`
- **Status**: `STATUS_AND_NEXT_STEPS.md`
- **Refactoring Summary**: `REFACTORING_SUMMARY.md`

---

## ✅ Success Criteria

All tests should pass:

- [x] `test_jira_raw.py` → Shows tickets
- [x] `test_jira_connection.py` → Shows formatted tickets + export
- [x] `test_auth_flow.py` → 5/5 tests pass
- [x] Backend starts without errors
- [x] Mobile app can login
- [x] Mobile app shows Jira tickets

---

**Ready to test!** Start with `python test_jira_raw.py` 🚀
