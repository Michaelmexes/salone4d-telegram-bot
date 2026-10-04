# 🎯 SALONE 4D — Telegram Auto Post System

Singapore Pools 4D historical data ကိုအခြေခံပြီး Hot Numbers ထုတ်ကာ
Telegram channel မှာ auto post လုပ်ပေးတဲ့ system။

---

## 📁 File Structure

```
Salone4dTelegramPost/
├── app.py               ← 🚀  Unified Runner for Render (Web Health + Bot + Scheduler)
├── render.yaml          ← 🌐  Render Blueprint configuration
├── config.py            ← ⚙️  Token, OpenRouter & Settings
├── customer_bot.py      ← 💬  24/7 Customer Service Bot (DeepSeek AI Auto-Reply)
├── memory_manager.py    ← 🧠  Multi-turn Conversation Memory manager
├── openrouter_client.py ← 🤖  OpenRouter AI Client (DeepSeek V4 Flash)
├── keyboards.py         ← 🔘  Inline keyboard menu builder
├── texts/               ← 🇲🇲  Burmese & English menu texts
├── scraper.py           ← 🕷️  Singapore Pools data scraper
├── analyzer.py          ← 📊  Hot number analyzer
├── formatter.py         ← ✍️  Post format builder
├── bot.py               ← 🤖  Telegram channel sender
├── main.py              ← ▶️  Main pipeline runner
├── scheduler.py         ← ⏰  Auto daily scheduler
├── requirements.txt     ← 📦  Python libraries
└── data/
    ├── 4d_results.csv   ← Historical data
    └── salone4d.log     ← Logs
```

---

## 🚀 Setup (ပထမဆုံး Run နည်း)

### Step 1 — Libraries install လုပ်ပါ
```bash
pip install -r requirements.txt
```

### Step 2 — config.py မှာ Token ထည့်ပါ
```python
BOT_TOKEN  = "1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ"
CHANNEL_ID = "@Salone4D_Official"   # သို့မဟုတ် -1001234567890
```

### Step 3 — Bot test လုပ်ပါ
```bash
python bot.py
```

### Step 4 — Post format preview ကြည့်ပါ
```bash
python main.py --test
```

### Step 5 — Data ဆွဲပြီး channel မှာ post လုပ်ပါ
```bash
python main.py
```

### Step 6 — နေ့တိုင်း auto post (scheduler)
```bash
python scheduler.py
```

---

## ⏰ Schedule Settings (config.py)

| Setting | Default | ရှင်းလင်းချက် |
|---|---|---|
| `POST_TIME` | `"18:00"` | Post လုပ်မည့် အချိန် |
| `POST_ON_DRAW_DAYS_ONLY` | `False` | `True` = Wed/Sat/Sun မှာပဲ post |

---

## 🧪 Commands

```bash
# Customer Service Auto-Reply Bot (OpenRouter AI with Multi-turn Memory)
python customer_bot.py
# (Commands: /start, /applink, /appguide, /support, /reset, /help)

# Test mode (Telegram post မလုပ်ဘဲ preview ကြည့်)
python main.py --test

# Data ဆွဲပြီး channel မှာ post ချက်ချင်း
python main.py

# Scheduler ကို ချက်ချင်း trigger (test)
python scheduler.py --now

# Scheduler background run
python scheduler.py
```

---

## 📮 Post Format Preview

```
╔══════════════════════╗
║  🎯  SALONE 4D  🎯   ║
╚══════════════════════╝
📅 သောကြာနေ့ │ ၀၂ အောက်တိုဘာ ၂၀၂၆

💥 ကံကောင်းဂဏန်းများ 💥
──────────────────────

🥇 ၄ ─ ၈ ─ ၂ ─ ၃  │ (၄၅ ကြိမ်ပေါ်)
🥈 ၇ ─ ၁ ─ ၅ ─ ၆  │ (၄၂ ကြိမ်ပေါ်)
🥉 ၃ ─ ၀ ─ ၉ ─ ၁  │ (၃၉ ကြိမ်ပေါ်)
4️⃣ ၆ ─ ၇ ─ ၄ ─ ၈  │ (၃၇ ကြိမ်ပေါ်)
5️⃣ ၂ ─ ၃ ─ ၆ ─ ၅  │ (၃၅ ကြိမ်ပေါ်)

──────────────────────
Base on Singapore Pools 4D
📈 2023 ─ 2026 Data အပေါ် အခြေခံ၍
🍀 ကံကောင်းပါစေ! 🍀
@mexes30salone
```

---

## ☁️ Deploy to Render (Render.com တွင် Run နည်း)

### ၁။ GitHub သို့ Code တင်ခြင်း (Push to GitHub)
```bash
git add .
git commit -m "Initial commit for Render deployment"
git branch -M main
git remote add origin https://github.com/<YOUR_USERNAME>/<YOUR_REPO>.git
git push -u origin main
```

### ၂။ Render.com တွင် Web Service ပြုလုပ်ခြင်း
1. [Render.com](https://render.com) တွင် Login ဝင်ပြီး **New +** > **Web Service** ကို ရွေးပါ။
2. မိမိ၏ GitHub Repository ကို ချိတ်ဆက်ပါ (Connect Repository)။
3. အောက်ပါ အချက်များကို ဖြည့်သွင်းပါ:
   - **Name:** `salone4d-bot`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python app.py`
   - **Instance Type:** `Free`

### ၃။ Environment Variables သတ်မှတ်ခြင်း (Render Dashboard > Environment)
| Variable | Value |
|---|---|
| `CHANNEL_ID` | `@mexes30salone` |
| `BOT_TOKEN` | `<YOUR_TELEGRAM_BOT_TOKEN>` |
| `OPENROUTER_API_KEY` | `<YOUR_OPENROUTER_API_KEY>` |
| `RUN_MODE` | `all` (Auto-poster + Customer Bot နှစ်ခုလုံး run မည်) |

> `app.py` သည် Render ၏ Web Health Check ($PORT) ကို အလိုအလျောက် ဖြေကြားပေးပြီး Channel Auto-Poster နှင့် Customer Bot နှစ်ခုလုံးကို တစ်ပြိုင်နက်တည်း 24/7 Run ပေးထားမည် ဖြစ်ပါသည်။

