import os

# Auto-load environment variables from .env file if present
def _load_dotenv():
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_file):
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k and k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass

_load_dotenv()

# ==========================================
# SALONE 4D - Configuration File
# ==========================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "")                  # Telegram Bot token (from .env or environment)

# ==========================================
# Telegram Channel Configuration (Environment)
# ==========================================
# Production သို့မဟုတ် Staging ပြောင်းရန် ဤနေရာတွင် 'production' (သို့) 'staging' ရွေးပါ:
# - "production" => @Salone4dOfficial
# - "staging"    => @mexes30salone
ENVIRONMENT = os.getenv("ENVIRONMENT", "production").lower().strip()

CHANNELS = {
    "production": "@Salone4dOfficial",
    "staging": "@mexes30salone",
}

# လက်ရှိ အသုံးပြုမည့် Channel ID
# ENVIRONMENT သတ်မှတ်ထားပါက ၎င်းအတိုင်း တိုက်ရိုက်ယူမည်
if os.getenv("ENVIRONMENT"):
    CHANNEL_ID = CHANNELS.get(os.getenv("ENVIRONMENT").lower().strip(), "@Salone4dOfficial")
elif os.getenv("CHANNEL_ID"):
    CHANNEL_ID = os.getenv("CHANNEL_ID").strip()
else:
    CHANNEL_ID = CHANNELS.get(ENVIRONMENT, "@Salone4dOfficial")

# Format channel handle
if not CHANNEL_ID.startswith("@"):
    CHANNEL_ID = f"@{CHANNEL_ID}"

TELEGRAM_CHANNEL = CHANNEL_ID

# Web Service Port for Render / Cloud hosting
PORT = int(os.getenv("PORT", "10000"))

# ==========================================
# OpenRouter & AI Customer Service Settings
# ==========================================
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")  # OpenRouter API Key (from .env or environment)

OPENROUTER_MODELS = [
    "qwen/qwen3.8-27b:free",
    "google/gemma-4-31b-it:free",
    "google/gemma-4-26b-a4b-it:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "openrouter/free"
]

# Support Contacts & Info
COMPANY_NAME_EN = "Salone4D Lottery Service"
COMPANY_NAME_MY = "Salone4D ထီဝန်ဆောင်မှု"
SUPPORT_PHONE = "+95 9 894 169 717"
SUPPORT_VIBER = "+95 9 894 169 717"
APP_LINK = "https://t.ly/pemBm"
TELEGRAM_CHANNEL = os.getenv("TELEGRAM_CHANNEL", "@mexes30salone")
ADMIN_TELEGRAM = "@salone4DAdmin"

# AI Assistant System Prompt
AI_SYSTEM_PROMPT = (
    "You are the official Customer Service AI Assistant for Salone4D Lottery Service.\n"
    "Bot Structure & FAQs:\n"
    "  1. 4D App လေးသွင်းပါ (Link: https://t.ly/pemBm or www.salone4d.com)\n"
    "  2. 4D App သုံးနည်း:\n"
    "     2.1 Register / Login ဝင်နည်း: အကောင့်လုပ်မည် သို့သွားပြီး နာမည်၊ ဖုန်း၊ password ဖြည့်သွင်း၍ ဖွင့်ပါ။\n"
    "     2.2 4D ထိုးနည်း: App ရှိ 'Buy' ကိုနှိပ်ပါ၊ ရက်စွဲနှင့် အမျိုးအစား (4D/Sweep) ရွေးချယ်ပြီး မိမိကြိုက်သောဂဏန်းများရွေးပါ။\n"
    "     2.3 ငွေသွင်း/ငွေထုတ်နည်း: 'Cash' > 'ငွေသွင်း'/'ငွေထုတ်' သို့သွားပါ။ KBZPay, WaveMoney ဖြင့် အနည်းဆုံး ကျပ် ၁,၀၀၀ သွင်း/ထုတ်နိုင်ပါသည်။\n"
    "     2.4 ထိုးထားတာပြန်စစ်နည်း: 'Record' သို့မဟုတ် 'History' မီနူးတွင် ထိုးထားသည့်လက်မှတ်များကို ပြန်လည်စစ်ဆေးနိုင်ပါသည်။\n"
    "  3. ဆက်သွယ်ရန် / Viber: +95 9 894 169 717 (https://viber.click/959894169717)\n"
    "Rules:\n"
    "  - အရေးကြီးသည်: အမြဲတမ်း သဘာဝကျပြီး ယဉ်ကျေးပျူငှာသော မြန်မာဘာသာစကားဖြင့်သာ ဖြေကြားပေးရပါမည်။ အင်္ဂလိပ်လို လုံးဝမဖြေရပါ။ (STRICT: Reply ONLY in Burmese/Myanmar language. Never output English).\n"
    "  - Keep answers brief, friendly, and helpful in Burmese.\n"
    "  - Do NOT output chain of thought, reasoning, or internal thoughts. Output only the final response for the user in Burmese."
)

