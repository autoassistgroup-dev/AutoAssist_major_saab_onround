# 🧪 Jasmine Feedback — Full Test Plan

> **App:** `http://localhost:5000`  
> **Date:** March 11, 2026  
> **Tester:** _______________  

---

## 🚀 SETUP — Start Fresh

### 1. Start the App
```bash
cd "/Users/appleenterprises/Desktop/mission abort clone version"
python3 app.py
```
Open **http://localhost:5000** in your browser.

### 2. Login as Admin
- Go to the login page
- Enter your **Admin** credentials
- You should land on the **Tickets** page

### 3. Create a Test Ticket
- Click **"Create Ticket"** button
- Fill in:
  - **Subject:** `TEST - Jasmine QA Check`
  - **Body:** `This is a test ticket for QA testing`
  - **Name:** `Test Customer`
  - **Email:** `test@example.com`
  - **Priority:** `Medium`
- Click **Submit**
- ✏️ **Write down the Ticket ID** (e.g. `M12AB3`): _______________

---

## 🛡️ PHASE 1 — Admin Tests

> Stay logged in as **Admin** for all Phase 1 tests.

---

### ① Backdate Claim Date

> *"Unable to backdate the claim date"*

| Step | Action | Expected |
|:----:|--------|----------|
| 1 | Open your test ticket | Detail page loads |
| 2 | Find & click **"Edit Vehicle & Claim Info"** button | Modal opens |
| 3 | Set **Claim Date** to `2024-06-15` (past date) | Date picker accepts it |
| 4 | Click **Save** | ✅ Success message, page reloads showing `2024-06-15` |

```
Result:  ⬜ PASS    ⬜ FAIL
Notes: 
```

---

### ② Re-edit Fields After Saving

> *"Can't change technician, service date, claim date after initially setting them"*

| Step | Action | Expected |
|:----:|--------|----------|
| 1 | Open the **same ticket** from Test ① | Claim date shows `2024-06-15` |
| 2 | Click **"Edit Vehicle & Claim Info"** again | Modal opens with `2024-06-15` pre-filled |
| 3 | Change Claim Date to `2025-03-01` | Field is editable |
| 4 | Change Service Date to any date | Field is editable |
| 5 | Save | ✅ New values show after reload |

```
Result:  ⬜ PASS    ⬜ FAIL
Notes: 
```

---

### ③ Revisit Section Visible Without Selecting "Revisit" Outcome

> *"Revisit section should be visible during the claim process"*

| Step | Action | Expected |
|:----:|--------|----------|
| 1 | Open the test ticket | |
| 2 | Scroll to the **Outcome / Sidebar** area | |
| 3 | Look for **"Revisit Details"** panel | Should be visible **WITHOUT** choosing "Revisit" as outcome |
| 4 | Can you fill in Revisit Date, Technician, Reason? | Fields should be editable |

```
Result:  ⬜ PASS    ⬜ FAIL
Notes: 
```

---

### ④ Document Preview (Admin)

> *"Document preview says 'data not available'"*

| Step | Action | Expected |
|:----:|--------|----------|
| 1 | Open a ticket that has **email attachments** (image/PDF) | Attachment cards visible |
| 2 | Click **👁 Preview** button | File displays inline |
| 3 | Click **⬇ Download** button | File downloads to your Mac |
| 4 | If preview fails — what's the exact error message? | Write it down |

> 💡 If your test ticket has no attachments, find an existing ticket that does.

```
Result:  ⬜ PASS    ⬜ FAIL
Error message (if any): 
```

---

### ⑤ Conversation Message Order

> *"New messages should go at bottom"*

| Step | Action | Expected |
|:----:|--------|----------|
| 1 | Open a ticket with **2+ replies** | |
| 2 | Look at the conversation | **Oldest** message at top, **newest** at bottom |
| 3 | Type a reply and send it | New reply appears at the **bottom** |

```
Result:  ⬜ PASS    ⬜ FAIL
Notes: 
```

---

### ⑥ Refresh Button on Tickets Page

> *"Refresh button doesn't work"*

| Step | Action | Expected |
|:----:|--------|----------|
| 1 | Go to **Tickets** list page | |
| 2 | Click the **🔄 Refresh** button (top-right) | Button shows spinner |
| 3 | Wait 1-2 seconds | Ticket list updates (no full page reload) |
| 4 | Open browser console (F12 → Console tab) and click Refresh again | No red errors |

> 💡 Also try opening `http://localhost:5000/api/index/tickets` directly in a new tab — if you see JSON data, the API works.

```
Result:  ⬜ PASS    ⬜ FAIL
Console errors (if any): 
```

---

### ⑦ New Customer Message Notification (Red Dot)

> *"No notification/red light for new customer messages"*

**Step A — Simulate a customer reply:**

Open a **new Terminal window** and run:
```bash
curl -X POST http://localhost:5000/api/webhook/reply \
  -H "Content-Type: application/json" \
  -d '{"ticket_id": "REPLACE_ME", "message": "Hello, any update on my ticket?", "sender_name": "Test Customer"}'
```
> ⚠️ Replace `REPLACE_ME` with your test ticket ID from Setup Step 3.

