# Exclude Already Assigned Tickets from Recommendations

## Problem
When scanning equipment for assignment, the AI was recommending tickets that had already been assigned equipment in a previous scan. This causes:
- Duplicate assignments to the same ticket
- Incorrect inventory tracking
- User confusion (seeing same ticket recommended multiple times)

**Example**: User scans headset → assigns to ticket SD-12345 → later scans another headset → SD-12345 appears in top 3 recommendations again.

## Root Cause
The recommendation endpoint was not filtering out tickets that have existing `stock_exit` records. All open tickets were eligible for recommendation, regardless of whether they'd already received equipment.

## Solution
Added filtering logic in `recommend_tickets` endpoint to exclude tickets with stock exits:

```python
# Filter out tickets that already have stock exits (already assigned equipment)
from ..models.stock_exit import StockExit
assigned_ticket_ids = db.query(StockExit.ticket_id).distinct().all()
assigned_ticket_ids = [tid[0] for tid in assigned_ticket_ids]

available_tickets = [t for t in tickets if t.jira_key not in assigned_ticket_ids]

print(f"🔍 Filtering: {len(tickets)} total tickets → {len(available_tickets)} available (excluded {len(tickets) - len(available_tickets)} already assigned)")

if not available_tickets:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="No unassigned tickets available. All tickets have been assigned equipment."
    )
```

## How It Works
1. Fetch all open tickets from Jira (as before)
2. Query `stock_exits` table to get all ticket IDs that have stock exits
3. Filter tickets: only keep tickets NOT in the assigned list
4. Pass filtered tickets to AI recommendation service
5. AI analyzes only unassigned tickets

## Database Relationships Used
- `Ticket.stock_exits`: relationship to StockExit records
- `StockExit.ticket_id`: Foreign key to tickets.id (Jira key)

## Edge Cases Handled
- If ALL tickets have been assigned → returns 404 with helpful message
- If no tickets match equipment + unassigned → returns empty recommendations
- Distinct query ensures multi-item assignments to same ticket don't create duplicates

## Files Modified
- `backend/app/routers/inventory.py` (lines ~126-143)
  - Added stock_exit query and filtering logic
  - Pass `available_tickets` instead of `tickets` to AI service

## Testing
✅ Scan headset → assign to ticket A → scan another headset → ticket A should NOT appear in recommendations
✅ If all matching tickets are assigned → should get "No unassigned tickets available" error
✅ Multiple stock exits to same ticket → should still be excluded (distinct query)
✅ Backend logs show: "X total tickets → Y available (excluded Z already assigned)"

## Business Logic
Once a ticket receives equipment (has a stock_exit), it:
- Is excluded from future AI recommendations
- Can still be manually selected in "All Tickets" tab (if needed for special cases)
- Can still be selected via "Ticket ID" tab (manual override)

This ensures:
- Each ticket typically gets one equipment assignment
- AI recommendations stay relevant
- Manual override still possible for edge cases