# ==========================================
# Scraper Settings
# ==========================================
SCRAPE_FROM_YEAR = 2023                 # Data စတင်ဆွဲမည့် နှစ်
DATA_FILE = "data/4d_results.csv"       # Data သိမ်းမည့် file path

# ==========================================
# Hot Number Settings
# ==========================================
TOP_N = 5                               # ထုတ်ပေးမည့် hot number အရေအတွက်

# ==========================================
# Scheduler Settings
# ==========================================

# ၁။ Hot Numbers Schedule (ထီဂဏန်း ခန့်မှန်းချက် တင်မည့်အချိန်)
# နေ့တိုင်း မနက် (၁၀:၀၀) နာရီတွင် အလိုအလျောက် Post တင်မည် (Render: HOT_POST_TIME သို့မဟုတ် POST_TIME)
HOT_POST_TIME = os.getenv("HOT_POST_TIME", os.getenv("POST_TIME", "10:00"))
POST_TIME = HOT_POST_TIME               # Backwards compatibility
POST_ON_DRAW_DAYS_ONLY = False          # True = ဆွဲတဲ့နေ့တွေမှာပဲ post / False = နေ့တိုင်း post

# ၂။ Official Draw Result Schedule (ထီပေါက်စဉ် စစ်ဆေးပြီး တင်မည့်အချိန်)
# Singapore Pools 4D ပေါက်စဉ်သည် Wed, Sat, Sun ညနေ ၅:၄၅ မှ ၇:၀၀ အတွင်း အသစ်ထွက်လာသည်နှင့် တင်ပေးသည်
RESULT_POST_START_TIME = os.getenv("RESULT_POST_START_TIME", os.getenv("RESULT_CHECK_START_TIME", "17:45"))
RESULT_CHECK_START_TIME = RESULT_POST_START_TIME       # စတင်စစ်ဆေးမည့်အချိန် (မြန်မာစံတော်ချိန် ညနေ ၅:၄၅ PM)
RESULT_CHECK_END_TIME   = os.getenv("RESULT_CHECK_END_TIME", "19:00")  # နောက်ဆုံးစစ်ဆေးမည့်အချိန် (ညနေ ၇:၀၀ PM)
RESULT_CHECK_INTERVAL_MINS = int(os.getenv("RESULT_CHECK_INTERVAL_MINS", "2"))  # ၂ မိနစ်တစ်ကြိမ် စစ်ဆေးမည်

# ==========================================
# Myanmar Locale
# ==========================================
MYANMAR_DIGITS = {
    '0': '၀', '1': '၁', '2': '၂', '3': '၃', '4': '၄',
    '5': '၅', '6': '၆', '7': '၇', '8': '၈', '9': '၉'
}

MYANMAR_DAYS = {
    'Monday':    'တနင်္လာနေ့',
    'Tuesday':   'အင်္ဂါနေ့',
    'Wednesday': 'ဗုဒ္ဓဟူးနေ့',
    'Thursday':  'ကြာသပတေးနေ့',
    'Friday':    'သောကြာနေ့',
    'Saturday':  'စနေနေ့',
    'Sunday':    'တနင်္ဂနွေနေ့'
}

MYANMAR_MONTHS = {
    1:  'ဇန်နဝါရီ',
    2:  'ဖေဖော်ဝါရီ',
    3:  'မတ်',
    4:  'ဧပြီ',
    5:  'မေ',
    6:  'ဇွန်',
    7:  'ဇူလိုင်',
    8:  'သြဂုတ်',
    9:  'စက်တင်ဘာ',
    10: 'အောက်တိုဘာ',
    11: 'နိုဝင်ဘာ',
    12: 'ဒီဇင်ဘာ'
}
