"""
==========================================
SALONE 4D - Master Scheduler
==========================================
၁။ နေ့တိုင်း မနက် ၁၀:၀၀ တွင် Hot Numbers Post တင်ပေးခြင်း
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
_POSTED_DRAWS_MEMORY = set()


def get_last_posted_draw() -> str:
    """နောက်ဆုံး Post တင်ပြီးသော Draw အမှတ်အသားကို ဖတ်သည်"""
    if os.path.exists(LAST_POSTED_DRAW_FILE):
        try:
            with open(LAST_POSTED_DRAW_FILE, 'r', encoding='utf-8') as f:
                val = f.read().strip()
                if val:
                    _POSTED_DRAWS_MEMORY.add(val)
                return val
        except Exception:
            pass
    return ""


def set_last_posted_draw(draw_no_str: str):
    """Post တင်ပြီးသော Draw အမှတ်အသားကို မှတ်သားသည်"""
    val = draw_no_str.strip()
    _POSTED_DRAWS_MEMORY.add(val)
    try:
        with open(LAST_POSTED_DRAW_FILE, 'w', encoding='utf-8') as f:
            f.write(val)
    except Exception as e:
        logger.warning(f"Error saving last posted draw: {e}")


def is_within_result_check_window() -> bool:
    """လက်ရှိအချိန်သည် မြန်မာစံတော်ချိန် ညနေ ၅:၄၅ PM မှ ၇:၀၀ PM အတွင်း ဟုတ်မဟုတ် စစ်ဆေးသည်"""
    try:
        import pytz
        mm_tz = pytz.timezone("Asia/Yangon")
        now = datetime.now(mm_tz)
    except Exception:
        now = datetime.now()

    now_time_str = now.strftime("%H:%M")
    start_time = getattr(config, 'RESULT_CHECK_START_TIME', '17:45')
    end_time = getattr(config, 'RESULT_CHECK_END_TIME', '19:00')
    return start_time <= now_time_str <= end_time


def check_and_post_draw_result():
    """Singapore Pools Draw Result အသစ်ထွက်မထွက် စစ်ဆေးပြီး ထွက်ပါက Telegram သို့ ချက်ချင်း တင်သည်"""
    try:
        import pytz
        mm_tz = pytz.timezone("Asia/Yangon")
        now_dt = datetime.now(mm_tz)
    except Exception:
        now_dt = datetime.now()

    today_weekday = now_dt.weekday()
    if today_weekday not in DRAW_WEEKDAYS:
        return

    # မြန်မာစံတော်ချိန် ညနေ ၅:၄၅ PM မတိုင်မီဆိုလျှင် မ run ပါ
    if not is_within_result_check_window():
        return

    logger.info("🔍 [5:45 PM+ Window] Checking Singapore Pools for new 4D official draw result...")
    result_data = result_poster.fetch_latest_result()
    if not result_data:
        return

    current_draw_no = result_data.get('draw_no_str', '').strip()
    prizes = result_data.get('prizes', {})
    
    # 1st Prize ထွက်ပြီးမှသာ တရားဝင်ပြီးပြည့်စုံသော ရလဒ်ဖြစ်သည်
    if not prizes.get('1st'):
        logger.info("⏳ Draw results not fully published yet.")
        return

    last_posted = get_last_posted_draw()
    if current_draw_no and current_draw_no != last_posted and current_draw_no not in _POSTED_DRAWS_MEMORY:
        logger.info(f"🎉 New draw result found: {current_draw_no}! Formatting and sending to Telegram...")
        # Mark as posted immediately to prevent race conditions from concurrent triggers
        set_last_posted_draw(current_draw_no)

        message = result_poster.build_result_post(result_data)
        success = bot.send_message(message)
        if success:
            logger.info(f"✅ Official 4D Result for {current_draw_no} posted successfully to Telegram!")
            # ဒေတာအသစ်ကိုပါ database CSV ထဲ ထပ်မံဖြည့်စွက်သိမ်းဆည်း
            try:
                import scraper
                scraper.update_latest()
            except Exception:
                pass

            # Result ထွက်ပြီး ၅ မိနစ် (300 စက္ကန့်) အကြာတွင် Lucky Winners post စစ်ဆေးတင်မည်
            schedule_winner_check(result_data, delay_seconds=300)
        else:
            logger.error(f"❌ Failed to send Official 4D Result for {current_draw_no}.")
    else:
        logger.info(f"ℹ️ Latest draw ({current_draw_no}) is already posted.")



def schedule_winner_check(result_data: dict, delay_seconds: int = 300):
    """Result ထွက်ပြီး သတ်မှတ်စက္ကန့်အကြာတွင် Lucky Winner post စစ်ဆေးတင်သည်"""
    import threading
    def _delayed_check():
        logger.info(f"⏳ Waiting {delay_seconds}s before checking Lucky Winners for {result_data.get('draw_no_str')}...")
        time.sleep(delay_seconds)
        try:
            import winner_checker
            post = winner_checker.check_and_build_winner_post(result_data)
            if post:
                sent = bot.send_message(post)
                if sent:
                    logger.info(f"🏆 Lucky Winners celebratory post sent for {result_data.get('draw_no_str')}!")
            else:
                logger.info(f"ℹ️ No matching lucky winners to post for {result_data.get('draw_no_str')}.")
        except Exception as e:
            logger.error(f"Error in delayed winner check: {e}")

    threading.Thread(target=_delayed_check, daemon=True).start()


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
    elif len(sys.argv) > 1 and sys.argv[1] == '--winner-now':
        # Lucky winner post ကို ချက်ချင်း စမ်းစစ်ပြီး တင်လိုပါက
        import winner_checker
        data = result_poster.fetch_latest_result()
        if data:
            post = winner_checker.check_and_build_winner_post(data)
            if post:
                print(post)
                bot.send_message(post)
            else:
                print("No matching winners found for latest draw.")
    else:
        start()
