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



# -------- ChateChat Auto-Responder Bot & Webhook Relay ----------
DEBUG_WEBHOOK_LOGS = []

def record_debug_log(category, detail):
    try:
        DEBUG_WEBHOOK_LOGS.append({
            "time": datetime.now(MYANMAR_TZ).strftime("%H:%M:%S"),
            "category": category,
            "detail": detail
        })
        if len(DEBUG_WEBHOOK_LOGS) > 40:
            DEBUG_WEBHOOK_LOGS.pop(0)
    except Exception:
        pass

def get_chatechat_token():
    t = getattr(config, "CHATECHAT_BOT_TOKEN", None) or os.getenv("CHATECHAT_BOT_TOKEN", "")
    if t:
        return t.strip()
    token_file = os.path.join("data", "chatechat_token.txt")
    if os.path.exists(token_file):
        try:
            with open(token_file, "r", encoding="utf-8") as f:
                saved = f.read().strip()
                if saved:
                    os.environ["CHATECHAT_BOT_TOKEN"] = saved
                    setattr(config, "CHATECHAT_BOT_TOKEN", saved)
                    return saved
        except Exception:
            pass
    return ""

def set_chatechat_token(token_val):
    if not token_val:
        return
    token_val = token_val.strip()
    os.environ["CHATECHAT_BOT_TOKEN"] = token_val
    setattr(config, "CHATECHAT_BOT_TOKEN", token_val)
    try:
        os.makedirs("data", exist_ok=True)
        with open(os.path.join("data", "chatechat_token.txt"), "w", encoding="utf-8") as f:
            f.write(token_val)
    except Exception as e:
        logger.warning(f"Could not save chatechat token to disk: {e}")


def sync_to_chatechat_inbox(chat_id, text, bot_name="ChateChat AI"):
    """Sync bot reply to ChateChat Inbox in real-time via Webhook API"""
    def _post():
        try:
            url = getattr(config, "CHATECHAT_BOT_REPLY_URL", "https://chatechat.onrender.com/api/v1/webhooks/telegram/bot-reply")
            payload = {
                "chatId": str(chat_id),
                "text": text,
                "botName": bot_name
            }
            res = req.post(url, json=payload, timeout=8)
            record_debug_log("chatechat_inbox_sync", {"chat_id": chat_id, "status": res.status_code})
            logger.info(f"ChateChat inbox sync status for chat {chat_id}: {res.status_code}")
        except Exception as e:
            record_debug_log("chatechat_inbox_sync_err", {"chat_id": chat_id, "error": str(e)})
            logger.warning(f"ChateChat inbox sync error: {e}")

    threading.Thread(target=_post, daemon=True).start()


def chatechat_send(chat_id, text, reply_markup=None):
    token = get_chatechat_token()
    if not token:
        logger.error("❌ CHATECHAT_BOT_TOKEN is missing!")
        record_debug_log("send_error", "CHATECHAT_BOT_TOKEN is missing")
        return False
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        r = req.post(f"https://api.telegram.org/bot{token}/sendMessage", json=payload, timeout=12)
        res_data = r.json()

        # If Markdown parsing fails (e.g. unescaped symbols), retry with plain text
        if not res_data.get("ok"):
            err_desc = res_data.get("description", "")
            logger.warning(f"Telegram sendMessage with Markdown failed: {err_desc}. Retrying plain text...")
            payload.pop("parse_mode", None)
            r = req.post(f"https://api.telegram.org/bot{token}/sendMessage", json=payload, timeout=12)
            res_data = r.json()

        ok = res_data.get("ok", False)
        if ok:
            record_debug_log("send_ok", {"chat_id": chat_id, "text": text[:35]})
            # Real-time sync to ChateChat Inbox
            sync_to_chatechat_inbox(chat_id, text)
        else:
            record_debug_log("send_failed", {"chat_id": chat_id, "error": res_data})
            logger.error(f"Telegram sendMessage failed: {res_data}")
        return ok
    except Exception as e:
        record_debug_log("send_exception", {"chat_id": chat_id, "error": str(e)})
        logger.error(f"chatechat_send error: {e}")
        return False


def get_chatechat_kb():
    return {
        "inline_keyboard": [
            [{"text": "📲 Download Android APK", "url": getattr(config, "CHATECHAT_APK_URL", "https://tinyurl.com/chatechat-app")}],
            [{"text": "🌐 Open Web App", "url": getattr(config, "CHATECHAT_WEBAPP_URL", "https://chatechat.onrender.com")}]
        ]
    }

