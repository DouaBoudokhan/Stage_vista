# Debugging AI Recommendation

## The Problem

When scanning a **Headset**, the top 3 recommendations don't include tickets that mention "headset", even though:
- ✅ YOLO correctly detects "Headset"
- ✅ Database has 8 tickets mentioning headsets
- ❌ Top 3 recommendations are unrelated tickets

---

## What I Added

### 1. Debug Logging in `rank_tickets_with_ai()`

Now shows:
```
🎯 AI RECOMMENDATION REQUEST
   Detected Product: Headset
   Category: Headset  
   Product Hint (used): Headset
   Quantity: 5
   Available: 20
   Total Tickets: 100
```

**Check**: Is `Product Hint` actually "Headset"? Or is it something else?

### 2. Debug Logging in `_quick_filter_candidates()`

Now shows:
```
🔍 Quick filter: Looking for 'Headset' in 100 tickets

📊 Top 5 candidates (out of 100):
  1. [80] SD-235529: defective headset
      Reasons: 'Headset' found, 1 equipment keywords, priority:Low
  2. [75] SD-235528: Docking Station Power supplier / Mouse and Headset
      Reasons: 'Headset' found, 3 equipment keywords, priority:Low
  ...
```

**Check**: Do the top 5 candidates include headset tickets?

---

## How to Debug

### Step 1: Scan a Headset in Mobile App

1. Open mobile app
2. Navigate to Stock Entry workflow
3. Scan or detect a Headset
4. Tap "Get AI Recommendation"

### Step 2: Check Backend Logs

Look for these sections in the backend terminal:

```
🎯 AI RECOMMENDATION REQUEST
   Detected Product: <-- WHAT DOES THIS SAY?
   Product Hint (used): <-- WHAT DOES THIS SAY?

🔍 Quick filter: Looking for '<PRODUCT>' in 100 tickets

📊 Top 5 candidates:
  1. [score] TICKET_ID: Title
      Reasons: ...
```

### Step 3: Identify the Issue

**Scenario A: Product Hint is Wrong**
```
Product Hint (used): equipment  <-- NOT "Headset"!
```
**Problem**: The detected product or category isn't being passed correctly  
**Fix**: Check how mobile app sends the request

**Scenario B: Product Hint is Correct, but Scores are Wrong**
```
Product Hint (used): Headset  <-- Correct!

Top 5 candidates:
  1. [30] SD-235523: logout from 7:23  <-- NO "Headset"!
  2. [25] SD-235524: PC update  <-- NO "Headset"!
```
**Problem**: Scoring algorithm is broken  
**Fix**: Adjust weights in `_quick_filter_candidates()`

**Scenario C: Top Candidates are Correct, but Final Top 3 are Wrong**
```
Top 5 candidates:
  1. [80] SD-235529: defective headset  <-- Good!
  2. [75] SD-235528: Docking Station... Headset  <-- Good!

But AI returns:
  1. SD-235523: logout from 7:23  <-- Wrong!
```
**Problem**: Rule-based scoring is overriding pre-filter scores  
**Fix**: Fix `_rule_based_scoring()` to respect product matches

---

## Tickets Mentioning Headsets

From database (should be in top results):

1. **SD-235529**: "defective headset" - Status: Resolved, Priority: Low
2. **SD-235528**: "Docking Station Power supplier / Mouse and Headset" - Status: Waiting for customer
3. **SD-235480**: "I need a new headset" - Status: Blocked  
4. **SD-235466**: "Headset Replacement" - Status: Resolved
5. **SD-235463**: "Headset replacement" - Status: Waiting for customer
6. **SD-235534**: "Headset Issue" - Status: Resolved

---

## Current Scoring System

### Pre-Filter (_quick_filter_candidates)
- Exact product match ("headset" in text): **+50 points**
- Equipment keywords match: **+5 per keyword**
- Priority: High=+20, Medium=+10, Low=+5
- Status (Open/Assigned/In Progress): **+10 points**

### AI Analysis (_rule_based_scoring)
- Exact product match: **+40 points**
- Any equipment keyword: **+20 points**  
- Urgency keywords: **+15 points**
- Priority: High=+10, Medium=+5, Low=+2
- Quantity match: **+10 points**
- Availability: **+10 or -20 points**

---

## Expected Behavior

### When you scan "Headset":

**Pre-Filter should select:**
```
Top 20 candidates:
  1. SD-235529: defective headset (score: ~55-60)
  2. SD-235528: Docking Station... Headset (score: ~55-65)
  3. SD-235534: Headset Issue (score: ~55-60)
  4. SD-235466: Headset Replacement (score: ~55-60)
  5. SD-235463: Headset replacement (score: ~55-60)
  ...
```

**AI Analysis should rank:**
```
Top 3:
  1. SD-235529: defective headset (score: 80-90)
      Reason: "matches Headset, mentions equipment type"
  2. SD-235528: Docking Station... Headset (score: 75-85)
      Reason: "matches Headset, mentions equipment type"
  3. SD-235534: Headset Issue (score: 70-80)
      Reason: "matches Headset, mentions equipment type"
```

---

## Next Steps

1. **Run the test** on mobile app with headset
2. **Copy the backend logs** from the terminal
3. **Share the logs** so I can see:
   - What `Product Hint` was received
   - What the top 5 candidates were
   - What the final top 3 recommendations were
4. **I'll fix the issue** based on what the logs show

---

## Possible Fixes

### If product hint is wrong:
- Check mobile app request body
- Fix how `detected_product` or `category` is passed

### If pre-filter scores are wrong:
- Increase weight for exact product match (50 → 100?)
- Decrease weight for priority/status
- Ignore status entirely (as you mentioned)

### If AI analysis overrides good candidates:
- Make sure `_rule_based_scoring` gives high scores to product matches
- Check availability calculation isn't penalizing too much

---

**Test now and share the logs!** 🔍
