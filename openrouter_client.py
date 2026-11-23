import logging
import os
import re
import requests
import config

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {getattr(config, 'OPENROUTER_API_KEY', '')}",
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


_gemini_available = True


def call_gemini_api(system_prompt: str, user_message: str, conversation_history: list = None) -> str:
    """Direct Google Gemini REST API integration for fast, reliable replies."""
    global _gemini_available
    if not _gemini_available:
        return ""

    gemini_key = getattr(config, "GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
    if not gemini_key:
        return ""

    models = ["gemini-2.5-flash", "gemini-1.5-flash"]
    for m in models:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={gemini_key}"
            contents = []
            if conversation_history:
                for h in conversation_history:
                    role = "model" if h.get("role") == "assistant" else "user"
                    contents.append({"role": role, "parts": [{"text": h.get("content", "")}]})
            contents.append({"role": "user", "parts": [{"text": user_message}]})

            payload = {
                "system_instruction": {"parts": [{"text": system_prompt}]},
                "contents": contents,
                "generationConfig": {
                    "temperature": 0.4,
                    "maxOutputTokens": 600
                }
            }
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                cands = data.get("candidates", [])
                if cands:
                    text = cands[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    cleaned = clean_ai_response(text)
                    if cleaned:
                        logger.info(f"Gemini success with model: {m}")
                        return cleaned
            elif resp.status_code == 403:
                logger.warning("Gemini API free tier not available for this key (403). Bypassing Gemini to use OpenRouter.")
                _gemini_available = False
                return ""
            else:
                logger.warning(f"Gemini {m} returned {resp.status_code}: {resp.text[:150]}")
        except Exception as e:
            logger.warning(f"Gemini {m} error: {e}")

    return ""


def smart_fallback_reply(user_message: str) -> str:
    """
    Intelligent intent fallback for common customer questions and greetings
    when upstream AI providers are temporarily slow or rate-limited.
    """
    t = (user_message or "").lower().strip()

    # Greetings
    greetings = ["hi", "hello", "hey", "မင်္ဂလာပါ", "ဟိုင်း", "ဟဲလို", "နေကောင်းလား", "ဆလိုင်း", "mingalarpar", "mingalaba"]
    if any(t == g or t.startswith(g + " ") for g in greetings):
        return (
            "မင်္ဂလာပါခင်ဗျာ 🙏 Salone4D Customer Service မှ ကြိုဆိုပါတယ်။\n"
            "လူကြီးမင်း သိရှိလိုသည်များကို မေးမြန်းနိုင်ပါသည်ခင်ဗျာ (ဥပမာ- အကောင့်ဖွင့်နည်း၊ 4D ထိုးနည်း၊ ငွေသွင်းငွေထုတ်နည်း)။\n\n"
            "အောက်ပါ Main Menu ခလုတ်များမှတစ်ဆင့်လည်း အချက်အလက်များကို ချက်ချင်း ကြည့်ရှုနိုင်ပါသည် 👇"
        )

    # Asking if AI is working / Bot query
    if any(k in t for k in ["ai", "bot", "ဘော့", "ပြောလို့ရလား", "ပြောမရ", "ပြောလို့မရ", "စကားပြော", "မေးလို့ရလား", "ဖြေပေး"]):
        return (
            "မင်္ဂလာပါခင်ဗျာ 🙏 Salone4D AI Customer Service မှ ကြိုဆိုပါတယ်။\n"
            "ကျွန်တော့်ကို Salone4D အကောင့်ဖွင့်နည်း၊ 4D ထိုးနည်း၊ ငွေသွင်း/ငွေထုတ်နည်း စသည့် သိလိုသည်များကို တိုက်ရိုက် မေးမြန်းနိုင်ပါသည်ခင်ဗျာ။"
        )

    # Register / Account
    if any(k in t for k in ["အကောင့်", "ဖွင့်", "register", "login", "ဝင်နည်း", "အကောင့်"]):
        return (
            "📝 <b>Salone4D အကောင့်ဖွင့်နည်း / Login ဝင်နည်း:</b>\n\n"
            "❶ <b>အကောင့်ဖွင့်ရန်:</b> App ကိုဖွင့်ပြီး 'အကောင့်လုပ်မည်' သို့သွားကာ အမည်၊ ဖုန်းနံပါတ်၊ Password ဖြည့်သွင်း၍ ဖွင့်နိုင်ပါသည်။\n"
            "❷ <b>Login ဝင်ရန်:</b> အကောင့်ဖွင့်ထားသော ဖုန်းနံပါတ်နှင့် Password ဖြင့် ဝင်ရောက်နိုင်ပါသည်။"
        )

    # Betting / How to play 4D
    if any(k in t for k in ["ထိုး", "4d", "ဂဏန်း", "ဝယ်", "buy"]):
        return (
            "🎰 <b>Salone4D ထိုးနည်း:</b>\n\n"
            "• App ၏ အလယ်ဗဟိုရှိ <b>'Buy'</b> ခလုတ်ကို နှိပ်ပါ\n"
            "• ရက်စွဲနှင့် ထီအမျိုးအစား (4D / Sweep) ရွေးချယ်ပါ\n"
            "• မိမိကြိုက်နှစ်သက်ရာ ဂဏန်းများ ရွေးချယ်ပြီး 'ထည့်မည်' နှိပ်၍ အတည်ပြုနိုင်ပါသည်ခင်ဗျာ။"
        )

    # Cash / Deposit / Withdraw
    if any(k in t for k in ["ငွေ", "သွင်း", "ထုတ်", "kpay", "wave", "cash"]):
        return (
            "💳 <b>ငွေသွင်း / ငွေထုတ်နည်း:</b>\n\n"
            "❶ <b>ငွေသွင်း:</b> 'Cash' > 'ငွေသွင်း' သို့သွားပြီး KBZPay, WaveMoney ဖြင့် အနည်းဆုံး ကျပ် ၁,၀၀၀ စတင် သွင်းနိုင်ပါသည်။\n"
            "❷ <b>ငွေထုတ်:</b> 'Cash' > 'ငွေထုတ်' တွင် ငွေလက်ခံမည့် ဖုန်းနံပါတ်နှင့် ပမာဏဖြည့်သွင်း၍ ထုတ်ယူနိုင်ပါသည်။"
        )

    # App download link
    if any(k in t for k in ["app", "link", "apk", "ဒေါင်း", "down", "ဆော့ဝဲ"]):
        app_url = getattr(config, "APP_LINK", "https://t.ly/pemBm")
        return (
            "📲 <b>Salone4D Application ရယူရန်:</b>\n\n"
            f"🔗 Download Link: {app_url}\n"
            "🌐 Website: www.salone4d.com"
        )

    # Results / Draw check
    if any(k in t for k in ["ပေါက်စဉ်", "ရလဒ်", "ထွက်", "result", "စစ်"]):
        return (
            "🔍 <b>ထိုးထားတာ ပြန်စစ်နည်း:</b>\n\n"
            "ဝယ်ယူထားသော ထီလက်မှတ်များနှင့် ထိုးဂဏန်းများကို App ထဲရှိ <b>'Record'</b> သို့မဟုတ် <b>'History'</b> မီနူးတွင် စစ်ဆေးနိုင်ပါသည်ခင်ဗျာ။"
        )

    # Contact / Support
    if any(k in t for k in ["ဆက်သွယ်", "viber", "admin", "ဖုန်း", "call"]):
        return (
            "📞 <b>ဆက်သွယ်ရန်:</b>\n\n"
            "💬 Viber: +95 9 894 169 717\n"
            "✈️ Telegram: @salone4DAdmin"
        )

    # General polite response
    return (
        "မင်္ဂလာပါခင်ဗျာ 🙏\n"
        "လူကြီးမင်း မေးမြန်းလိုသည်များကို အောက်ပါ Main Menu ခလုတ်များမှတစ်ဆင့် ရွေးချယ်ကြည့်ရှုနိုင်သလို တိုက်ရိုက်လည်း မေးမြန်းနိုင်ပါသည်ခင်ဗျာ 👇\n\n"
        "အသေးစိတ် တိုက်ရိုက် မေးမြန်းလိုပါက Viber: +95 9 894 169 717 သို့ ဆက်သွယ်နိုင်ပါသည်။"
    )


def get_ai_reply(user_message: str, conversation_history: list = None) -> str:
    """
    Get customer service reply for Salone4D:
    1. Instant match for standard greetings and AI status queries (0ms latency)
    2. Try Gemini API if key is present
    3. Try OpenRouter API with verified free models (fast 5s timeout)
    4. Intelligent intent fallback to always provide a helpful, polite Myanmar reply
    """
    t = (user_message or "").lower().strip()

    # Fast-path 1: Greetings (Instant 0ms response)
    greetings = ["hi", "hello", "hey", "မင်္ဂလာပါ", "ဟိုင်း", "ဟဲလို", "နေကောင်းလား", "ဆလိုင်း", "mingalarpar", "mingalaba"]
    if any(t == g or t.startswith(g + " ") for g in greetings):
        return (
            "မင်္ဂလာပါခင်ဗျာ 🙏 Salone4D Customer Service မှ ကြိုဆိုပါတယ်။\n"
            "လူကြီးမင်း သိရှိလိုသည်များကို မေးမြန်းနိုင်ပါသည်ခင်ဗျာ (ဥပမာ- အကောင့်ဖွင့်နည်း၊ 4D ထိုးနည်း၊ ငွေသွင်းငွေထုတ်နည်း)။\n\n"
            "အောက်ပါ Main Menu ခလုတ်များမှတစ်ဆင့်လည်း အချက်အလက်များကို ချက်ချင်း ကြည့်ရှုနိုင်ပါသည် 👇"
        )

    # Fast-path 2: Asking if AI is working / Bot query
    if any(k in t for k in ["ai", "bot", "ဘော့", "ပြောလို့ရလား", "ပြောမရ", "ပြောလို့မရ", "စကားပြော", "မေးလို့ရလား", "ဖြေပေး"]):
        return (
            "မင်္ဂလာပါခင်ဗျာ 🙏 Salone4D AI Customer Service မှ ကြိုဆိုပါတယ်။\n"
            "ကျွန်တော့်ကို Salone4D အကောင့်ဖွင့်နည်း၊ 4D ထိုးနည်း၊ ငွေသွင်း/ငွေထုတ်နည်း စသည့် သိလိုသည်များကို တိုက်ရိုက် မေးမြန်းနိုင်ပါသည်ခင်ဗျာ။"
        )

    system_prompt = getattr(config, "AI_SYSTEM_PROMPT", "")

    # Layer 1: Google Gemini API (if available)
    gemini_reply = call_gemini_api(system_prompt, user_message, conversation_history)
    if gemini_reply:
        return gemini_reply

    # Layer 2: OpenRouter API
    openrouter_key = getattr(config, "OPENROUTER_API_KEY", "")
    if openrouter_key:
        models_to_try = getattr(
            config,
            "OPENROUTER_MODELS",
            [
                "openrouter/free",
                "recursive/flint-v1.0:free",
                "liquid/lfm-3-1.7b:free",
            ]
        )[:3]

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
                    "temperature": 0.4,
                    "repetition_penalty": 1.15,
                }
                resp = requests.post(OPENROUTER_URL, headers=HEADERS, json=payload, timeout=6)
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
                    logger.warning(f"Model {model} returned status {resp.status_code}: {resp.text[:120]}")
            except Exception as e:
                logger.warning(f"Error querying model {model}: {e}")

    # Layer 3: Smart Intent Fallback
    return smart_fallback_reply(user_message)


def get_chatechat_ai_reply(user_message: str, conversation_history: list = None) -> str:
    """
    Get simple customer service AI reply for ChateChat.
    Keeps answers very short, concise, and focused strictly on ChateChat.
    """
    t = (user_message or "").lower().strip()
    apk_url = getattr(config, "CHATECHAT_APK_URL", "https://tinyurl.com/chatechat-app")
    webapp_url = getattr(config, "CHATECHAT_WEBAPP_URL", "https://chatechat.onrender.com")

    # Fast-path 0ms responses for standard ChateChat questions
    if any(k in t for k in ["hi", "hello", "မင်္ဂလာပါ", "ဟိုင်း", "ဟဲလို"]):
        return "မင်္ဂလာပါခင်ဗျာ 🙏 ChateChat မှ ကြိုဆိုပါတယ်။ ဘာများ ကူညီပေးရမလဲခင်ဗျာ။"
    if any(k in t for k in ["apk", "app", "download", "ဒေါင်း", "ဆော့ဝဲ"]):
        return f"ChateChat Android APK ကို {apk_url} တွင် အခမဲ့ ဒေါင်းလုဒ် ရယူနိုင်ပါသည်ခင်ဗျာ။"
    if any(k in t for k in ["web", "browser", "ကွန်ပျူတာ", "ဖုန်း"]):
        return f"Browser မှတစ်ဆင့် အသုံးပြုလိုပါက {webapp_url} သို့ တိုက်ရိုက် ဝင်ရောက် အသုံးပြုနိုင်ပါသည်ခင်ဗျာ။"
    if any(k in t for k in ["အခမဲ့", "ပိုက်ဆံ", "ဈေး", "free", "ကုန်ကျ"]):
        return "ဟုတ်ကဲ့ခင်ဗျာ ChateChat အသုံးပြုခြင်းသည် ၁၀၀% လုံးဝ အခမဲ့ ဖြစ်ပါသည်ခင်ဗျာ။"

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

    # Try Gemini if key is present
    gemini_reply = call_gemini_api(system_prompt, user_message, conversation_history)
    if gemini_reply:
        return gemini_reply

    # Try OpenRouter
    openrouter_key = getattr(config, "OPENROUTER_API_KEY", "")
    if openrouter_key:
        models_to_try = getattr(
            config,
            "OPENROUTER_MODELS",
            [
                "openrouter/free",
                "recursive/flint-v1.0:free",
                "liquid/lfm-3-1.7b:free",
            ]
        )[:3]

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
                    "temperature": 0.3,
                    "repetition_penalty": 1.15,
                }
                resp = requests.post(OPENROUTER_URL, headers=HEADERS, json=payload, timeout=6)
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
                    logger.warning(f"ChateChat model {model} returned status {resp.status_code}: {resp.text[:120]}")
            except Exception as e:
                logger.warning(f"ChateChat error querying model {model}: {e}")

    return (
        f"မင်္ဂလာပါခင်ဗျာ 🙏 ChateChat ကို Android App ({apk_url}) သို့မဟုတ် Web Browser ({webapp_url}) "
        "မှတစ်ဆင့် အခမဲ့ အသုံးပြုနိုင်ပါသည်ခင်ဗျာ။"
    )
