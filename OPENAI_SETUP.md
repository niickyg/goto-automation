# OpenAI API Setup - Get $5 Free Credit

## Step 1: Create OpenAI Account (2 minutes)

1. Go to: **https://platform.openai.com/signup**
2. Sign up with Google/Microsoft or email
3. Verify your email
4. ✅ **You now have $5 in free credits!**

---

## Step 2: Create API Key (1 minute)

1. Go to: **https://platform.openai.com/api-keys**
2. Click **"Create new secret key"**
3. Name it: "CallWise Testing"
4. Click **"Create secret key"**
5. **COPY THE KEY** (starts with `sk-proj-...` or `sk-...`)
   - ⚠️ You can only see it once!
   - Save it somewhere safe

---

## Step 3: Add to CallWise (30 seconds)

```bash
cd /home/user0/goto-automation

# Edit the .env file
nano .env

# Change line 3 from:
OPENAI_API_KEY=test_key

# To (paste your key):
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxx

# Save: Ctrl+X, then Y, then Enter
```

---

## Step 4: Verify It Works (1 minute)

```bash
# Restart backend to pick up new key
docker compose restart backend

# Wait 10 seconds
sleep 10

# Test the API
curl -X POST http://localhost:8000/api/test-openai

# Should return: {"status": "success", "message": "OpenAI API is working"}
```

---

## ✅ You're Ready!

Your $5 free credit allows:
- **125 call transcriptions + AI analysis**
- **Weeks of testing**
- **Complete demo library**

Cost per call: $0.04
Your free credit: $5.00
**Calls you can test: 125 FREE!**

---

## 💰 Check Your Usage

Monitor your credits:
1. Go to: **https://platform.openai.com/usage**
2. See how much you've used
3. See how much credit remains

You'll see:
- Whisper API usage (transcription)
- GPT-4 API usage (analysis)
- Total spent
- Remaining credit

---

## 💳 After Free Credits Run Out

When you use all $5 (after ~125 calls):

**Option 1: Add $10**
- Gives you 250 more calls
- Good for continued testing

**Option 2: Add payment method**
- Only charged for what you use
- $0.04 per call
- Set spending limits to stay safe

**Option 3: Launch and make money first!**
- Get 1 paying customer ($49/month)
- That covers 1,225 calls worth of OpenAI costs
- You profit $45/month
- Use customer revenue to pay OpenAI

---

## 🛡️ Safety Tips

### Set Spending Limits

1. Go to: **https://platform.openai.com/account/limits**
2. Set **monthly budget**: $50 (or whatever you're comfortable with)
3. Get email alerts at 75% and 100%
4. Automatically stops at limit

### Monitor Usage Daily

Check your dashboard:
- Daily: https://platform.openai.com/usage
- Make sure costs align with testing
- ~$0.04 per call

### Cost Control

```bash
# If testing gets expensive, reduce quality:
# Use GPT-3.5 instead of GPT-4 (saves 90%)
# Use Whisper "base" instead of "large" (saves 50%)
# We can modify the code if needed
```

---

## 📊 Expected Costs

### Your Testing Phase
```
Week 1: 20 calls × $0.04 = $0.80
Week 2: 30 calls × $0.04 = $1.20
Week 3: 40 calls × $0.04 = $1.60
Week 4: 35 calls × $0.04 = $1.40
Total: $5.00 (FREE with credits!)
```

### First Customer
```
Month 1: 100 calls × $0.04 = $4.00
Revenue: $49.00
Profit: $45.00
ROI: 1,125% 🚀
```

### 10 Customers
```
Month: 1,000 calls × $0.04 = $40.00
Revenue: $490.00
Profit: $450.00
ROI: 1,125%
```

---

## ⚡ Quick Start Commands

```bash
# 1. Get API key from: https://platform.openai.com/api-keys

# 2. Add to CallWise:
cd /home/user0/goto-automation
nano .env
# Add your key to line 3

# 3. Restart:
docker compose restart backend

# 4. Test:
curl -X POST http://localhost:8000/api/test-openai

# 5. Generate demo calls:
python3 simulate_calls.py

# 6. Open dashboard:
firefox http://localhost:3000 &
```

---

## 🎉 You Have Everything You Need

- ✅ $5 free credit (125 calls)
- ✅ CallWise ready to run
- ✅ AI features configured
- ✅ Demo call generator
- ✅ Beautiful dashboard

**Total cost to test: $0.00**

**Ready to start?** Get your API key:
👉 **https://platform.openai.com/api-keys**