def get_chatechat_welcome_msg():
    return (
        "💬 *ChateChat မှ ကြိုဆိုပါသည်!* ✨\n"
        "───────────────────────\n\n"
        "မင်္ဂလာပါခင်ဗျာ... ChateChat ကို အသုံးပြုရန်အတွက် အောက်ပါ Link များမှတစ်ဆင့် Android Application (သို့မဟုတ်) Web App ကို အလွယ်တကူ ဝင်ရောက်အသုံးပြုနိုင်ပါသည် 👇\n\n"
        "📲 *Android APK ဒေါင်းလုဒ် ရယူရန်:*\n"
        f"👉 {getattr(config, 'CHATECHAT_APK_URL', 'https://tinyurl.com/chatechat-app')}\n\n"
        "🌐 *Web App တိုက်ရိုက် အသုံးပြုရန်:*\n"
        f"👉 {getattr(config, 'CHATECHAT_WEBAPP_URL', 'https://chatechat.onrender.com')}\n\n"
        "အောက်ပါ ခလုတ်များကို နှိပ်၍လည်း တိုက်ရိုက် ရယူနိုင်ပါသည်ခင်ဗျာ 👇"
    )

def _process_chatechat_message(chat_id, user_text):
    """Processes user message for ChateChat (shared by Polling & Webhook Relay)"""
    kb = get_chatechat_kb()
    welcome = get_chatechat_welcome_msg()

    t_lower = user_text.lower().strip()
    # Commands or direct download keywords -> instant welcome & download links
    if t_lower in ("/start", "/help", "/download", "/apk", "/app", "/webapp") or \
       any(k in t_lower for k in ["apk", "app", "download", "ဒေါင်း", "လင့်", "လင့်", "down"]):
        chatechat_send(chat_id, welcome, reply_markup=kb)
    else:
        # Simple questions -> ChateChat AI auto-reply
        ai_reply = ""
        try:
            import openrouter_client
            ai_reply = openrouter_client.get_chatechat_ai_reply(user_text)
        except Exception as e:
            logger.error(f"ChateChat AI error: {e}")

        if ai_reply:
            chatechat_send(chat_id, ai_reply, reply_markup=kb)
        else:
            chatechat_send(chat_id, welcome, reply_markup=kb)


def extract_update_info(data):
    """
    Extracts (chat_id, user_text) from any Telegram update or ChateChat Webhook Relay format.
    Handles standard Telegram payloads, ChateChat normalized JSON, nested wrappers, and callback queries.
    """
    if not isinstance(data, dict):
        return None, None

    # 1. Direct ChateChat relay fields: chatId, text
    chat_id = data.get("chatId") or data.get("chat_id")
    text = data.get("text") or data.get("message_text") or data.get("content")

    # 2. Standard Telegram message / edited_message / channel_post
    for k in ("message", "edited_message", "channel_post"):
        m = data.get(k)
        if isinstance(m, dict):
            if not text:
                text = m.get("text") or m.get("caption")
            if not chat_id:
                chat = m.get("chat")
                if isinstance(chat, dict):
                    chat_id = chat.get("id")
                frm = m.get("from")
                if not chat_id and isinstance(frm, dict):
                    chat_id = frm.get("id")
            if chat_id and text:
                return str(chat_id), str(text).strip()

    # 3. Telegram callback_query (inline button clicks)
    cb = data.get("callback_query")
    if isinstance(cb, dict):
        if not text:
            text = cb.get("data")
        if not chat_id:
            m = cb.get("message")
            if isinstance(m, dict) and isinstance(m.get("chat"), dict):
                chat_id = m.get("chat", {}).get("id")
            frm = cb.get("from")
            if not chat_id and isinstance(frm, dict):
                chat_id = frm.get("id")
        if chat_id and text:
            return str(chat_id), str(text).strip()

    # 4. Nested under 'update', 'data', 'payload', 'body'
    for wrapper in ("update", "data", "payload", "body"):
        sub = data.get(wrapper)
        if isinstance(sub, dict):
            c, t = extract_update_info(sub)
            if c and t:
                return c, t

    if chat_id and text:
        return str(chat_id), str(text).strip()

    return None, None


def _handle_incoming_webhook(endpoint_name):
    try:
        u = request.get_json(force=True, silent=True)
        if not u and request.form:
            u = request.form.to_dict()
        if not u:
            raw = request.get_data(as_text=True)
            if raw:
                try:
                    u = json.loads(raw)
                except Exception:
                    pass
        u = u or {}

        record_debug_log("incoming_webhook", {
            "endpoint": endpoint_name,
            "raw_keys": list(u.keys()) if isinstance(u, dict) else str(type(u)),
            "summary": str(u)[:160]
        })

        chat_id, user_text = extract_update_info(u)
        if chat_id and user_text:
            logger.info(f"Incoming update on {endpoint_name} from {chat_id}: {user_text[:30]}")
            record_debug_log("processed_message", {"endpoint": endpoint_name, "chat_id": chat_id, "text": user_text[:30]})
            threading.Thread(target=_process_chatechat_message, args=(chat_id, user_text), daemon=True).start()
            return "OK", 200
        else:
            record_debug_log("ignored_webhook", {"endpoint": endpoint_name, "data": str(u)[:120]})
    except Exception as e:
        record_debug_log("webhook_error", {"endpoint": endpoint_name, "error": str(e)})
        logger.error(f"Webhook {endpoint_name} error: {e}")

    return "OK", 200


