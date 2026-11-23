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
# - "production" => @salone4d
# - "staging"    => @mexes30salone
ENVIRONMENT = os.getenv("ENVIRONMENT", "production").lower().strip()

CHANNELS = {
    "production": "@salone4d",
    "staging": "@mexes30salone",
}

SIGNATURES = {
    "production": "@salone4d",
    "staging": "@mexes30salone",
}

# လက်ရှိ အသုံးပြုမည့် Channel ID
# ENVIRONMENT သတ်မှတ်ထားပါက ၎င်းအတိုင်း တိုက်ရိုက်ယူမည်
if os.getenv("ENVIRONMENT"):
    CHANNEL_ID = CHANNELS.get(os.getenv("ENVIRONMENT").lower().strip(), "@salone4d")
elif os.getenv("CHANNEL_ID"):
    CHANNEL_ID = os.getenv("CHANNEL_ID").strip()
else:
    CHANNEL_ID = CHANNELS.get(ENVIRONMENT, "@salone4d")

# Format channel handle
if not CHANNEL_ID.startswith("@"):
    CHANNEL_ID = f"@{CHANNEL_ID}"

TELEGRAM_CHANNEL = CHANNEL_ID

# Post Footer တွင် ဖော်ပြမည့် Signature (production တွင် @salone4d / staging တွင် @mexes30salone)
CHANNEL_SIGNATURE = SIGNATURES.get(os.getenv("ENVIRONMENT", ENVIRONMENT).lower().strip(), "@salone4d")

# Web Service Port for Render / Cloud hosting
PORT = int(os.getenv("PORT", "10000"))

# ==========================================
# OpenRouter & AI Customer Service Settings
# ==========================================
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")  # OpenRouter API Key (from .env or environment)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))

OPENROUTER_MODELS = [
    "openrouter/free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "nvidia/nemotron-3.5-lightning:free",
    "mistralai/mistral-7b-instruct:free",
    "deepseek/deepseek-r1:free",
    "qwen/qwen-2.5-72b-instruct:free",
]

# Support Contacts & Info
COMPANY_NAME_EN = "Salone4D Lottery Service"
COMPANY_NAME_MY = "Salone4D ထီဝန်ဆောင်မှု"
BOT_USERNAME = os.getenv("BOT_USERNAME", "@Salone4dOfficialBot")
SUPPORT_PHONE = "+95 9 894 169 717"
SUPPORT_VIBER = "+95 9 894 169 717"
APP_LINK = "https://t.ly/pemBm"
TELEGRAM_CHANNEL = CHANNEL_ID
ADMIN_TELEGRAM = "@salone4DAdmin"

# Human Handover Configuration
HANDOVER_MESSAGE = (
    "ဟုတ်ကဲ့ခင်ဗျာ၊ ခေတ္တစောင့်ဆိုင်းပေးပါရှင်/ခင်ဗျာ။ "
    "လူကြီးမင်းအား အသေးစိတ် ကူညီဖြေကြားပေးနိုင်ရန် တာဝန်ကျ ဆိုင်ဝန်ထမ်း (Human Agent) "
    "ထံသို့ အကြောင်းကြား လွှဲပြောင်းပေးထားပါပြီခင်ဗျာ။ 👨‍💼"
)

HANDOVER_KEYWORDS = [
    "လူနဲ့ ပြောချင်တယ်", "လူနဲ့ပြောချင်", "လူနဲ့ပြော", "လူနဲ့စကားပြော",
    "agent ခေါ်ပေးပါ", "agent နဲ့", "agent ခေါ်", "agent",
    "ဝန်ထမ်းနဲ့ တွေ့ချင်တယ်", "ဝန်ထမ်းနဲ့", "ဝန်ထမ်းခေါ်", "ဝန်ထမ်း",
    "အကူအညီလိုတယ်", "အကူအညီပေးပါ", "အကူအညီ", "ပြဿနာတက်",
    "စလစ်", "ငွေမဝင်", "ငွေမရောက်", "လိမ်တယ်", "လိမ်", "human", "admin"
]

