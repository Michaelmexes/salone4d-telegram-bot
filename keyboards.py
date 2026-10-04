# =============================================
#    Keyboard Builder - Updated Submenu System
# =============================================
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from texts import burmese as my_txt
from texts import english as en_txt


def get_text_module(lang):
    """Return text module based on language object."""
    return en_txt if lang == "en" else my_txt


def get_string(key, lang):
    """Safely get string from language module."""
    module = get_text_module(lang)
    return getattr(module, key, f"Missing [{key}]")


def main_menu_keyboard(lang):
    t = get_text_module(lang)
    keyboard = [
        [InlineKeyboardButton(t.BTN_STEP_APP, url="https://t.ly/pemBm")],
        [InlineKeyboardButton(t.BTN_APP_USAGE, callback_data="menu_app_usage")],
        [InlineKeyboardButton(t.BTN_VIBER_HELP, callback_data="menu_viber")],
    ]
    return InlineKeyboardMarkup(keyboard)


def app_usage_menu_keyboard(lang):
    t = get_text_module(lang)
    keyboard = [
        [InlineKeyboardButton(t.BTN_USAGE_REGISTER, callback_data="usage_register")],
        [InlineKeyboardButton(t.BTN_USAGE_BETTING,  callback_data="usage_betting")],
        [InlineKeyboardButton(t.BTN_USAGE_MONEY,    callback_data="usage_money")],
        [InlineKeyboardButton(t.BTN_USAGE_CHECK,    callback_data="usage_check_history")],
        [InlineKeyboardButton(t.BTN_BACK_MAIN,      callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def sub_answer_keyboard(lang):
    t = get_text_module(lang)
    keyboard = [
        [InlineKeyboardButton(t.BTN_BACK_SUBMENU, callback_data="menu_app_usage")],
        [InlineKeyboardButton(t.BTN_BACK_MAIN,    callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def back_keyboard(lang):
    t = get_text_module(lang)
    keyboard = [
        [InlineKeyboardButton(t.BTN_BACK_MAIN, callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def app_link_keyboard(lang):
    t = get_text_module(lang)
    keyboard = [
        [InlineKeyboardButton("📲 App ဒေါင်းလုဒ် ရယူရန်", url="https://t.ly/pemBm")],
        [InlineKeyboardButton(t.BTN_BACK_MAIN, callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def support_keyboard(lang):
    t = get_text_module(lang)
    keyboard = [
        [InlineKeyboardButton("💬 Viber ဆက်သွယ်ရန်", url="https://viber.click/959894169717")],
        [InlineKeyboardButton("✈️ Telegram Support", url="https://t.me/salone4DAdmin")],
        [InlineKeyboardButton(t.BTN_BACK_MAIN, callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)