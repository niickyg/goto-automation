# 🤖 Test CallWise AI Features - Complete Guide

## What You'll Test

- ✅ **Call Transcription** - AI converts calls to text
- ✅ **Sentiment Analysis** - Positive, negative, neutral detection
- ✅ **Action Item Extraction** - Automatically finds follow-up tasks
- ✅ **Urgency Detection** - Prioritizes important calls
- ✅ **Dashboard UI** - Beautiful React interface
- ✅ **Kanban Board** - Manage action items visually

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Set Up OpenAI API Key

You need an OpenAI key for AI features to work:

1. Go to: https://platform.openai.com/api-keys
2. Sign up / Log in
3. Click "Create new secret key"
4. Copy the key (starts with `sk-...`)

**Add it to your .env file:**
```bash
cd /home/user0/goto-automation

# Edit .env file
nano .env
# Change: OPENAI_API_KEY=test_key
# To: OPENAI_API_KEY=sk-your-actual-key-here
```

Or set it directly:
```bash
export OPENAI_API_KEY=sk-your-actual-key-here
```

---

### Step 2: Start CallWise Product

```bash
cd /home/user0/goto-automation

# Start all services (database, backend, frontend)
docker compose up -d

# Wait 30 seconds for everything to start
sleep 30

# Check status
docker compose ps
```

**Expected Output:**
```
goto-automation-db        running   5432/tcp
goto-automation-redis     running   6379/tcp
goto-automation-api       running   8000/tcp
goto-automation-frontend  running   3000/tcp
```

---

### Step 3: Generate Test Calls with AI Analysis

```bash
# Run the call simulator (creates 50 realistic calls)
python3 simulate_calls.py

# This will:
# - Create 50 different call scenarios
# - Run AI transcription on each
# - Extract sentiment (positive/negative/neutral)
# - Find action items automatically
# - Calculate urgency scores
# - Populate your dashboard with data
```

**Expected Output:**
```
Creating 50 test calls...
✓ Call 1: Password Reset (negative sentiment)
✓ Call 2: Product Demo Request (positive sentiment)
✓ Call 3: Technical Issue (negative sentiment)
...
✓ All 50 calls created with AI analysis!
```

---

### Step 4: View the Dashboard

**Open in your browser:**
```
http://localhost:3000
```

Or **on your phone** (same WiFi):
```
http://192.168.5.6:3000
```

You'll see:
- 📊 **Dashboard** with call statistics
- 📞 **Call List** with AI transcriptions
- 😊 **Sentiment Analysis** (positive/negative/neutral badges)
- ✅ **Action Items** extracted by AI
- 🎯 **Kanban Board** to manage follow-ups
- ⚡ **Urgency Indicators** (1-5 scale)

---

## 🧪 Testing Checklist

### Test 1: View Call Transcriptions

1. Open dashboard: http://localhost:3000
2. Click on any call
3. See full AI-generated transcript
4. Verify it reads naturally

**What to look for:**
- ✅ Transcript is readable
- ✅ Proper punctuation
- ✅ Names capitalized correctly
- ✅ Technical terms spelled correctly

---

### Test 2: Check Sentiment Analysis

1. Look at call list
2. Each call has a sentiment badge:
   - 😊 Green = Positive
   - 😐 Yellow = Neutral
   - 😠 Red = Negative

3. Click on a negative call
4. Verify the content matches the sentiment

**Examples:**
- "I love your product!" → Positive
- "This is frustrating" → Negative
- "I have a question" → Neutral

---

### Test 3: Review Action Items

1. Open any call detail
2. Scroll to "Action Items" section
3. See AI-extracted tasks

**Example call:**
```
Customer: "I need a password reset and please follow up next week"

AI Extracted Action Items:
✓ Send password reset link
✓ Schedule follow-up call for next week
```

---

### Test 4: Test Kanban Board

1. Click "Kanban" in navigation
2. See action items organized in columns:
   - 📝 **To Do**
   - ⏳ **In Progress**
   - ✅ **Done**

3. Drag and drop items between columns
4. Mark items as complete

---

### Test 5: Test Urgency Prioritization

1. Sort calls by urgency
2. High urgency (4-5) appears first
3. Click on urgent call
4. Verify it needs immediate attention

**Urgency Examples:**
- 5: Enterprise deal, major bug
- 4: Customer can't access account
- 3: Feature request, upgrade inquiry
- 2: General question
- 1: Informational call

---

### Test 6: Search & Filter

1. Use search box
2. Search for keywords: "password", "demo", "bug"
3. Filter by sentiment
4. Filter by date range
5. Verify results are accurate

---

### Test 7: Mobile Experience

**On your phone**, visit: http://192.168.5.6:3000

Test:
- [ ] Dashboard loads properly
- [ ] Call list is readable
- [ ] Can click on calls to view details
- [ ] Sentiment badges visible
- [ ] Action items displayed
- [ ] Kanban board works (drag & drop)

---

## 📊 What the AI Does

### 1. Call Transcription (OpenAI Whisper)
- Converts audio → text
- Handles accents and background noise
- Punctuation and capitalization
- Speaker identification

### 2. Sentiment Analysis (GPT-4)
- Analyzes tone and language
- Classifies: Positive, Negative, Neutral
- Confidence scores
- Context-aware (understands sarcasm)

### 3. Action Item Extraction (GPT-4)
- Scans transcript for tasks
- Identifies:
  - Follow-up calls needed
  - Documents to send
  - Issues to escalate
  - Meetings to schedule