@app.route("/webhook/chatechat", methods=["POST", "GET"])
def chatechat_webhook():
    if request.method == "GET":
        return jsonify({"service": "chatechat_webhook", "status": "active"}), 200
    return _handle_incoming_webhook("webhook_chatechat")


@app.route("/webhook", methods=["POST", "GET"])
def webhook():
    if request.method == "GET":
        return jsonify({"service": "webhook", "status": "active"}), 200
    return _handle_incoming_webhook("webhook_root")


@app.route("/webhook/debug", methods=["GET"])
def webhook_debug():
    token = get_chatechat_token()
    token_suffix = token[-6:] if token else "None"
    return jsonify({
        "status": "ok",
        "token_configured": bool(token),
        "token_suffix": token_suffix,
        "logs_count": len(DEBUG_WEBHOOK_LOGS),
        "logs": DEBUG_WEBHOOK_LOGS
    }), 200


def ensure_chatechat_relay():
    """Keeps ChateChat Webhook Relay connected and healthy automatically"""
    token = get_chatechat_token()
    if not token:
        return
    try:
        status_url = "https://chatechat.onrender.com/api/v1/webhooks/telegram/status"
        res = req.get(status_url, timeout=8)
        if res.status_code == 200:
            st = res.json()
            target_forward = "https://salone4d-telegram-bot.onrender.com/webhook/chatechat"
            if not st.get("isActive") or st.get("forwardWebhookUrl") != target_forward:
                logger.info("ChateChat relay not active or forward URL missing. Auto-connecting...")
                connect_url = "https://chatechat.onrender.com/api/v1/webhooks/connect/telegram"
                payload = {
                    "botToken": token,
                    "forwardWebhookUrl": target_forward,
                    "mode": "WEBHOOK_RELAY",
                    "organizationId": "org_royal"
                }
                c_res = req.post(connect_url, json=payload, timeout=12)
                logger.info(f"ChateChat auto-heal connect status: {c_res.status_code}")
                record_debug_log("chatechat_auto_heal", {"status": c_res.status_code})
    except Exception as e:
        logger.warning(f"ChateChat keep-alive check: {e}")


