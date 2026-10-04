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
CHANNEL_ID = os.getenv("CHANNEL_ID", "@mexes30salone")  # Target Telegram Channel

# Web Service Port for Render / Cloud hosting
PORT = int(os.getenv("PORT", "10000"))

# ==========================================
# OpenRouter & AI Customer Service Settings
# ==========================================
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")  # OpenRouter API Key (from .env or environment)

OPENROUTER_MODELS = [
    "deepseek/deepseek-v4-flash",
    "deepseek/deepseek-v4.1-flash",
    "deepseek/deepseek-chat",
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
    "     2.4 ထိုးထားတာပြန်စစ်နည်း: 'Record' သို့မဟုတ် 'History' မနူးတွင် ထိုးထားသည့်လက်မှတ်များကို ပြန်လည်စစ်ဆေးနိုင်ပါသည်။\n"
    "  3. ဆက်သွယ်ရန် / Viber: +95 9 894 169 717 (https://viber.click/959894169717)\n"
    "Rules:\n"
    "  - Always reply politely and naturally in Burmese language.\n"
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
# နေ့တိုင်း Hot numbers post လုပ်မည့် အချိန် (24hr format)
POST_TIME = "18:00"                     # နေ့တိုင်း post လုပ်မည့် အချိန် (HH:MM)
POST_ON_DRAW_DAYS_ONLY = False          # True = ဆွဲတဲ့နေ့တွေမှာပဲ post / False = နေ့တိုင်း post

# Wed, Sat, Sun များတွင် 4D Result အသစ် စတင်စစ်ဆေးမည့် အချိန်သတ်မှတ်ချက် (မြန်မာစံတော်ချိန်)
# 5:45 PM မှ စတင်စစ်ဆေးမည်
RESULT_CHECK_START_TIME = "17:45"       # မြန်မာစံတော်ချိန် ညနေ ၅:၄၅ PM
RESULT_CHECK_END_TIME   = "19:00"       # ညနေ ၇:၀၀ PM အထိ မထွက်သေးပါက စစ်ဆေးမည်
RESULT_CHECK_INTERVAL_MINS = 2          # ၂ မိနစ်တစ်ကြိမ် စစ်ဆေးမည်

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
