#!/usr/bin/env python3
# ==========================================================
#   Salone4D Telegram Bot - Customer Service Auto-Reply Bot
#   Powered by OpenRouter Free AI Models & Inline Menu System
# ==========================================================

import sys
import logging
import asyncio
from telegram import Update, BotCommand
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
import config
from keyboards import (
    get_string,
    main_menu_keyboard,
    app_usage_menu_keyboard,
    sub_answer_keyboard,
    back_keyboard,
    app_link_keyboard,
    support_keyboard,
)
import openrouter_client
import memory_manager

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
logger = logging.getLogger(__name__)

# User language cache (defaults to Myanmar 'my')
user_lang = {}


def get_user_lang(user_id: int) -> str:
    return user_lang.get(user_id, "my")


# ══════════════════════════════════════════════════════════════
#   /start and /help Commands
# ══════════════════════════════════════════════════════════════
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    user_lang[user_id] = "my"

    welcome_text = get_string("WELCOME", "my")
    keyboard = main_menu_keyboard("my")

    if update.message:
        await update.message.reply_text(
            text=welcome_text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )


# ══════════════════════════════════════════════════════════════
#   /applink Command - App Download Link
# ══════════════════════════════════════════════════════════════
async def applink_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_user_lang(user_id)
    app_url = getattr(config, "APP_LINK", "https://t.ly/pemBm")
    
    text = (
        "📲 *Salone4D Application ဒေါင်းလုဒ်ရယူရန်*\n\n"
        "အောက်ပါ Link ကို နှိပ်၍ Salone4D Application ကို အလွယ်တကူ ဒေါင်းလုဒ် ရယူနိုင်ပါသည် 👇\n\n"
        f"🔗 *Download Link:* {app_url}\n"
        "🌐 *Official Website:* www.salone4d.com"
    )
    if update.message:
        await update.message.reply_text(
            text=text,
            reply_markup=app_link_keyboard(lang),
            parse_mode="Markdown"
        )


# ══════════════════════════════════════════════════════════════
#   /appguide Command - App Usage Guide Menu
# ══════════════════════════════════════════════════════════════
async def appguide_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_user_lang(user_id)
    text = get_string("APP_USAGE_MENU", lang)
    keyboard = app_usage_menu_keyboard(lang)
    
    if update.message:
        await update.message.reply_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )


# ══════════════════════════════════════════════════════════════
#   /support Command - Contact & Viber Support Info
# ══════════════════════════════════════════════════════════════
async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_user_lang(user_id)
    text = get_string("VIBER_INFO", lang)
    keyboard = support_keyboard(lang)
    
    if update.message:
        await update.message.reply_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )


# ══════════════════════════════════════════════════════════════
#   /reset Command - Clear User Conversation Memory
# ══════════════════════════════════════════════════════════════
async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_user_lang(user_id)
    memory_manager.clear_user_history(user_id)
    
    text = (
        "🧹 *စကားပြော မှတ်တမ်းများကို ရှင်းလင်းလိုက်ပါပြီ။*\n\n"
        "မင်္ဂလာပါခင်ဗျာ! အသစ်ပြန်လည် စတင်မေးမြန်းနိုင်ပါပြီ။"
    )
    if update.message:
        await update.message.reply_text(
            text=text,
            reply_markup=main_menu_keyboard(lang),
            parse_mode="Markdown"
        )


# ══════════════════════════════════════════════════════════════
#   Main Menu Helper
# ══════════════════════════════════════════════════════════════
async def show_main_menu(update: Update, lang: str):
    query = update.callback_query
    text = get_string("MAIN_MENU", lang)
    keyboard = main_menu_keyboard(lang)

    await query.edit_message_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


# ══════════════════════════════════════════════════════════════
#   Callback Query Handler (Inline Button Presses)
# ══════════════════════════════════════════════════════════════
async def button_click_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    lang = get_user_lang(user_id)
    data = query.data

    # ── Main Menu ──────────────────────────────────────────
    if data in ("main_menu", "back_main"):
        await show_main_menu(update, lang)
        return

    # ── Menu 2: 4D App သုံးနည်း ─────────────────────────────
    elif data == "menu_app_usage":
        await query.edit_message_text(
            text=get_string("APP_USAGE_MENU", lang),
            reply_markup=app_usage_menu_keyboard(lang),
            parse_mode="Markdown"
        )

    # ── Submenu 2.1: Register / Login ──────────────────────
    elif data == "usage_register":
        await query.edit_message_text(
            text=get_string("USAGE_REGISTER", lang),
            reply_markup=sub_answer_keyboard(lang),
            parse_mode="Markdown"
        )

    # ── Submenu 2.2: 4D ထိုးနည်း ─────────────────────────────
    elif data == "usage_betting":
        await query.edit_message_text(
            text=get_string("USAGE_BETTING", lang),
            reply_markup=sub_answer_keyboard(lang),
            parse_mode="Markdown"
        )

    # ── Submenu 2.3: ငွေသွင်း/ငွေထုတ်နည်း ─────────────────────
    elif data == "usage_money":
        await query.edit_message_text(
            text=get_string("USAGE_MONEY", lang),
            reply_markup=sub_answer_keyboard(lang),
            parse_mode="Markdown"
        )

    # ── Submenu 2.4: ထိုးထားတာပြန်စစ်နည်း ──────────────────────
    elif data == "usage_check_history":
        await query.edit_message_text(
            text=get_string("USAGE_CHECK_HISTORY", lang),
            reply_markup=sub_answer_keyboard(lang),
            parse_mode="Markdown"
        )

    # ── Menu 3: Viber (သိလိုရာမေး) ─────────────────────────────
    elif data == "menu_viber":
        await query.edit_message_text(
            text=get_string("VIBER_INFO", lang),
            reply_markup=back_keyboard(lang),
            parse_mode="Markdown"
        )


