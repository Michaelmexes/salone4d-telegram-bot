"""
SALONE 4D - Render Server (Webhook + Polling)
===========================================
Flask + python-telegram-bot + APScheduler
"""
import os, sys, json, threading, logging, asyncio
from datetime import datetime

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from flask import Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

import config, bot, main as hot_pipeline, result_poster
import requests as req

os.makedirs("data", exist_ok=True)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("data/server.log", encoding="utf-8")])
logger = logging.getLogger(__name__)

MYANMAR_TZ = pytz.timezone("Asia/Yangon")
app = Flask(__name__)
scheduler = BackgroundScheduler(timezone=MYANMAR_TZ)
DRAW_WEEKDAYS = {2, 5, 6}
LAST_POSTED_DRAW_FILE = "data/last_posted_draw.txt"


# -------- Telegram REST helpers ----------
def tg_send(chat_id, text, parse_mode="HTML", reply_markup=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode, "disable_web_page_preview": True}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        r = req.post(f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage", json=payload, timeout=10)
        return r.json().get("ok", False)
    except Exception as e:
        logger.error(f"tg_send: {e}")
        return False

def tg_edit(chat_id, msg_id, text, parse_mode="HTML", reply_markup=None):
    payload = {"chat_id": chat_id, "message_id": msg_id, "text": text, "parse_mode": parse_mode}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        r = req.post(f"https://api.telegram.org/bot{config.BOT_TOKEN}/editMessageText", json=payload, timeout=10)
        return r.json().get("ok", False)
    except Exception as e:
        logger.error(f"tg_edit: {e}")
        return False

def tg_answer(cb_id):
    try:
        req.post(f"https://api.telegram.org/bot{config.BOT_TOKEN}/answerCallbackQuery",
                 json={"callback_query_id": cb_id}, timeout=5)
    except Exception:
        pass


# -------- Keyboards ----------
def mk_kb(rows):
    return {"inline_keyboard": rows}

MAIN_KB = mk_kb([
    [{"text": "၁။ 4D App လေးသွင်းပါ (link)", "url": "https://t.ly/pemBm"}],
    [{"text": "၂။ 4D App သုံးနည်း", "callback_data": "app_usage"}],
    [{"text": "၃။ Viber (သိလိုရာမေး)", "callback_data": "viber"}],
])
APP_USAGE_KB = mk_kb([
    [{"text": "၂.၁ Register / Login ဝင်နည်း", "callback_data": "reg"}],
    [{"text": "၂.၂ 4D ထိုးနည်း", "callback_data": "bet"}],
    [{"text": "၂.၃ ငွေသွင်း/ငွေထုတ်နည်း", "callback_data": "money"}],
    [{"text": "၂.၄ ထိုးထားတာပြန်စစ်နည်း", "callback_data": "check"}],
    [{"text": "◀️ Main Menu သို့ ပြန်သွားရန်", "callback_data": "main_menu"}],
])
SUB_KB = mk_kb([
    [{"text": "◀️ App သုံးနည်း သို့ ပြန်သွားရန်", "callback_data": "app_usage"}],
    [{"text": "🏠 Main Menu သို့ ပြန်သွားရန်", "callback_data": "main_menu"}],
])
SUPPORT_KB = mk_kb([
    [{"text": "💬 Viber ဆက်သွယ်ရန်", "url": "https://viber.click/959894169717"}],
    [{"text": "✈️ Telegram Support", "url": "https://t.me/salone4DAdmin"}],
    [{"text": "🏠 Main Menu သို့ ပြန်သွားရန်", "callback_data": "main_menu"}],
])


# -------- Content ----------
WELCOME = "🎰 *Salone4D ထီဝန်ဆောင်မှုမှ ကြိုဆိုပါသည်!*\n\nအောက်ပါ မီနူးများမှတစ်ဆင့် ရွေးချယ်နိုင်ပါသည် 👇"
MAIN_MSG = "🏠 *Main Menu* - ခလုတ်တစ်ခု ရွေးချယ်ပါ 👇"

TEXTS = {
    "reg": "📝 *၂.၁ Register လုပ်နည်း / login ဝင်နည်း*\n\n❶ *အကောင့်ဖွင့်နည်း (Register):*\n• App ကို ဖွင့်ပါ။\n• ဘယ်ဘက်အောက်ထောင့်ရှိ 'အကောင့်လုပ်မည်' သို့ ဝင်ပါ။\n• အမည်၊ ဖုန်းနံပါတ်၊ လျှို့ဝှက်နံပါတ် ဖြည့်သွင်း၍ 'ဖွင့်မည်' ကို နှိပ်ပါ\n\n❷ *Login ဝင်နည်း:*\n• အကောင့်ဖွင့်ထားသော ဖုန်းနံပါတ်နှင့် Password ရိုက်ထည့်၍ ဝင်ရောက်ပါ",
    "bet": "🎰 *၂.၂ 4D ထိုးနည်း*\n\n• App ၏ အလယ်ဗဟိုရှိ *'Buy'* ခလုတ်ကို နှိပ်ပါ\n• အပေါ်တွင် ထိုးချင်သည့် ရက်စွဲနှင့် ထီအမျိုးအစား (4D / Sweep) ကို ရွေးချယ်ပါ\n• မိမိကြိုက်နှစ်သက်ရာ ဂဏန်းများ ရွေးချယ်ပြီး 'ထည့်မည်' ကို နှိပ်ပါ\n• ဂဏန်းအကုန်ရွေးပြီးပါက 'ရှေ့သို့' နှိပ်၍ အတည်ပြုပါ",
    "money": "💳 *၂.၃ ငွေသွင်း/ငွေထုတ်နည်း*\n\n❶ *ငွေသွင်းနည်း:*\n• 'Cash' > 'ငွေသွင်း' သို့သွားပါ\n• KBZPay သို့မဟုတ် WaveMoney ဖြင့် အနည်းဆုံး ကျပ် ၁,၀၀၀ သွင်းနိုင်ပါသည် (နံနက် ၉ နာရီမှ ည ၉ နာရီအတွင်း)\n\n❷ *ငွေထုတ်နည်း:*\n• 'Cash' > 'ငွေထုတ်' သို့သွားပါ\n• ငွေလက်ခံမည့် ဖုန်းနံပါတ်နှင့် ပမာဏဖြည့်သွင်း၍ ထုတ်ယူနိုင်ပါသည်။",
    "check": "🔍 *၂.၄ ထိုးထားတာပြန်စစ်နည်း*\n\n• ဝယ်ယူပြီးသော ထီလက်မှတ်များ နှင့် ထိုးထားသည့် ဂဏန်းများကို App ထဲရှိ *'Record'* သို့မဟုတ် *'History'* မီနူးတွင် စိတ်ချစွာ ပြန်လည်စစ်ဆေးနိုင်ပါသည်။",
    "viber": "📞 *ဆက်သွယ်ရန်*\n\n💬 Viber: +95 9 894 169 717\n✈️ Telegram: @salone4DAdmin\n",
}
FALLBACK = (
    "မင်္ဂလာပါခင်ဗျာ 🙏\n"
    "အသေးစိတ် သိရှိလိုပါက အောက်ပါ Main Menu ခလုတ်များမှတစ်ဆင့် ဝင်ရောက်ကြည့်ရှုနိုင်ပါသည် 👇\n\n"
    "အသေးစိတ် တိုက်ရိုက်မေးမြန်းလိုပါက Viber: +95 9 894 169 717 သို့ ဆက်သွယ်နိုင်ပါသည်။"
)


# -------- Handlers ----------
def handle_start(chat_id):
    tg_send(chat_id, WELCOME, reply_markup=MAIN_KB)

def handle_applink(chat_id):
    app_url = getattr(config, "APP_LINK", "https://t.ly/pemBm")
    text = (
        "📲 <b>Salone4D Application ဒေါင်းလုဒ်ရယူရန်</b>\n\n"
        "အောက်ပါ Link ကို နှိပ်၍ Salone4D Application ကို အလွယ်တကူ ဒေါင်းလုဒ် ရယူနိုင်ပါသည် 👇\n\n"
        f"🔗 <b>Download Link:</b> {app_url}\n"
        "🌐 <b>Official Website:</b> www.salone4d.com"
    )
    kb = mk_kb([
        [{"text": "📲 App ဒေါင်းလုဒ် ရယူရန်", "url": app_url}],
        [{"text": "🏠 Main Menu သို့ ပြန်သွားရန်", "callback_data": "main_menu"}],
    ])
    tg_send(chat_id, text, reply_markup=kb)

def handle_appguide(chat_id):
    text = "📖 <b>၂။ 4D App သုံးနည်း</b>\nသိလိုသည့် အကြောင်းအရာကို ရွေးချယ်ပါ 👇"
    tg_send(chat_id, text, reply_markup=APP_USAGE_KB)

def handle_support(chat_id):
    text = TEXTS["viber"]
    tg_send(chat_id, text, reply_markup=SUPPORT_KB)

def handle_reset(chat_id):
    try:
        import memory_manager
        memory_manager.clear_user_history(chat_id)
    except Exception:
        pass
    text = (
        "🧹 <b>စကားပြော မှတ်တမ်းများကို ရှင်းလင်းလိုက်ပါပြီ။</b>\n\n"
        "မင်္ဂလာပါခင်ဗျာ! အသစ်ပြန်လည် စတင်မေးမြန်းနိုင်ပါပြီ။"
    )
    tg_send(chat_id, text, reply_markup=MAIN_KB)

def handle_cb(chat_id, msg_id, cb_id, data):
    tg_answer(cb_id)
    if data == "main_menu":
        tg_edit(chat_id, msg_id, MAIN_MSG, reply_markup=MAIN_KB)
    elif data == "app_usage":
        tg_edit(chat_id, msg_id, MAIN_MSG, reply_markup=APP_USAGE_KB)
    elif data == "viber":
        tg_edit(chat_id, msg_id, TEXTS["viber"], reply_markup=SUPPORT_KB)
    elif data in TEXTS:
        tg_edit(chat_id, msg_id, TEXTS[data], reply_markup=SUB_KB)

def handle_text(chat_id, text):
    if config.OPENROUTER_API_KEY:
        try:
            import openrouter_client, memory_manager
            memory_manager.add_message(chat_id, "user", text)
            history = memory_manager.get_user_history(chat_id)
            reply = openrouter_client.get_ai_reply(text, history)
            if reply:
                memory_manager.add_message(chat_id, "assistant", reply)
                tg_send(chat_id, reply)
                return
        except Exception as e:
            logger.error(f"OpenRouter: {e}")
    tg_send(chat_id, FALLBACK, reply_markup=MAIN_KB)


# -------- Polling Bot Thread ----------
def run_bot():
    """Simple REST API polling - no python-telegram-bot dependency"""
    import time
    last_id = 0
    token = getattr(config, "BOT_TOKEN", None) or os.getenv("BOT_TOKEN", "")
    if not token:
        logger.error("❌ BOT_TOKEN is missing! Please configure BOT_TOKEN in Render Environment variables.")
        return

    logger.info("REST polling started (no python-telegram-bot)")

    # Set Telegram bot menu commands
    try:
        req.post(f"https://api.telegram.org/bot{token}/setMyCommands", json={
            "commands": [
                {"command": "start", "description": "🏠 ပင်မ မီနူး (Main Menu)"},
                {"command": "applink", "description": "📲 4D App ဒေါင်းလုဒ် Link"},
                {"command": "appguide", "description": "📖 4D App အသုံးပြုနည်း လမ်းညွှန်"},
                {"command": "support", "description": "💬 ဆက်သွယ်ရန် / အကူအညီ"},
                {"command": "reset", "description": "🧹 မှတ်တမ်းရှင်းလင်းရန် (New Chat)"},
            ]
        }, timeout=10)
    except Exception as e:
        logger.warning(f"setMyCommands failed: {e}")

    while True:
        try:
            r = req.post(f"https://api.telegram.org/bot{token}/getUpdates", 
                json={"offset": last_id + 1, "timeout": 30, "allowed_updates": ["message", "callback_query"]},
                timeout=35)
            data = r.json()
            if not data.get("ok"):
                time.sleep(5)
                continue
            for upd in data.get("result", []):
                uid = upd["update_id"]
                if uid <= last_id:
                    continue
                last_id = uid
                cb = upd.get("callback_query")
                msg = upd.get("message")
                if cb:
                    handle_cb(cb["message"]["chat"]["id"], cb["message"]["message_id"], cb["id"], cb["data"])
                elif msg and msg.get("text"):
                    t = msg["text"].strip()
                    cmd = t.split()[0].lower() if t.startswith("/") else ""
                    if cmd == "/start":
                        handle_start(msg["chat"]["id"])
                    elif cmd == "/applink":
                        handle_applink(msg["chat"]["id"])
                    elif cmd == "/appguide":
                        handle_appguide(msg["chat"]["id"])
                    elif cmd == "/support":
                        handle_support(msg["chat"]["id"])
                    elif cmd in ("/reset", "/newchat"):
                        handle_reset(msg["chat"]["id"])
                    elif t.startswith("/"):
                        handle_start(msg["chat"]["id"])
                    else:
                        handle_text(msg["chat"]["id"], t)
        except Exception as e:
            logger.error(f"Polling: {e}")
            time.sleep(5)



@app.route("/trigger/test", methods=["POST"])
def trig_test():
    """Test: manually run hot numbers pipeline and post to channel"""
    def _test():
        logger.info("Manual test trigger: running hot numbers pipeline...")
        try:
            result = hot_pipeline.run()
            logger.info(f"Test pipeline result: {result}")
        except Exception as e:
            logger.error(f"Test failed: {e}", exc_info=True)
    threading.Thread(target=_test, daemon=True).start()
    return jsonify({"status": "ok", "job": "test"})

# -------- Webhook ----------
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        u = request.get_json(force=True)
        if not u:
            return "OK", 200
        msg = u.get("message", {})
        cb = u.get("callback_query", {})
        if cb:
            handle_cb(cb["message"]["chat"]["id"], cb["message"]["message_id"], cb["id"], cb["data"])
        elif msg and msg.get("text"):
            t = msg["text"].strip()
            if t.startswith("/"):
                handle_start(msg["chat"]["id"])
            else:
                handle_text(msg["chat"]["id"], t)
    except Exception:
        pass
    return "OK", 200


# -------- Scheduler ----------
def _last_posted():
    if os.path.exists(LAST_POSTED_DRAW_FILE):
        try:
            with open(LAST_POSTED_DRAW_FILE, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            pass
    return ""

def _save_last(d):
    try:
        with open(LAST_POSTED_DRAW_FILE, "w", encoding="utf-8") as f:
            f.write(d.strip())
    except Exception:
        pass

def hot_job():
    logger.info("Hot numbers job triggered")
    try:
        if not config.POST_ON_DRAW_DAYS_ONLY or datetime.now().weekday() in DRAW_WEEKDAYS:
            result = hot_pipeline.run()
            if result:
                logger.info("Hot numbers posted successfully")
            else:
                logger.warning("Hot numbers pipeline returned False")
    except Exception as e:
        logger.error(f"Hot numbers job failed: {e}", exc_info=True)

def draw_job():
    try:
        if datetime.now(MYANMAR_TZ).weekday() not in DRAW_WEEKDAYS:
            return
        now = datetime.now(MYANMAR_TZ).strftime("%H:%M")
        if not (config.RESULT_CHECK_START_TIME <= now <= config.RESULT_CHECK_END_TIME):
            return
        data = result_poster.fetch_latest_result()
        if not data or not data.get("prizes", {}).get("1st"):
            return
        dn = data.get("draw_no_str", "")
        if dn and dn != _last_posted():
            msg = result_poster.build_result_post(data)
            if bot.send_message(msg):
                _save_last(dn)
                logger.info(f"Draw {dn} posted!")
                try:
                    import scraper; scraper.update_latest()
                except Exception:
                    pass
    except Exception as e:
        logger.error(f"Draw job failed: {e}", exc_info=True)


@app.route("/")
def index():
    return jsonify({"status": "running", "bot": f"@{config.CHANNEL_ID}",
        "time": datetime.now(MYANMAR_TZ).isoformat(),
        "scheduled_posts": {"hot_numbers": config.POST_TIME,
            "draw_check": f"{config.RESULT_CHECK_INTERVAL_MINS} mins (5:45-7PM Wed/Sat/Sun)"}})

@app.route("/health")
@app.route("/ping")
def health():
    return "OK", 200

@app.route("/trigger/hot", methods=["POST"])
def trig_hot():
    threading.Thread(target=hot_job, daemon=True).start()
    return jsonify({"status": "ok"})

@app.route("/trigger/result", methods=["POST"])
def trig_draw():
    threading.Thread(target=draw_job, daemon=True).start()
    return jsonify({"status": "ok"})


# ---- Startup: run at module level (gunicorn imports this) ----
logger.info("Starting SALONE 4D background services...")
try:
    h, m = config.POST_TIME.split(":")
    scheduler.add_job(hot_job, CronTrigger(hour=int(h), minute=int(m), timezone=MYANMAR_TZ), id="h", replace_existing=True)
    scheduler.add_job(draw_job, CronTrigger(minute=f"*/{config.RESULT_CHECK_INTERVAL_MINS}", hour="17-19", timezone=MYANMAR_TZ), id="d", replace_existing=True)
    scheduler.start()
    logger.info("Scheduler started!")
except Exception as e:
    logger.error(f"Scheduler: {e}")

t = threading.Thread(target=run_bot, daemon=True)
t.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"Flask on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
