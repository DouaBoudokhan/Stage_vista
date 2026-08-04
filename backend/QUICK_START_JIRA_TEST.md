# Quick Start - Test Jira Connection

## 1️⃣ Configure Jira Credentials

Edit `backend/.env`:

```bash
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_USER_EMAIL=your-email@domain.com
JIRA_API_TOKEN=your-api-token-here
JIRA_PROJECT_KEY=IT
```

**Get API Token**: https://id.atlassian.com/manage-profile/security/api-tokens

---

## 2️⃣ Run Quick Test

```bash
cd backend
python test_jira_raw.py
```

**Expected**: List of open tickets printed to terminal + saved to `jira_raw_response.json`

---

## 3️⃣ Run Full Test (Optional)

```bash
python test_jira_connection.py
```

**Expected**: Formatted tickets + statistics + saved to `jira_tickets_export.json`

---

## ✅ Success Looks Like:

```
✅ Authentication successful!
   Authenticated as: Your Name
   Email: your-email@domain.com

✅ Query successful!
Total matching tickets: 5
Tickets returned: 5

Ticket 1: IT-123
────────────────────────────────────────────────────────────────────
  Summary: New laptop request for developer
  Status: Open
  Priority: High
  ...
```

---

## ❌ Common Errors:

### "Authentication failed! Status: 401"
→ **Fix**: Check email and API token in `.env`

### "No open tickets found"
→ **Fix**: Check `JIRA_PROJECT_KEY` or create test ticket in Jira

### "Connection Error"
→ **Fix**: Check `JIRA_BASE_URL` (should be https://your-domain.atlassian.net)

---

## 📝 View Results:

```bash
# View raw Jira response
cat jira_raw_response.json

# View parsed tickets
cat jira_tickets_export.json
```

---

**That's it!** If the test succeeds, your Jira integration is working. 🎉

Next: Test the full backend with `python test_auth_flow.py`
