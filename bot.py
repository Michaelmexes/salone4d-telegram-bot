"""
==========================================
SALONE 4D - Telegram Bot
==========================================
Formatted post ကို Telegram Channel မှာ ပို့တဲ့ module
"""

import logging
import sys
import requests

# Windows console UTF-8 fix
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def send_message(text: str, token: str = None, channel_id: str = None) -> bool:
    """
    Telegram channel မှာ message ပို့သည်

    Parameters:
        text:       ပို့မည့် message text
        token:     8654662573:AAE_BPejDCDilNlF_pIvXWElhr3cO8o1Tb4 (None = config မှ ယူသည်)
        channel_id: t.me/salone4d (None = config မှ ယူသည်)

    Returns:
        True if successful, False otherwise
    """
    token      = token      or config.BOT_TOKEN
    channel_id = channel_id or config.CHANNEL_ID

    if token == "YOUR_BOT_TOKEN_HERE":
        logger.error("❌ Bot token မသတ်မှတ်ရသေးပါ။ config.py မှာ BOT_TOKEN ထည့်ပါ။")
        return False

    if channel_id == "YOUR_CHANNEL_ID_HERE":
        logger.error("❌ Channel ID မသတ်မှတ်ရသေးပါ။ config.py မှာ CHANNEL_ID ထည့်ပါ။")
        return False

    url     = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id':    channel_id,
        'text':       text,
        'parse_mode': 'HTML',
    }

    try:
        resp = requests.post(url, json=payload, timeout=15)
        data = resp.json()

        if data.get('ok'):
            logger.info(f"✅ Message sent successfully! Message ID: {data['result']['message_id']}")
            return True
        else:
            logger.error(f"❌ Telegram API Error: {data.get('description', 'Unknown error')}")
            return False

    except requests.exceptions.Timeout:
        logger.error("❌ Request timed out. Telegram API ကို ချိတ်ဆက်မရပါ။")
        return False
    except requests.exceptions.ConnectionError:
        logger.error("❌ Connection error. Internet ချိတ်ဆက်မှု စစ်ဆေးပါ။")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False


def test_bot() -> bool:
    """Bot connection ကို စမ်းသပ်သည်"""
    token = config.BOT_TOKEN
    if token == "YOUR_BOT_TOKEN_HERE":
        logger.error("❌ Bot token မသတ်မှတ်ရသေးပါ။")
        return False

    url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if data.get('ok'):
            bot_info = data['result']
            logger.info(f"✅ Bot connected: @{bot_info.get('username')} ({bot_info.get('first_name')})")
            return True
        else:
            logger.error(f"❌ Bot test failed: {data.get('description')}")
            return False
    except Exception as e:
        logger.error(f"❌ Bot test error: {e}")
        return False


if __name__ == '__main__':
    # Bot connection test
    print("🔍 Bot connection testing...")
    if test_bot():
        print("✅ Bot is ready!")
        # Test message ပို့ကြည့်မယ်
        test_msg = "🎯 Salone 4D Bot — Test Message\n✅ Bot is working correctly!"
        send_message(test_msg)
    else:
        print("❌ Bot connection failed. config.py ကို စစ်ဆေးပါ။")
