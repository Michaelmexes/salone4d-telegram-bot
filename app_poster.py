"""
==========================================
SALONE 4D - App Download Link Poster
==========================================
User အသစ်များအတွက် Salone4D Application ဒေါင်းလုဒ် Link ကို
သတ်မှတ်ထားသည့် အချိန်ကာလ (၂ ရက်လျှင် ၁ ကြိမ်၊ မနက် ၁၀:၃၀) တွင်
Telegram Channel (@salone4d) သို့ အလိုအလျောက် Post တင်ပေးသော Module
"""

import os
import logging
from datetime import datetime, date
import config
import bot

logger = logging.getLogger(__name__)

LAST_POSTED_APP_FILE = getattr(config, "LAST_POSTED_APP_FILE", "data/last_posted_app_download.txt")


def build_app_download_post() -> str:
    """Option 2 - တိုတိုရှင်းရှင်း ပုံစံဖြင့် App Download Link Post စာသား ဖန်တီးသည်"""
    bot_name = getattr(config, "BOT_USERNAME", "@Salone4dOfficialBot")
    signature = getattr(config, "CHANNEL_SIGNATURE", "@Salone4dOfficial")
    app_link = getattr(config, "APP_LINK", "https://t.ly/pemBm")
    support_phone = getattr(config, "SUPPORT_PHONE", "+95 9 894 169 717")

    post = (
        "🎯 SALONE4D APPLICATION ဒေါင်းလုဒ် 🎯\n"
        "───────────────────────\n\n"
        "မိတ်ဆွေသစ်များအတွက် Salone4D Application ဒေါင်းလုဒ် Link လေး မျှဝေပေးလိုက်ပါတယ်ခင်ဗျာ 📲✨\n\n"
        "🔗 App Download Link:\n"
        f"👉 {app_link}\n"
        "🌐 Website: www.salone4d.com\n\n"
        "✨ App ထဲမှာ KBZPay, WaveMoney ဖြင့် အလွယ်တကူ ငွေသွင်း/ငွေထုတ် ပြုလုပ်ပြီး 4D ထီများကို စိတ်ချယုံကြည်စွာ ထိုးယူနိုင်ပါပြီ။\n\n"
        f"💬 သိလိုသည်များရှိပါက Customer Care Bot ({bot_name}) နှင့် Viber ({support_phone}) တွင် မေးမြန်းနိုင်ပါသည်။\n\n"
        "🍀 ကံထူးရှင်များ ဖြစ်ကြပါစေ! 🍀\n"
        f"{signature}"
    )
    return post


def get_last_posted_app_date() -> str:
    """နောက်ဆုံး Post တင်ခဲ့သော ရက်စွဲ (YYYY-MM-DD) ကို ဖတ်သည်"""
    if os.path.exists(LAST_POSTED_APP_FILE):
        try:
            with open(LAST_POSTED_APP_FILE, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception as e:
            logger.warning(f"Error reading {LAST_POSTED_APP_FILE}: {e}")
    return ""


def set_last_posted_app_date(date_str: str):
    """Post တင်ပြီးသော ရက်စွဲကို ဖိုင်ထဲတွင် သိမ်းဆည်းသည်"""
    try:
        os.makedirs(os.path.dirname(LAST_POSTED_APP_FILE) or "data", exist_ok=True)
        with open(LAST_POSTED_APP_FILE, "w", encoding="utf-8") as f:
            f.write(date_str.strip())
    except Exception as e:
        logger.warning(f"Error saving {LAST_POSTED_APP_FILE}: {e}")


def should_post_app_download() -> bool:
    """
    နောက်ဆုံးတင်ခဲ့သည့် ရက်စွဲနှင့် လက်ရှိရက်စွဲကို နှိုင်းယှဉ်၍
    သတ်မှတ်ထားသည့် ကြားကာလ (၂ ရက်) ပြည့်/မပြည့် စစ်ဆေးသည်
    """
    last_date_str = get_last_posted_app_date()
    if not last_date_str:
        # ယခင်က တစ်ကြိမ်မျှ မတင်ရသေးပါက တင်ခွင့်ပြုသည်
        return True

    try:
        last_dt = datetime.strptime(last_date_str, "%Y-%m-%d").date()
        today = date.today()
        interval = getattr(config, "APP_POST_INTERVAL_DAYS", 2)
        diff_days = (today - last_dt).days
        return diff_days >= interval
    except Exception as e:
        logger.error(f"Error comparing dates in should_post_app_download: {e}")
        return True


def post_app_download_if_due(force: bool = False) -> bool:
    """
    ၂ ရက်လျှင် ၁ ကြိမ် သတ်မှတ်ချက်နှင့် ကိုက်ညီပါက Telegram သို့ Post တင်သည်
    force=True ဖြစ်ပါက ကြားကာလ မပြည့်သော်လည်း ချက်ချင်း စမ်းသပ် တင်ပေးသည်
    """
    today_str = date.today().strftime("%Y-%m-%d")

    if not force and not should_post_app_download():
        last_date = get_last_posted_app_date()
        logger.info(f"ℹ️ App download post is not due yet (Last posted: {last_date}).")
        return False

    message = build_app_download_post()
    logger.info("📲 Sending Salone4D App Download post to Telegram channel...")
    success = bot.send_message(message)
    if success:
        set_last_posted_app_date(today_str)
        logger.info(f"✅ App Download post published successfully to {config.CHANNEL_ID} for {today_str}!")
        return True
    else:
        logger.error("❌ Failed to send App Download post.")
        return False


if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("\n--- Preview of App Download Post ---")
    print(build_app_download_post())
    print("------------------------------------\n")
    print(f"Should post today? {should_post_app_download()}")