- Formats as actionable tasks

### 4. Urgency Detection
- Analyzes sentiment + keywords
- Scores 1-5 (low to high)
- Considers:
  - Customer emotion
  - Topic (billing > question)
  - Language ("urgent", "asap")

---

## 🎯 Demo Scenarios

### Scenario 1: Support Call Gone Wrong
1. Find a negative sentiment call
2. Open call details
3. See AI detected frustration
4. Review extracted action items
5. Move to "In Progress" in Kanban

### Scenario 2: Sales Opportunity
1. Filter for positive sentiment
2. Find "Product Demo Request"
3. See high urgency (3-4)
4. Check action items: "Schedule demo"
5. Mark as important

### Scenario 3: Bug Report
1. Search for "bug" or "crash"
2. Should be negative sentiment
3. High urgency (4-5)
4. Action items include: "Escalate to engineering"
5. Track resolution in Kanban

---

## 🔍 API Endpoints to Test

### Get All Calls
```bash
curl http://localhost:8000/api/calls
```

### Get Call by ID
```bash
curl http://localhost:8000/api/calls/1
```

### Get Action Items
```bash
curl http://localhost:8000/api/action-items
```

### Get Statistics
```bash
curl http://localhost:8000/api/stats
```

---

## 💰 Revenue Features to Test

### Billing Integration (Stripe)

1. Navigate to Settings → Billing
2. See pricing tiers:
   - Starter: $49/month
   - Professional: $99/month
   - Business: $199/month

3. Click "Upgrade" (test mode)
4. Stripe checkout should open

**Note**: You need to set Stripe keys in .env for this to work fully.

---

## 📱 Test on Your Phone

**WiFi Connection Required**

1. Connect phone to same WiFi as computer
2. Open browser on phone
3. Visit: http://192.168.5.6:3000
4. Test all features:
   - Dashboard navigation
   - Call details
   - Sentiment indicators
   - Action items
   - Kanban drag & drop (may be limited on mobile)

---

## 🐛 Troubleshooting

### Issue: "OPENAI_API_KEY not set"

**Fix:**
```bash
cd /home/user0/goto-automation
nano .env
# Add: OPENAI_API_KEY=sk-your-key-here
docker compose restart backend
```

### Issue: No calls appearing

**Fix:**
```bash
# Re-run simulator
python3 simulate_calls.py

# Or check logs
docker logs goto-automation-api
```

### Issue: Frontend not loading

**Fix:**
```bash
# Rebuild frontend
docker compose down
docker compose up -d --build
```

### Issue: AI analysis not working

**Check:**
1. OpenAI API key is valid
2. You have credits in OpenAI account
3. Backend logs show no errors:
   ```bash
   docker logs goto-automation-api --tail 50
   ```

---

## 📊 Sample AI Output

**Example Call:**
```
Customer: "Hi, I've been trying to log in for the past hour and it keeps
saying my password is wrong. I know I'm using the right one. This is
really frustrating because I have an important meeting in 10 minutes."

AI Analysis:
├─ Sentiment: NEGATIVE (confidence: 92%)
├─ Urgency: 4 (High)
├─ Topic: Account Access Issue
└─ Action Items:
   1. Reset password immediately
   2. Verify account status
   3. Follow up before customer's meeting
   4. Investigate login system issues
```

---

## ✅ Success Criteria

After testing, you should see:

- ✅ 50+ calls in dashboard
- ✅ All calls have AI transcripts
- ✅ Sentiment badges on all calls
- ✅ Action items extracted automatically
- ✅ Urgency scores assigned
- ✅ Kanban board populated
- ✅ Search/filter working
- ✅ Mobile interface responsive
- ✅ No console errors
- ✅ API endpoints responding

---

## 🎉 Next Steps

Once testing is complete:

1. **Show to potential customers**
   - Use demo data to showcase AI features
   - Highlight time saved (manual vs AI)
   - Show ROI calculation

2. **Create demo video**
   - Screen record the dashboard
   - Show AI analyzing calls in real-time
   - Demonstrate Kanban workflow

3. **Deploy to production**
   - Use DigitalOcean App Platform ($24/mo)
   - Or Railway ($10-20/mo)
   - Connect real GoTo API

4. **Start selling**
   - Email waitlist with demo link
   - Offer early access pricing
   - Target: 10 customers × $99 = $990 MRR

---

## 🚀 Quick Commands

```bash
# Start everything
cd /home/user0/goto-automation && docker compose up -d

# Generate test calls
python3 simulate_calls.py

# View logs
docker logs goto-automation-api -f

# Stop everything
docker compose down

# Rebuild after changes
docker compose up -d --build

# Check API health
curl http://localhost:8000/health

# View calls
curl http://localhost:8000/api/calls | jq
```

---

## 💡 What Makes This Valuable

**Time Savings:**
- Manual call review: 10 min/call
- AI analysis: 30 seconds/call
- **Savings**: 95% faster

**Value Per Customer:**
- 100 calls/month × 10 min = 1,000 minutes saved
- = 16.7 hours saved
- At $50/hour = **$835/month in time saved**
- Your price: $49-199/month
- **ROI**: 4-17x

**This is why customers will pay!**

---

**Ready to test?**

```bash
cd /home/user0/goto-automation
docker compose up -d
sleep 30
python3 simulate_calls.py
firefox http://localhost:3000 &
```

Your AI-powered CallWise dashboard will open with 50 analyzed calls! 🚀
