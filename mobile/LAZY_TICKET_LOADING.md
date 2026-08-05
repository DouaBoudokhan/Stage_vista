# Lazy Ticket Loading - Fetch Only When Needed ✅

## Problem Identified

Jira tickets were being fetched **too early** in the workflow:

```
User opens assignment screen
    ↓
Component mounts
    ↓
useTickets() called immediately  ← PROBLEM!
    ↓
GET /tickets → Jira API fetch (100 tickets)
    ↓
Backend logs: "Fetching from Jira..."
    ↓
User is still in Step 1 (YOLO scanning)...
    ↓
YOLO takes 5-10 seconds...
    ↓
(Tickets loaded but not needed yet!)
```

**Impact:**
- Unnecessary Jira API call during YOLO detection
- Wasted network bandwidth
- Backend processing overhead
- Tickets might become stale by the time user reaches Step 3

---

## Solution: Lazy Loading

**Only fetch tickets when user enters Step 3** (ticket selection):

```
User opens assignment screen
    ↓
Component mounts
    ↓
useQuery with enabled: false  ← Don't fetch yet!
    ↓
Step 1: YOLO scanning (no Jira call)
    ↓
Step 2: Choose quantity (no Jira call)
    ↓
Step 3: Choose ticket assignment
    ↓
NOW fetch tickets: refetchTickets()  ← Only now!
    ↓
GET /tickets → Jira API fetch
    ↓
Backend logs: "Fetching from Jira..."
```

---

## Changes Made

### File: `mobile/screens/WorkflowAssignScreen.tsx`

#### 1. Added Imports
```typescript
// ADDED
import { useQuery } from '@tanstack/react-query';
import { ticketsApi } from '../api/tickets';

// REMOVED
import { useTickets } from '../hooks/useApi';
```

#### 2. Changed useTickets to Lazy useQuery
```typescript
// BEFORE
const {
  data: tickets,
  isLoading: ticketsLoading,
  isFetching: ticketsFetching,
  isError: ticketsIsError,
  error: ticketsError,
} = useTickets();  // ← Fetches immediately!

// AFTER
const {
  data: tickets,
  isLoading: ticketsLoading,
  isFetching: ticketsFetching,
  isError: ticketsIsError,
  error: ticketsError,
  refetch: refetchTickets,  // ← Manual trigger!
} = useQuery({
  queryKey: ['tickets'],
  queryFn: ticketsApi.getAll,
  enabled: false,  // ← Don't fetch on mount!
});
```

#### 3. Trigger Fetch in Step 3
```typescript
// NEW: Fetch tickets when entering Step 3
useEffect(() => {
  if (step === 3) {
    // Fetch tickets when entering Step 3 (if not already fetched)
    if (!tickets && !ticketsLoading && !ticketsFetching) {
      console.log('[workflow2] Step 3: Fetching tickets from Jira...');
      refetchTickets();  // ← Trigger fetch now!
    }
    
    // Trigger AI recommendation if method is 'ai'
    if (method === 'ai' && selectedProduct && !aiRecommendation) {
      getAiRecommendation();
    }
  }
}, [step, method, selectedProduct, aiRecommendation, tickets]);
```

---

## New Workflow Timeline

### Step 1: YOLO Scanning (0-10 seconds)
```
✅ No Jira API call
✅ Backend is quiet
✅ User scans equipment
```

### Step 2: Choose Quantity (~2 seconds)
```
✅ No Jira API call
✅ User enters quantity
```

### Step 3: Choose Ticket Assignment
```
🔄 NOW fetching tickets from Jira!
Backend logs: "Fetching from Jira..."
100 tickets synced
✅ Tickets ready for AI or manual selection
```

---

## Benefits

### ✅ Faster YOLO Experience
- No background network calls during Step 1
- YOLO can use full device resources
- No competing for network bandwidth

### ✅ Fresher Data
- Tickets fetched right before they're needed
- Less chance of stale data (especially ticket status)
- More up-to-date recommendations

### ✅ Reduced API Calls
- If user abandons workflow at Step 1/2, no Jira call made
- Only fetch when user actually needs tickets

