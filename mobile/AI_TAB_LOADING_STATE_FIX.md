# AI Tab Loading State Fix

## Problem
When entering Step 3 with AI Recommendation tab selected by default, users saw:
1. "No AI results, tap to retry" message immediately
2. Clicking "Retry" showed alert: "No tickets available"
3. After waiting a few seconds, it started working

**Root Cause**: Rendering logic checked for `aiRecommendation` existence before checking if tickets were still loading, causing premature "No results" state.

## Solution
Reordered the conditional rendering to prioritize loading states:

```typescript
// OLD (wrong order)
{!aiRecommendation ? (
  ticketsLoading ? "Loading..." : 
  !tickets ? "No tickets" : 
  "Tap to retry"
) : (
  <Results />
)}

// NEW (correct order)
{aiLoading ? (
  "Computing matches..."
) : ticketsLoading ? (
  "Loading tickets..."
) : !tickets ? (
  "No tickets found"
) : !aiRecommendation ? (
  "Tap to retry"
) : (
  <Results />
)}
```

## Flow Now
1. User enters Step 3 → `refetchTickets()` starts
2. UI shows: **"Loading tickets from Jira..."** (ticketsLoading=true)
3. Tickets finish loading → useEffect triggers `getAiRecommendation()`
4. UI shows: **"Computing optimal ticket matches..."** (aiLoading=true)
5. AI completes → Shows recommendations

## Files Modified
- `mobile/screens/WorkflowAssignScreen.tsx` (lines ~716-748)
  - Changed nested ternary inside Surface to flat conditional chain
  - Priority: aiLoading → ticketsLoading → !tickets → !aiRecommendation

## Testing
✅ Enter Step 3 with AI tab → should show "Loading tickets..." immediately
✅ No "tap to retry" until tickets are loaded
✅ No alert "No tickets available" during initial load
✅ Automatic AI recommendation after tickets load
