#!/usr/bin/env python3
# ==========================================================
#   ChateChat Telegram Bot - Auto-Responder Bot
#   Welcome & APK / Web App Download Auto-Reply Service
# ==========================================================

import sys
import logging
import asyncio
from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import config

# ── Force UTF-8 encoding on Windows console ─────────────────
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ── Logging Setup ───────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("ChateChatBot")

# ── Keywords Definition ─────────────────────────────────────
GREETING_KEYWORDS = [
    "hi", "hello", "hey", "မင်္ဂလာပါ", "မင်္ဂလာပါခင်ဗျာ", "မင်္ဂလာပါရှင့်",
    "mingalaba", "hello bot", "hi bot"
]

DOWNLOAD_KEYWORDS = [
    "apk", "app", "download", "လင့်", "လင့်", "ဒေါင်း", "down", "ဆွဲ",
    "link", "link ပေးပါ", "ဒေါင်းနည်း", "apk download"
]


def build_chatechat_keyboard() -> InlineKeyboardMarkup:
    """ChateChat Android APK နှင့် Web App ခလုတ်များ ဖန်တီးသည်"""
    apk_url = getattr(config, "CHATECHAT_APK_URL", "https://tinyurl.com/chatechat-app")
    webapp_url = getattr(config, "CHATECHAT_WEBAPP_URL", "https://chatechat.onrender.com")

    keyboard = [
        [InlineKeyboardButton("📲 Download Android APK", url=apk_url)],
        [InlineKeyboardButton("🌐 Open Web App", url=webapp_url)],
    ]
    return InlineKeyboardMarkup(keyboard)


def build_welcome_message() -> str:
    """Welcome & APK Download လမ်းညွှန် စာသား"""
    apk_url = getattr(config, "CHATECHAT_APK_URL", "https://tinyurl.com/chatechat-app")
    webapp_url = getattr(config, "CHATECHAT_WEBAPP_URL", "https://chatechat.onrender.com")

    message = (
        "💬 *ChateChat မှ ကြိုဆိုပါသည်!* ✨\n"
        "───────────────────────\n\n"
        "မင်္ဂလာပါခင်ဗျာ... ChateChat ကို အသုံးပြုရန်အတွက် အောက်ပါ Link များမှတစ်ဆင့် Android Application (သို့မဟုတ်) Web App ကို အလွယ်တကူ ဝင်ရောက်အသုံးပြုနိုင်ပါသည် 👇\n\n"
        "📲 *Android APK ဒေါင်းလုဒ် ရယူရန်:*\n"
        f"👉 {apk_url}\n\n"
        "🌐 *Web App တိုက်ရိုက် အသုံးပြုရန်:*\n"
        f"👉 {webapp_url}\n\n"
        "အောက်ပါ ခလုတ်များကို နှိပ်၍လည်း တိုက်ရိုက် ဒေါင်းလုဒ်ရယူခြင်း (သို့) Web App ဖွင့်လှစ်ခြင်းများ ပြုလုပ်နိုင်ပါသည်ခင်ဗျာ 👇"
    )
    return message


async def send_welcome_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome & APK Download မက်ဆေ့ခ်ျနှင့် ခလုတ်များကို ပို့ပေးသည်"""
    if not update.effective_chat:
        return

    # Typing status ပြသခြင်း
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    except Exception:
        pass

    text = build_welcome_message()
    keyboard = build_chatechat_keyboard()

    if update.message:
        await update.message.reply_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start သို့မဟုတ် /help command ခေါ်ဆိုမှုများကို ဖြေကြားသည်"""
    await send_welcome_response(update, context)


async def download_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/download, /apk, /app commands များကို ဖြေကြားသည်"""
    await send_welcome_response(update, context)


async def webapp_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/webapp command ကို ဖြေကြားသည်"""
    await send_welcome_response(update, context)


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User ထံမှ ဝင်ရောက်လာသော မက်ဆေ့ခ်ျများကို စစ်ဆေး၍ အလိုအလျောက် တုံ့ပြန်သည်"""
    if not update.message or not update.message.text:
        return

    user_text = update.message.text.strip().lower()

    # Greetings သို့မဟုတ် Download keywords စစ်ဆေးခြင်း
    is_greeting = any(k in user_text for k in GREETING_KEYWORDS)
    is_download = any(k in user_text for k in DOWNLOAD_KEYWORDS)

    # Keywords ပါဝင်ပါက (သို့မဟုတ် Auto-Responder အနေဖြင့် အခြားစာသားများအတွက်ပါ) တုံ့ပြန်ပေးသည်
    if is_greeting or is_download:
        logger.info(f"Matched keyword from user {update.effective_user.id}: {user_text[:30]}")
        await send_welcome_response(update, context)
    else:
        # မည်သည့် မက်ဆေ့ခ်ျ ပို့လာသည်ဖြစ်စေ ကူညီလမ်းညွှန်ပေးသည့်အနေဖြင့် Welcome & Link ပို့ပေးသည်
        logger.info(f"General message from user {update.effective_user.id}: {user_text[:30]}")
        await send_welcome_response(update, context)


async def setup_bot_commands(application: Application):
    """Register menu commands with Telegram so they appear when typing '/'."""
    commands = [
        BotCommand("start", "🏠 ကြိုဆိုပါသည် (Welcome & App Links)"),
        BotCommand("download", "📲 Android APK ဒေါင်းလုဒ် ရယူရန်"),
        BotCommand("webapp", "🌐 Open Web App ဖွင့်ရန်"),
    ]
    try:
        await application.bot.set_my_commands(commands)
        logger.info("✅ ChateChat Bot commands registered successfully.")
    except Exception as e:
        logger.warning(f"Could not register commands for ChateChat bot: {e}")


def main():
    token = getattr(config, "CHATECHAT_BOT_TOKEN", None)
    if not token or token == "YOUR_CHATECHAT_BOT_TOKEN_HERE":
        logger.error("❌ config.py တွင် CHATECHAT_BOT_TOKEN မသတ်မှတ်ရသေးပါ။")
        return

    # Ensure a dedicated asyncio event loop in this thread
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    logger.info("Initializing ChateChat Auto-Responder Bot...")
    application = (
        Application.builder()
        .token(token)
        .post_init(setup_bot_commands)
        .build()
    )

    # Handlers
    application.add_handler(CommandHandler(["start", "help"], start_command))
    application.add_handler(CommandHandler(["download", "apk", "app"], download_command))
    application.add_handler(CommandHandler("webapp", webapp_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    logger.info("✅ ChateChat Auto-Responder Bot is running! Listening for user messages...")
    application.run_polling(stop_signals=None, drop_pending_updates=True)


if __name__ == "__main__":
    main()