# ══════════════════════════════════════════════════════════════
#   OpenRouter AI Chat Handler (Free-text messages)
# ══════════════════════════════════════════════════════════════
async def handle_user_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_id = update.effective_user.id
    user_text = update.message.text.strip()
    lang = get_user_lang(user_id)

    # Show typing action
    await update.message.chat.send_action(action=ChatAction.TYPING)

    # Send temporary thinking notification
    thinking_msg = (
        "🤖 ခဏစောင့်ပေးပါ... AI မှ တွေးတောဖြေကြားပေးနေပါသည်..."
        if lang == "my"
        else "🤖 Please wait... AI assistant is replying..."
    )
    sent_msg = await update.message.reply_text(thinking_msg)

    # Save incoming user message to memory
    memory_manager.add_message(user_id, "user", user_text)
    user_history = memory_manager.get_user_history(user_id)

    # Query OpenRouter in a separate thread so event loop is not blocked
    loop = asyncio.get_running_loop()
    try:
        reply_text = await loop.run_in_executor(
            None,
            openrouter_client.get_ai_reply,
            user_text,
            user_history
        )
    except Exception as e:
        logger.error(f"Error querying OpenRouter: {e}")
        reply_text = (
            "မင်္ဂလာပါခင်ဗျာ 🙏\n"
            "အသေးစိတ် သိရှိလိုပါက အောက်ပါ Main Menu ခလုတ်များမှတစ်ဆင့် ဝင်ရောက်ကြည့်ရှုနိုင်ပါသည် 👇"
        )

    # Save AI response to memory
    memory_manager.add_message(user_id, "assistant", reply_text)

    # Delete temporary thinking message
    try:
        await context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=sent_msg.message_id
        )
    except Exception:
        pass

    # Send AI reply along with Back to Main menu button
    reply_markup = back_keyboard(lang)
    try:
        await update.message.reply_text(
            text=reply_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    except Exception:
        # Fallback to plain text if Markdown has invalid entities
        await update.message.reply_text(
            text=reply_text,
            reply_markup=reply_markup
        )


async def setup_bot_commands(application: Application):
    """Register menu commands with Telegram so they appear when typing '/'."""
    commands = [
        BotCommand("start", "🏠 မူလ မနူး (Main Menu)"),
        BotCommand("applink", "📲 4D App ဒေါင်းလုဒ် Link"),
        BotCommand("appguide", "📖 4D App အသုံးပြုနည်း လမ်းညွှန်"),
        BotCommand("support", "💬 ဆက်သွယ်ရန် / အကူအညီ"),
        BotCommand("reset", "🧹 မှတ်တမ်းရှင်းလင်းရန် (New Chat)"),
        BotCommand("help", "❓ အကူအညီ ရယူရန်"),
    ]
    try:
        await application.bot.set_my_commands(commands)
        logger.info("✅ Bot commands menu registered successfully.")
    except Exception as e:
        logger.warning(f"Could not register commands menu: {e}")


# ══════════════════════════════════════════════════════════════
#   Main Entry Point
# ══════════════════════════════════════════════════════════════
def main():
    token = getattr(config, "BOT_TOKEN", None)
    if not token or token == "YOUR_BOT_TOKEN_HERE":
        logger.error("❌ config.py တွင် BOT_TOKEN မသတ်မှတ်ရသေးပါ။")
        return

    logger.info("Initializing Salone4D Customer Service Bot with OpenRouter AI...")
    application = (
        Application.builder()
        .token(token)
        .post_init(setup_bot_commands)
        .build()
    )

    # Handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", start_command))
    application.add_handler(CommandHandler("applink", applink_command))
    application.add_handler(CommandHandler("appguide", appguide_command))
    application.add_handler(CommandHandler("support", support_command))
    application.add_handler(CommandHandler("reset", reset_command))
    application.add_handler(CommandHandler("newchat", reset_command))
    application.add_handler(CallbackQueryHandler(button_click_handler))
    # Any free text message -> OpenRouter AI auto-reply
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_text))

    logger.info("✅ Salone4D Customer Bot is running! Listening for user messages...")
    application.run_polling()


if __name__ == "__main__":
    main()