# ==========================================
# ChateChat Auto-Responder Bot Settings
# ==========================================
CHATECHAT_BOT_TOKEN = os.getenv("CHATECHAT_BOT_TOKEN", "")
if not CHATECHAT_BOT_TOKEN:
    _tf = os.path.join(os.path.dirname(__file__), "data", "chatechat_token.txt")
    if os.path.exists(_tf):
        try:
            with open(_tf, "r", encoding="utf-8") as _f:
                CHATECHAT_BOT_TOKEN = _f.read().strip()
        except Exception:
            pass
CHATECHAT_BOT_USERNAME = os.getenv("CHATECHAT_BOT_USERNAME", "@chatechatbot")
CHATECHAT_APK_URL = os.getenv("CHATECHAT_APK_URL", "https://tinyurl.com/chatechat-app")
CHATECHAT_WEBAPP_URL = os.getenv("CHATECHAT_WEBAPP_URL", "https://chatechat.onrender.com")
CHATECHAT_BOT_REPLY_URL = os.getenv("CHATECHAT_BOT_REPLY_URL", "https://chatechat.onrender.com/api/v1/webhooks/telegram/bot-reply")


CHATECHAT_AI_SYSTEM_PROMPT = (
    "You are the official simple Customer Care AI Assistant for ChateChat (online chat and messaging application).\n"
    "ChateChat Details:\n"
    "  - Android APK Download Link: https://tinyurl.com/chatechat-app\n"
    "  - Web App (Browser access): https://chatechat.onrender.com\n"
    "  - Supported devices: Android phones (via APK) and any browser on PC/Mobile (Web App).\n"
    "  - Free to use: ChateChat is 100% free to chat, call and message.\n"
    "  - Account: Users can easily sign up inside the App or Web App with their username/phone.\n"
    "Rules:\n"
    "  - STRICT: Answer ONLY in natural, polite Myanmar/Burmese language. Never reply in English.\n"
    "  - Keep answers VERY SHORT and simple (1 or 2 sentences only).\n"
    "  - ONLY answer simple questions related to ChateChat (downloading, web app, basic account usage).\n"
    "  - If the question is outside ChateChat or too complex, politely say that you only assist with ChateChat app and guide them to use the APK or Web App.\n"
    "  - Do NOT output chain of thought or internal reasoning. Output only the final response in Burmese."
)


# AI Assistant System Prompt
SALONE4D_AI_PREFIX = (
    "[Role & Purpose]\n"
    "သင်သည် [Salone4d] ၏ တရားဝင် Telegram Customer Service AI Agent ဖြစ်သည်။\n"
    "Customer များ မေးမြန်းသမျှကို ယဉ်ကျေးပျူငှာစွာနှင့် တိကျစွာ မြန်မာဘာသာ/ အင်္ဂလိပ်ဘာသာ ဖြင့် ကူညီဖြေကြားပေးရမည်။\n\n"
    "[Operation with Human Support Team]\n"
    "ဤ Bot သည် ChateChat Multi-Channel Live Chat စနစ်နှင့် တွဲဖက်အလုပ်လုပ်နေပါသည်။\n"
    "လူကိုယ်တိုင် တာဝန်ကျ Support Agent ဝန်ထမ်းများကလည်း Inbox ထဲတွင် အသင့်ရှိနေပါသည်။\n\n"
    "[Rules for Auto-Reply & Human Handover]\n"
    "၁။ အခြေခံမေးခွန်းများကို AI အနေဖြင့် ချက်ချင်း အလိုအလျောက် ဖြေကြားပေးပါ။\n"
    "၂။ User က အောက်ပါ အခြေအနေများ ပြုလုပ်လာပါက Bot ဘက်မှ ဆက်လက် မဖြေကြားဘဲ လူကိုယ်တိုင် ဝန်ထမ်းထံသို့ ချက်ချင်း လွှဲပြောင်းပေးပါ:\n"
    "   - 'လူနဲ့ ပြောချင်တယ်', 'Agent ခေါ်ပေးပါ', 'ဝန်ထမ်းနဲ့ တွေ့ချင်တယ်', 'အကူအညီလိုတယ်' ဟု ပြောလာသည့်အခါ\n"
    "   - ငွေလွှဲပြေစာ (စလစ်) ပို့လာသည့်အခါ သို့မဟုတ် ပြဿနာတက်၍ စိတ်ဆိုးဒေါသထွက်နေသည့်အခါ\n"
    "   - Bot မှ တိကျစွာ မဖြေရှင်းနိုင်သော ရှုပ်ထွေးသည့် ကိစ္စများ ဖြစ်သည့်အခါ\n"
    "၃။ လူထံသို့ လွှဲပြောင်းသည့်အခါ အောက်ပါအတိုင်း စာတစ်စောင်သာ အသိပေး ပြန်ကြားပါ:\n"
    "   'ဟုတ်ကဲ့ခင်ဗျာ၊ ခေတ္တစောင့်ဆိုင်းပေးပါရှင်/ခင်ဗျာ။ လူကြီးမင်းအား အသေးစိတ် ကူညီဖြေကြားပေးနိုင်ရန် တာဝန်ကျ ဆိုင်ဝန်ထမ်း (Human Agent) ထံသို့ အကြောင်းကြား လွှဲပြောင်းပေးထားပါပြီခင်ဗျာ။ 👨‍💼'\n\n"
)

