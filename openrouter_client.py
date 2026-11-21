import logging
import re
import requests
import config

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
    "HTTP-Referer": "https://salone4d.com",
    "X-Title": "Salone4D Customer Bot",
    "Content-Type": "application/json"
}


def clean_ai_response(content: str) -> str:
    """Strip out chain-of-thought, reasoning tags, and analysis preambles."""
    if not content:
        return ""

    # Remove <think>...</think> tags if model uses them
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)

    # If the response starts with "Here's a thinking process:" or similar analysis preamble
    if "Here's a thinking process:" in content:
        parts = content.split("Here's a thinking process:")
        content = parts[0].strip() or parts[-1].strip()

    return content.strip()


def get_ai_reply(user_message: str, conversation_history: list = None) -> str:
    """
    Get customer service reply from OpenRouter using DeepSeek models.
    Supports multi-turn conversation memory and suppression of reasoning tokens.
    """
    system_prompt = getattr(
        config,
        "AI_SYSTEM_PROMPT",
        (
            "You are the official Customer Service AI Assistant for Salone4D Lottery Service.\n"
            "Bot Structure & FAQs:\n"
            "  1. 4D App လေးသွင်းပါ (Link: https://t.ly/pemBm or www.salone4d.com)\n"
            "  2. 4D App သုံးနည်း:\n"
            "     2.1 Register / Login ဝင်နည်း: အကောင့်လုပ်မည် သို့သွားပြီး နာမည်၊ ဖုန်း၊ password ဖြည့်သွင်း၍ ဖွင့်ပါ။\n"
            "     2.2 4D ထိုးနည်း: App ရှိ 'Buy' ကိုနှိပ်ပါ၊ ရက်စွဲနှင့် အမျိုးအစား (4D/Sweep) ရွေးချယ်ပြီး မိမိကြိုက်သောဂဏန်းများရွေးပါ။\n"
            "     2.3 ငွေသွင်း/ငွေထုတ်နည်း: 'Cash' > 'ငွေသွင်း'/'ငွေထုတ်' သို့သွားပါ။ KBZPay, WaveMoney ဖြင့် အနည်းဆုံး ကျပ် ၁,၀၀၀ သွင်း/ထုတ်နိုင်ပါသည်။\n"
            "     2.4 ထိုးထားတာပြန်စစ်နည်း: 'Record' သို့မဟုတ် 'History' မီနူးတွင် ထိုးထားသည့်လက်မှတ်များကို ပြန်လည်စစ်ဆေးနိုင်ပါသည်။\n"
            "  3. ဆက်သွယ်ရန် / Viber: +95 9 894 169 717 (https://viber.click/959894169717)\n"
            "Rules:\n"
            "  - အရေးကြီးသည်: အမြဲတမ်း သဘာဝကျပြီး ယဉ်ကျေးပျူငှာသော မြန်မာဘာသာစကားဖြင့်သာ ဖြေကြားပေးရပါမည်။ အင်္ဂလိပ်လို လုံးဝ မဖြေရပါ။ (STRICT: Reply ONLY in Myanmar/Burmese language. NEVER reply in English).\n"
            "  - User ၏ အမည်၊ ယခင်မေးခွန်းများနှင့် အကြောင်းအရာများကို အမြဲမှတ်မိနေပြီး ဆက်စပ်ဖြေကြားပေးပါ။\n"
            "  - အဖြေများကို တိုတိုရှင်းရှင်း၊ ဖော်ရွေစွာနှင့် အထောက်အကူပြုအောင် မြန်မာလိုသာ ဖြေပါ။\n"
            "  - မေးခွန်းကို တိုက်ရိုက်ဖြေပါ၊ internal thinking သို့မဟုတ် English analysis စာသားများ လုံးဝမထည့်ပါနှင့်။"
        )
    )

    models_to_try = getattr(
        config,
        "OPENROUTER_MODELS",
        [
            "baidu/ernie-5.5-flash-preview:free",
            "google/gemma-4-26b-a4b-it:free",
            "google/gemma-4-31b-it:free",
            "recursive/flint-v1.0:free",
            "openrouter/free"
        ]
    )

    # Format full messages payload including memory history
    if conversation_history:
        chat_messages = [{"role": "system", "content": system_prompt}] + conversation_history
    else:
        chat_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

    for model in models_to_try:
        try:
            payload = {
                "model": model,
                "messages": chat_messages,
                "max_tokens": 500,
                "temperature": 0.5,
            }

            resp = requests.post(OPENROUTER_URL, headers=HEADERS, json=payload, timeout=15)
            if resp.status_code == 200:
                result_json = resp.json()
                choices = result_json.get("choices", [])
                if choices:
                    msg = choices[0].get("message", {})
                    content = msg.get("content") or ""
                    cleaned = clean_ai_response(content)
                    if cleaned:
                        logger.info(f"OpenRouter success with model: {model}")
                        return cleaned
            else:
                logger.warning(f"Model {model} returned status {resp.status_code}")

        except Exception as e:
            logger.warning(f"Error querying model {model}: {e}")

    # Fallback message if all free models are temporarily busy
    return (
        "မင်္ဂလာပါခင်ဗျာ 🙏\n"
        "လောလောဆယ် AI စနစ် အနည်းငယ် မအားလပ်သေးပါသဖြင့် အောက်ပါ Main Menu ခလုတ်များမှတစ်ဆင့် အချက်အလက်များကို ကြည့်ရှုနိုင်ပါသည် 👇\n\n"
        "အသေးစိတ် တိုက်ရိုက်မေးမြန်းလိုပါက Viber: +95 9 894 169 717 သို့ ဆက်သွယ်နိုင်ပါသည်။"
    )