**Step B — Check the notification:**

| Step | Action | Expected |
|:----:|--------|----------|
| 1 | Run the curl command above | Terminal shows `"success": true` |
| 2 | Go to **Tickets** list page (or refresh) | 🔴 Red dot/badge next to that ticket |
| 3 | Click into the ticket | Red dot clears |
| 4 | Go back to tickets list | Dot is gone |

```
Result:  ⬜ PASS    ⬜ FAIL
Notes: 
```

---

### ⑧ Forward a Ticket → Appears in "Forwarded to You"

> *"Forwarded ticket didn't go into forwarded section"*

| Step | Action | Expected |
|:----:|--------|----------|
| 1 | Open the test ticket | |
| 2 | Click **"Forward"** button | Modal opens |
| 3 | Select **another team member** (or Tech Director) | |
| 4 | Type a note: `"Please review this claim"` | |
| 5 | Click **Forward** / **Submit** | ✅ Success message |
| 6 | **Logout** | |
| 7 | **Login as the person you forwarded to** | |
| 8 | Check the top of the Tickets page | **"Forwarded to You"** section shows the ticket |

```
Result:  ⬜ PASS    ⬜ FAIL
Notes: 
```

---

### ⑨ "Returned by Tech" Badge Visible on Main Page

> *"Not clear that ticket came back from tech"*

> ⚠️ Do this test **after** Test ⑧. You need a forwarded ticket first.

| Step | Action | Expected |
|:----:|--------|----------|
| 1 | Stay logged in as whoever the ticket was forwarded to | |
| 2 | Open the forwarded ticket | |
| 3 | Click **"Return to Admin"** (or similar button) | Success |
| 4 | **Logout** → **Login as Admin** | |
| 5 | Go to Tickets list | Ticket has a clear **"Returned by [Name]"** badge |

```
Result:  ⬜ PASS    ⬜ FAIL
Notes: 
```

---

## 🔧 PHASE 2 — Tech Director Tests

> **Logout** from Admin → **Login as Tech Director**

---

### ⑩ Private Notes / Forwarding Notes Visible to Tech

> *"Private messages don't pull through to tech"*

| Step | Action | Expected |
|:----:|--------|----------|
| 1 | Open the ticket that Admin forwarded in Test ⑧ | |
| 2 | Look for **"Forwarding & Notes"** section | Admin's note `"Please review this claim"` is visible |
| 3 | Also check the **Conversation** thread | Is the forwarding note in the conversation too? |

```
Result:  ⬜ PASS    ⬜ FAIL
Notes: 
```

---

### ⑪ Admin Replies Visible in Ticket (Tech View)

> *"Admin messages only show on main page, not in ticket"*

| Step | Action | Expected |
|:----:|--------|----------|
| 1 | Open a ticket where Admin **sent a regular reply** | |
| 2 | Check the **Conversation** section | Admin's reply shows with "Support Team" tag |

> 💡 If needed: Login as Admin first, send a reply to the test ticket, then login as Tech and check.

```
Result:  ⬜ PASS    ⬜ FAIL
Notes: 
```

---

### ⑫ Document Preview (Tech View)

> *"Unable to view documents as Tech"*

| Step | Action | Expected |
|:----:|--------|----------|
| 1 | Open a ticket with attachments | |
| 2 | Click **👁 Preview** | File displays inline |
| 3 | Click **⬇ Download** | File downloads |

```
Result:  ⬜ PASS    ⬜ FAIL
Notes: 
```

---

### ⑬ Forward from Tech → Goes to Forwarded Section

> *"Ticket forwarded from tech didn't show in forwarded section"*

| Step | Action | Expected |
|:----:|--------|----------|
| 1 | Open a ticket as Tech Director | |
| 2 | Click **"Return to Admin"** or **"Forward"** | |
| 3 | Add a note and submit | ✅ Success |
| 4 | **Logout** → **Login as the target person** | |
| 5 | Check **"Forwarded to You"** section | Ticket appears |

```
Result:  ⬜ PASS    ⬜ FAIL
Notes: 
```

---

## 📊 FINAL SCORECARD

| # | Test | Result |
|:-:|------|:------:|
| ① | Backdate claim date | |
| ② | Re-edit fields after save | |
| ③ | Revisit section always visible | |
| ④ | Document preview (Admin) | |
| ⑤ | Conversation order | |
| ⑥ | Refresh button | |
| ⑦ | New message notification | |
| ⑧ | Forward → forwarded section | |
| ⑨ | "Returned by Tech" badge | |
| ⑩ | Private notes (Tech view) | |
| ⑪ | Admin replies (Tech view) | |
| ⑫ | Document preview (Tech) | |
| ⑬ | Forward from Tech | |

**Total:** ___ / 13 passed

---

> 📱 **When done** → Tell me which tests **PASSED ✅** and which **FAILED ❌**  
> I'll immediately fix the failed ones.