AI_SYSTEM_PROMPT = SALONE4D_AI_PREFIX + (
    "Bot Structure & FAQs:\n"
    "  1. 4D App လေးသွင်းပါ (Link: https://t.ly/pemBm or www.salone4d.com)\n"
    "  2. 4D App သုံးနည်း:\n"
    "     2.1 Register / Login ဝင်နည်း: အကောင့်လုပ်မည် သို့သွားပြီး နာမည်၊ ဖုန်း၊ password ဖြည့်သွင်း၍ ဖွင့်ပါ။\n"
    "     2.2 4D ထိုးနည်း: App ရှိ 'Buy' ကိုနှိပ်ပါ၊ ရက်စွဲနှင့် အမျိုးအစား (4D/Sweep) ရွေးချယ်ပြီး မိမိကြိုက်သောဂဏန်းများရွေးပါ။\n"
    "     2.3 ငွေသွင်း/ငွေထုတ်နည်း: 'Cash' > 'ငွေသွင်း'/'ငွေထုတ်' သို့သွားပါ။ KBZPay, WaveMoney ဖြင့် အနည်းဆုံး ကျပ် ၁,၀၀၀ သွင်း/ထုတ်နိုင်ပါသည်။\n"
    "     2.4 ထိုးထားတာပြန်စစ်နည်း: 'Record' သို့မဟုတ် 'History' မီနူးတွင် ထိုးထားသည့်လက်မှတ်များကို ပြန်လည်စစ်ဆေးနိုင်ပါသည်။\n"
    "  3. ဆက်သွယ်ရန် / Viber: +95 9 894 169 717 (https://viber.click/959894169717) / Telegram: @salone4DAdmin\n"
    "Rules:\n"
    "  - အရေးကြီးသည်: အမြဲတမ်း သဘာဝကျပြီး ယဉ်ကျေးပျူငှာသော မြန်မာဘာသာစကားဖြင့်သာ ဖြေကြားပေးရပါမည်။ (User က အင်္ဂလိပ်လို မေးပါက အင်္ဂလိပ်လို ဖြေကြားနိုင်သည်)။\n"
    "  - Keep answers brief, friendly, and helpful.\n"
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

# ၃။ App Download Link Schedule (User အသစ်များအတွက် ၂ ရက် ၁ ကြိမ် မနက် ၁၀:၃၀ နာရီတွင် Post တင်မည့်အချိန်)
APP_POST_TIME = os.getenv("APP_POST_TIME", "10:30")
APP_POST_INTERVAL_DAYS = int(os.getenv("APP_POST_INTERVAL_DAYS", "2"))
LAST_POSTED_APP_FILE = "data/last_posted_app_download.txt"

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