### ✅ Better Performance
- Step 1 & 2 are instant (no network wait)
- Backend only processes when necessary

---

## Logs Comparison

### Before Fix (Tickets Loaded Too Early)
```
[Component Mount]
→ GET /tickets
→ Backend: "Fetching from Jira..."
→ Backend: "✅ Synced 100 tickets"

[Step 1: YOLO Scanning]
(Tickets already loaded but not used yet)

[Step 2: Choose Quantity]
(Tickets still not used)

[Step 3: Ticket Selection]
→ Use already-loaded tickets
```

### After Fix (Lazy Loading)
```
[Component Mount]
(No API calls)

[Step 1: YOLO Scanning]
(No API calls - clean!)

[Step 2: Choose Quantity]
(No API calls)

[Step 3: Ticket Selection]
→ GET /tickets  ← Only now!
→ Backend: "Fetching from Jira..."
→ Backend: "✅ Synced 100 tickets"
→ Use freshly-loaded tickets
```

---

## Edge Cases Handled

### 1. User Goes Back from Step 3 to Step 2
```
Step 3 → Tickets fetched
User clicks "Back"
Step 2 → Tickets still cached (React Query)
User clicks "Continue"
Step 3 → Uses cached tickets (no refetch)
```

### 2. User Switches Assignment Methods
```
Step 3 → Method: AI → Tickets fetched
User switches to "Manual List"
→ Uses same cached tickets (no refetch)
```

### 3. Tickets Already Cached
```
Step 3 → Tickets already in cache
→ No refetch needed
→ Instant display
```

### 4. User Abandons Workflow
```
Step 1 → User scans
Step 2 → User clicks "Cancel"
→ No Jira API call ever made ✅
```

---

## Testing

### Test 1: Verify No Early Fetch
1. Open WorkflowAssignScreen
2. Stay on Step 1 (don't proceed)
3. **Check backend logs:** Should be empty (no "Fetching from Jira...")
4. **Expected:** No Jira API call

### Test 2: Fetch Only in Step 3
1. Open WorkflowAssignScreen
2. Scan equipment (Step 1)
3. Choose quantity (Step 2)
4. Proceed to Step 3
5. **Check backend logs:** Should now see "Fetching from Jira..."
6. **Expected:** Jira call only when entering Step 3

### Test 3: Cache Works
1. Complete Test 2 (tickets loaded)
2. Click "Back" to Step 2
3. Click "Continue" to Step 3 again
4. **Check backend logs:** Should NOT see second "Fetching from Jira..."
5. **Expected:** Uses cached tickets

---

## Performance Impact

### Scenario: User Scans and Assigns
**Before:**
```
Component mount:        0.1s
GET /tickets:           2.0s  ← Wasted during YOLO
YOLO scan:              8.0s
Choose quantity:        2.0s
Step 3 (tickets ready): 0.0s  (already loaded)
Total:                 12.1s
```

**After:**
```
Component mount:        0.1s
YOLO scan:              8.0s  ← No background Jira call!
Choose quantity:        2.0s
Step 3 + GET /tickets:  2.0s  ← Fetched now
Total:                 12.1s
```

**Same total time, but:**
- ✅ YOLO step is cleaner (no competing network)
- ✅ Data is fresher (fetched closer to use)
- ✅ Less wasted if user cancels early

### Scenario: User Cancels Early
**Before:**
```
Component mount:        0.1s
GET /tickets:           2.0s  ← WASTED!
User clicks Cancel:     1.0s
Total wasted:           2.0s
```

**After:**
```
Component mount:        0.1s
User clicks Cancel:     1.0s
Total wasted:           0.0s  ← No Jira call!
```

---

## Status: ✅ READY TO TEST

**Mobile:** Lazy ticket loading implemented
**Backend:** No changes needed

**Test now:**
1. Open assignment screen → Check logs (should be quiet)
2. Scan equipment → Check logs (should still be quiet)
3. Enter Step 3 → Check logs (NOW fetching from Jira)
4. Verify workflow completes successfully

🚀
