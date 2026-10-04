"""
==========================================
SALONE 4D - Master Scheduler
==========================================
၁။ နေ့တိုင်း ညနေ ၆:၀၀ တွင် Hot Numbers Post တင်ပေးခြင်း
၂။ ဗုဒ္ဓဟူး၊ စနေ၊ တနင်္ဂနွေ ညနေ ၅:၁၅ ~ ၅:၄၅ (မြန်မာစံတော်ချိန်) တွင် 
   Singapore Pools 4D Official Result ထွက်ထွက်ချင်း Auto Post တင်ပေးခြင်း
"""

import os
import sys
import time
import logging
import schedule
from datetime import datetime

# Windows console UTF-8 fix
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

os.makedirs('data', exist_ok=True)

import config
import main as hot_pipeline
import result_poster
import bot

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('data/scheduler.log', encoding='utf-8'),
    ]
)
logger = logging.getLogger(__name__)

DRAW_WEEKDAYS = {2, 5, 6}   # Wednesday, Saturday, Sunday
LAST_POSTED_DRAW_FILE = "data/last_posted_draw.txt"


def get_last_posted_draw() -> str:
    """နောက်ဆုံး Post တင်ပြီးသော Draw အမှတ်အသားကို ဖတ်သည်"""
    if os.path.exists(LAST_POSTED_DRAW_FILE):
        try:
            with open(LAST_POSTED_DRAW_FILE, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception:
            pass
    return ""


def set_last_posted_draw(draw_no_str: str):
    """Post တင်ပြီးသော Draw အမှတ်အသားကို မှတ်သားသည်"""
    try:
        with open(LAST_POSTED_DRAW_FILE, 'w', encoding='utf-8') as f:
            f.write(draw_no_str.strip())
    except Exception as e:
        logger.warning(f"Error saving last posted draw: {e}")


def is_within_result_check_window() -> bool:
    """လက်ရှိအချိန်သည် မြန်မာစံတော်ချိန် ညနေ ၅:၄၅ PM မှ ၇:၀၀ PM အတွင်း ဟုတ်မဟုတ် စစ်ဆေးသည်"""
    now = datetime.now()
    now_time_str = now.strftime("%H:%M")
    start_time = getattr(config, 'RESULT_CHECK_START_TIME', '17:45')
    end_time = getattr(config, 'RESULT_CHECK_END_TIME', '19:00')
    return start_time <= now_time_str <= end_time


def check_and_post_draw_result():
    """Singapore Pools Draw Result အသစ်ထွက်မထွက် စစ်ဆေးပြီး ထွက်ပါက Telegram သို့ ချက်ချင်း တင်သည်"""
    today_weekday = datetime.now().weekday()
    if today_weekday not in DRAW_WEEKDAYS:
        return

    # မြန်မာစံတော်ချိန် ညနေ ၅:၄၅ PM မတိုင်မီဆိုလျှင် မ run ပါ
    if not is_within_result_check_window():
        return

    logger.info("🔍 [5:45 PM+ Window] Checking Singapore Pools for new 4D official draw result...")
    result_data = result_poster.fetch_latest_result()
    if not result_data:
        return

    current_draw_no = result_data.get('draw_no_str', '')
    prizes = result_data.get('prizes', {})
    
    # 1st Prize ထွက်ပြီးမှသာ တရားဝင်ပြီးပြည့်စုံသော ရလဒ်ဖြစ်သည်
    if not prizes.get('1st'):
        logger.info("⏳ Draw results not fully published yet.")
        return

    last_posted = get_last_posted_draw()
    if current_draw_no and current_draw_no != last_posted:
        logger.info(f"🎉 New draw result found: {current_draw_no}! Formatting and sending to Telegram...")
        message = result_poster.build_result_post(result_data)
        success = bot.send_message(message)
        if success:
            set_last_posted_draw(current_draw_no)
            logger.info(f"✅ Official 4D Result for {current_draw_no} posted successfully to Telegram!")
            # ဒေတာအသစ်ကိုပါ database CSV ထဲ ထပ်မံဖြည့်စွက်သိမ်းဆည်း
            try:
                import scraper
                scraper.update_latest()
            except Exception:
                pass
    else:
        logger.info(f"ℹ️ Latest draw ({current_draw_no}) is already posted.")


def hot_numbers_job():
    """နေ့စဉ် Hot Numbers Post တင်သည့် အလုပ်"""
    logger.info(f"⏰ Hot numbers scheduler triggered at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if not config.POST_ON_DRAW_DAYS_ONLY or datetime.now().weekday() in DRAW_WEEKDAYS:
        hot_pipeline.run()


def start():
    """Master Scheduler စတင်လည်ပတ်ခြင်း"""
    logger.info("=" * 60)
    logger.info("🚀 SALONE 4D - Master Scheduler Started")
    logger.info(f"   1. Daily Hot Numbers Post Time : {config.POST_TIME} (Daily)")
    # 1. နေ့စဉ် သတ်မှတ်ချိန်တွင် Hot numbers ပို့မည်
    schedule.every().day.at(config.POST_TIME).do(hot_numbers_job)

    # 2. Draw နေ့များ (Wed, Sat, Sun) တွင် ညနေ ၅:၄၅ PM မှစ၍ Result အသစ် စစ်ဆေးမည်
    interval = getattr(config, 'RESULT_CHECK_INTERVAL_MINS', 2)
    schedule.every(interval).minutes.do(check_and_post_draw_result)

    logger.info(f"   2. Official Draw Result Check  : Every {interval} mins (5:45 PM - 7:00 PM on Wed, Sat, Sun)")
    logger.info("=" * 60)
    logger.info("✅ All tasks scheduled. Listening for events... (Press Ctrl+C to stop)")

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--result-now':
        # Result post ကို ချက်ချင်း စမ်းတင်လိုပါက
        check_and_post_draw_result()
    elif len(sys.argv) > 1 and sys.argv[1] == '--hot-now':
        # Hot numbers ကို ချက်ချင်း တင်လိုပါက
        hot_numbers_job()
    else:
        start()