def run_chatechat_bot():
    """ChateChat Auto-Responder polling fallback & relay health thread"""
    import time
    last_id = 0
    last_health_check = 0

    logger.info("🤖 Starting ChateChat Auto-Responder service...")
    commands_set = False

    while True:
        token = get_chatechat_token()
        if not token:
            time.sleep(10)
            continue

        # Periodically ensure ChateChat platform Webhook Relay is connected & active
        now = time.time()
        if now - last_health_check > 60:
            last_health_check = now
            threading.Thread(target=ensure_chatechat_relay, daemon=True).start()

        if not commands_set:
            try:
                req.post(f"https://api.telegram.org/bot{token}/setMyCommands", json={
                    "commands": [
                        {"command": "start", "description": "🏠 ကြိုဆိုပါသည် (Welcome & App Links)"},
                        {"command": "download", "description": "📲 Android APK ဒေါင်းလုဒ်"},
                        {"command": "webapp", "description": "🌐 Web App ဖွင့်ရန်"},
                    ]
                }, timeout=10)
                commands_set = True
                logger.info("ChateChat setMyCommands registered successfully.")
            except Exception as e:
                logger.warning(f"ChateChat setMyCommands: {e}")

        try:
            r = req.post(f"https://api.telegram.org/bot{token}/getUpdates",
                json={"offset": last_id + 1, "timeout": 30, "allowed_updates": ["message"]},
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
                msg = upd.get("message")
                if msg and msg.get("text"):
                    chat_id = msg["chat"]["id"]
                    user_text = msg["text"].strip()
                    logger.info(f"ChateChat polling received from {chat_id}: {user_text[:30]}")
                    _process_chatechat_message(chat_id, user_text)
        except Exception as e:
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

def app_job():
    logger.info("App download link job triggered")
    try:
        import app_poster
        app_poster.post_app_download_if_due()
    except Exception as e:
        logger.error(f"App download job failed: {e}", exc_info=True)

def draw_job():
    try:
        import scheduler
        scheduler.check_and_post_draw_result()
    except Exception as e:
        logger.error(f"Draw job failed: {e}", exc_info=True)



def schedule_winner_check(result_data: dict, delay_seconds: int = 300):
    """Result ထွက်ပြီး သတ်မှတ်စက္ကန့်အကြာတွင် Lucky Winner post စစ်ဆေးတင်သည်"""
    def _delayed_check():
        logger.info(f"⏳ Waiting {delay_seconds}s before checking Lucky Winners for {result_data.get('draw_no_str')}...")
        import time
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


@app.route("/")
def index():
    cc_token = get_chatechat_token()
    return jsonify({
        "status": "running",
        "bot": config.CHANNEL_ID,
        "chatechat_configured": bool(cc_token),
        "chatechat_token_suffix": cc_token[-6:] if cc_token else "None",
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

@app.route("/trigger/applink", methods=["POST"])
def trig_applink():
    def _run_app():
        import app_poster
        app_poster.post_app_download_if_due(force=True)
    threading.Thread(target=_run_app, daemon=True).start()
    return jsonify({"status": "ok", "job": "applink"})

@app.route("/trigger/winner", methods=["POST"])
def trig_winner():
    def _run_winner():
        data = result_poster.fetch_latest_result()
        if data:
            import winner_checker
            post = winner_checker.check_and_build_winner_post(data)
            if post:
                bot.send_message(post)
    threading.Thread(target=_run_winner, daemon=True).start()
    return jsonify({"status": "ok"})


@app.route("/config/chatechat", methods=["POST", "GET"])
def config_chatechat():
    if request.method == "POST":
        data = request.get_json(force=True, silent=True) or {}
        new_token = data.get("token") or request.args.get("token")
        if new_token:
            set_chatechat_token(new_token)
            return jsonify({"status": "ok", "message": "CHATECHAT_BOT_TOKEN configured successfully"}), 200
        return jsonify({"status": "error", "message": "Missing token parameter"}), 400
    token = get_chatechat_token()
    token_suffix = token[-6:] if token else "None"
    return jsonify({"service": "chatechat", "configured": bool(token), "token_suffix": token_suffix})


# ---- Startup: run at module level (gunicorn imports this) ----
logger.info("Starting SALONE 4D background services...")
try:
    h, m = config.POST_TIME.split(":")
    scheduler.add_job(hot_job, CronTrigger(hour=int(h), minute=int(m), timezone=MYANMAR_TZ), id="h", replace_existing=True)
    app_h, app_m = getattr(config, 'APP_POST_TIME', '10:30').split(":")
    scheduler.add_job(app_job, CronTrigger(hour=int(app_h), minute=int(app_m), timezone=MYANMAR_TZ), id="app_dl", replace_existing=True)
    scheduler.add_job(draw_job, CronTrigger(minute=f"*/{config.RESULT_CHECK_INTERVAL_MINS}", hour="17-19", timezone=MYANMAR_TZ), id="d", replace_existing=True)
    scheduler.start()
    logger.info("Scheduler started!")
except Exception as e:
    logger.error(f"Scheduler: {e}")

def keep_alive_worker():
    """
    Pings both Salone4D bot server and ChateChat platform every 6 minutes
    to prevent Render Free Tier instances from going to sleep.
    """
    import time
    logger.info("🔄 Keep-alive worker started (6-min interval)")
    time.sleep(20)
    while True:
        try:
            self_url = os.getenv("RENDER_EXTERNAL_URL") or "https://salone4d-telegram-bot.onrender.com"
            r = req.get(f"{self_url.rstrip('/')}/ping", timeout=12)
            logger.info(f"🔄 Keep-alive ping self ({self_url}): {r.status_code}")
        except Exception as e:
            logger.warning(f"Keep-alive self ping error: {e}")

        try:
            cc_url = getattr(config, "CHATECHAT_WEBAPP_URL", "https://chatechat.onrender.com")
            r_cc = req.get(f"{cc_url.rstrip('/')}/api/v1/webhooks/telegram/status", timeout=12)
            logger.info(f"🔄 Keep-alive ping ChateChat ({cc_url}): {r_cc.status_code}")
        except Exception as e:
            logger.warning(f"Keep-alive ChateChat ping error: {e}")

        time.sleep(360)


t = threading.Thread(target=run_bot, daemon=True)
t.start()

t_cc = threading.Thread(target=run_chatechat_bot, daemon=True)
t_cc.start()

t_keepalive = threading.Thread(target=keep_alive_worker, daemon=True)
t_keepalive.start()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"Flask on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