def get_chatechat_ai_reply(user_message: str, conversation_history: list = None) -> str:
    """
    Get simple customer service AI reply for ChateChat.
    Keeps answers very short, concise, and focused strictly on ChateChat.
    """
    system_prompt = getattr(
        config,
        "CHATECHAT_AI_SYSTEM_PROMPT",
        (
            "You are the official simple Customer Care AI Assistant for ChateChat (online chat and messaging application).\n"
            "ChateChat Details:\n"
            "  - Android APK Download Link: https://tinyurl.com/chatechat-app\n"
            "  - Web App (Browser access): https://chatechat.onrender.com\n"
            "  - Supported devices: Android phones (via APK) and any browser on PC/Mobile (Web App).\n"
            "  - Free to use: ChateChat is 100% free to chat, call and message.\n"
            "  - Account: Users can easily sign up inside the App or Web App with their username/phone.\n"
            "Rules:\n"
            "  - STRICT: Answer ONLY in natural, polite Myanmar/Burmese language. Never reply in English.\n"
            "  - Keep answers VERY SHORT and simple (1 or 2 sentences only).\n"
            "  - ONLY answer simple questions related to ChateChat (downloading, web app, basic account usage).\n"
            "  - If the question is outside ChateChat or too complex, politely say that you only assist with ChateChat app and guide them to use the APK or Web App.\n"
            "  - Do NOT output chain of thought or internal reasoning. Output only the final response in Burmese."
        )
    )

    models_to_try = getattr(
        config,
        "OPENROUTER_MODELS",
        [
            "baidu/ernie-5.5-flash-preview:free",
            "google/gemma-4-26b-a4b-it:free",
            "google/gemma-4-31b-it:free",
            "recursive/flint-v1.0:free",
            "openrouter/free"
        ]
    )

    if conversation_history:
        chat_messages = [{"role": "system", "content": system_prompt}] + conversation_history
    else:
        chat_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

    for model in models_to_try:
        try:
            payload = {
                "model": model,
                "messages": chat_messages,
                "max_tokens": 400,
                "temperature": 0.4,
            }
            resp = requests.post(OPENROUTER_URL, headers=HEADERS, json=payload, timeout=12)
            if resp.status_code == 200:
                result_json = resp.json()
                choices = result_json.get("choices", [])
                if choices:
                    msg = choices[0].get("message", {})
                    content = msg.get("content") or ""
                    cleaned = clean_ai_response(content)
                    if cleaned:
                        logger.info(f"ChateChat OpenRouter success with model: {model}")
                        return cleaned
            else:
                logger.warning(f"ChateChat model {model} returned status {resp.status_code}")
        except Exception as e:
            logger.warning(f"ChateChat error querying model {model}: {e}")

    return ""

