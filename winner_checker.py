"""
==========================================
SALONE 4D - Lucky Winner Checker & Formatter
==========================================
၁။ Lucky numbers post တင်သည့်အခါ ဂဏန်းများကို သိမ်းဆည်းထားခြင်း
၂။ Result ထွက်သည့်အခါ ထီပေါက်စဉ်နှင့် တိုက်စစ်ခြင်း
၃။ ပေါက်ဂဏန်းရှိပါက ၅ မိနစ်အကြာတွင် အောင်ပွဲခံ Post ဖန်တီးပေးပို့ခြင်း
"""

import os
import json
import logging
from datetime import datetime
import config

logger = logging.getLogger(__name__)

LUCKY_NUMBERS_FILE = "data/posted_lucky_numbers.json"
LAST_POSTED_WINNER_FILE = "data/last_posted_winner_draw.txt"


def format_english_spaced(num_str: str) -> str:
    """'5821' ကို '5 8 2 1' အဖြစ် space ခွာသည်"""
    return " ".join(list(str(num_str)))


def to_myanmar_digits(text: str) -> str:
    """Arabic digits ကို Myanmar digits (၀-၉) သို့ ပြောင်းသည်"""
    result = ''
    for ch in str(text):
        result += config.MYANMAR_DIGITS.get(ch, ch)
    return result


def save_posted_lucky_numbers(hot_numbers: list, dt: datetime = None):
    """
    နေ့စဉ် Post တင်ခဲ့သော Lucky numbers များကို JSON ဖိုင်ထဲတွင် သိမ်းဆည်းသည်
    """
    if dt is None:
        dt = datetime.now()

    os.makedirs("data", exist_ok=True)

    # Extract 4-digit strings
    extracted_nums = []
    for item in hot_numbers:
        if isinstance(item, dict):
            num = str(item.get("number", "")).strip()
        else:
            num = str(item).strip()
        if len(num) == 4 and num.isdigit():
            extracted_nums.append(num)

    if not extracted_nums:
        logger.warning("No valid 4-digit numbers to save in posted lucky numbers.")
        return

    day_name = config.MYANMAR_DAYS.get(dt.strftime("%A"), dt.strftime("%A"))
    entry = {
        "date": dt.strftime("%Y-%m-%d"),
        "datetime": dt.strftime("%Y-%m-%d %H:%M:%S"),
        "day_name": day_name,
        "day_name_en": dt.strftime("%A"),
        "numbers": extracted_nums
    }

    # Load existing records
    records = []
    if os.path.exists(LUCKY_NUMBERS_FILE):
        try:
            with open(LUCKY_NUMBERS_FILE, "r", encoding="utf-8") as f:
                records = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load {LUCKY_NUMBERS_FILE}: {e}")
            records = []

    # Update today's record if already exists, else append
    updated = False
    for i, r in enumerate(records):
        if r.get("date") == entry["date"]:
            records[i] = entry
            updated = True
            break
    if not updated:
        records.append(entry)

    # Keep only 1 week (7 days) of records
    records = records[-7:]

    try:
        with open(LUCKY_NUMBERS_FILE, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ Saved {len(extracted_nums)} posted lucky numbers for {entry['date']} (Keeping 1 week/7 days)")
    except Exception as e:
        logger.error(f"❌ Failed to save posted lucky numbers: {e}")


def get_latest_posted_lucky_numbers() -> dict:
    """နောက်ဆုံး Post တင်ထားသော Lucky numbers စာရင်းကို ရယူသည်"""
    records = get_all_posted_lucky_numbers()
    if records:
        return records[-1]
    return None


def get_all_posted_lucky_numbers() -> list[dict]:
    """သိမ်းဆည်းထားသော Lucky numbers စာရင်းအားလုံးကို ဖတ်သည်"""
    if not os.path.exists(LUCKY_NUMBERS_FILE):
        return []
    try:
        with open(LUCKY_NUMBERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading lucky numbers file: {e}")
        return []


def check_winners(result_data: dict, lucky_numbers: list) -> list:
    """
    Singapore Pools Result နှင့် သိမ်းဆည်းထားသော Lucky numbers များကို တိုက်စစ်သည်
    Returns: [{'prize': '1st Prize', 'emoji': '🥇', 'number': '5821', 'order': 1}, ...]
    """
    if not result_data or not result_data.get("prizes"):
        return []

    prizes = result_data["prizes"]
    p_1st = str(prizes.get("1st", "")).strip()
    p_2nd = str(prizes.get("2nd", "")).strip()
    p_3rd = str(prizes.get("3rd", "")).strip()
    starters = [str(x).strip() for x in prizes.get("starter", [])]
    consolations = [str(x).strip() for x in prizes.get("consolation", [])]

    matches = []
    seen_matched_nums = set()

    for num in lucky_numbers:
        num = str(num).strip()
        if not num or num in seen_matched_nums:
            continue

        if num == p_1st:
            matches.append({"prize": "1st Prize", "emoji": "🥇", "number": num, "order": 1})
            seen_matched_nums.add(num)
        elif num == p_2nd:
            matches.append({"prize": "2nd Prize", "emoji": "🥈", "number": num, "order": 2})
            seen_matched_nums.add(num)
        elif num == p_3rd:
            matches.append({"prize": "3rd Prize", "emoji": "🥉", "number": num, "order": 3})
            seen_matched_nums.add(num)
        elif num in starters:
            matches.append({"prize": "Starter", "emoji": "🎖️", "number": num, "order": 4})
            seen_matched_nums.add(num)
        elif num in consolations:
            matches.append({"prize": "Consolation", "emoji": "🎖️", "number": num, "order": 5})
            seen_matched_nums.add(num)

    # Sort by prize hierarchy (1st -> 2nd -> 3rd -> Starter -> Consolation)
    matches.sort(key=lambda x: x["order"])
    return matches


def build_winner_post(result_data: dict, matches: list, matched_days_str: str = "ပြီးခဲ့တဲ့ရက်") -> str:
    """
    တောင်းဆိုထားသော ပုံစံအတိုင်း Lucky Winners Announcement Post ဖန်တီးသည်
    """
    if not matches:
        return ""

    dt = result_data.get("draw_date") or datetime.now()
    draw_no = result_data.get("draw_no_str", "Draw")
    draw_date_str = dt.strftime("%d %b %Y")  # e.g. "10 Oct 2026"
    draw_day_name = config.MYANMAR_DAYS.get(dt.strftime("%A"), dt.strftime("%A"))

    matched_count_mm = to_myanmar_digits(str(len(matches)))

    # Build prize lines
    prize_lines = []
    for m in matches:
        p_name = m["prize"].ljust(10)
        num_spaced = format_english_spaced(m["number"])
        prize_lines.append(f"{m['emoji']} {p_name} 👉 【 {num_spaced} 】")

    prizes_block = "\n".join(prize_lines)

    signature = getattr(config, "CHANNEL_SIGNATURE", "@Salone4dOfficial")

    post = (
        "🔴 WIN! 🎯 SALONE4D LUCKY WINNERS 🎯\n"
        f"📅 {draw_no} ({draw_date_str})\n\n"
        "ပေါက်တယ်ဆိုမှ တကယ် ပေါက်တာပါ! 💥\n"
        f"{matched_days_str}မှာ ထုတ်ပြန်ပေးခဲ့တဲ့ Lucky Numbers တွေထဲကမှ "
        f"{draw_day_name} Singapore Pools Draw မှာ ({matched_count_mm}) စုံ ကွက်တိ ဝင်သွားခဲ့ပါပြီ! ✨\n\n"
        f"{prizes_block}\n\n"
        "───────────────────────\n"
        "ကျန်ရှိနေသေးတဲ့ ဂဏန်းတွေရဲ့ Pattern Data များကိုလည်း ဆက်လက်လေ့လာပြီး နောက်တစ်ကြိမ်အတွက် အကောင်းဆုံး ပြင်ဆင်ပေးသွားပါမယ်။\n\n"
        "🏆 ကံထူးရှင်များအားလုံး ဂုဏ်ယူပါသည်! \n"
        f"{signature}"
    )

    return post


def get_last_posted_winner_draw() -> str:
    """နောက်ဆုံး Post တင်ပြီးသော Winner Draw အမှတ်အသားကို ဖတ်သည်"""
    if os.path.exists(LAST_POSTED_WINNER_FILE):
        try:
            with open(LAST_POSTED_WINNER_FILE, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            pass
    return ""


def set_last_posted_winner_draw(draw_no_str: str):
    """Post တင်ပြီးသော Winner Draw အမှတ်အသားကို မှတ်သားသည်"""
    try:
        with open(LAST_POSTED_WINNER_FILE, "w", encoding="utf-8") as f:
            f.write(draw_no_str.strip())
    except Exception as e:
        logger.warning(f"Error saving last posted winner draw: {e}")


def check_and_build_winner_post(result_data: dict) -> str:
    """
    Singapore Pools Draw Result နှင့် လွန်ခဲ့သော ၁ ပတ်စာ (၇ ရက်အတွင်း) တင်ခဲ့သော Lucky Numbers များကို စစ်ဆေး၍
    ပေါက်ဂဏန်းရှိပါက Post စာသား ဖန်တီးပေးသည်။
    (ပေါက်ဂဏန်း မရှိပါက (သို့မဟုတ်) ထို Draw အတွက် post တင်ပြီးသားဖြစ်ပါက None ပြန်သည်)
    """
    draw_no = result_data.get("draw_no_str", "")
    last_posted = get_last_posted_winner_draw()
    if draw_no and draw_no == last_posted:
        logger.info(f"ℹ️ Lucky winners for {draw_no} already posted previously. Skipping duplicate post.")
        return None

    all_records = get_all_posted_lucky_numbers()
    if not all_records:
        logger.info("No saved lucky numbers found to match.")
        return None

    # Draw ရက်စွဲ သို့မဟုတ် ယနေ့ရက်စွဲမှ လွန်ခဲ့သော ၇ ရက်အတွင်း (၁ ပတ်စာ) တင်ခဲ့သော စာရင်းများကိုသာ စစ်ထုတ်သည်
    dt_draw = result_data.get("draw_date") or datetime.now()
    from datetime import timedelta
    week_ago_str = (dt_draw - timedelta(days=7)).strftime("%Y-%m-%d")
    draw_date_str = dt_draw.strftime("%Y-%m-%d")

    records_in_week = [
        r for r in all_records
        if week_ago_str <= r.get("date", "") <= draw_date_str
    ]

    if not records_in_week:
        logger.info(f"No lucky numbers posted within the past 1 week ({week_ago_str} to {draw_date_str}).")
        return None

    # ၁ ပတ်စာအတွင်း ထုတ်ပြန်ခဲ့သော ဂဏန်းများနှင့် နေ့ရက်များကို စုစည်းသည်
    week_numbers = []
    matched_day_names = []
    for r in records_in_week:
        nums = r.get("numbers", [])
        week_numbers.extend(nums)

    # Winner တိုက်စစ်သည်
    matches = check_winners(result_data, week_numbers)
    if not matches:
        logger.info(f"No lucky number matched in {result_data.get('draw_no_str')} from past 1 week lucky posts.")
        return None

    # ဘယ်နေ့တွေက Lucky post နဲ့ ပေါက်ခဲ့လဲ နေ့အမည် စစ်ဆေးသည်
    matched_num_set = {m["number"] for m in matches}
    days_won = []
    for r in records_in_week:
        if any(n in matched_num_set for n in r.get("numbers", [])):
            dname = r.get("day_name", "")
            if dname and dname not in days_won:
                days_won.append(dname)

    if days_won:
        if len(days_won) == 1:
            matched_days_str = f"ပြီးခဲ့တဲ့ {days_won[0]}"
        else:
            matched_days_str = f"ပြီးခဲ့တဲ့ {', '.join(days_won)}"
    else:
        matched_days_str = "ပြီးခဲ့တဲ့တစ်ပတ်အတွင်း"

    logger.info(f"🎉 Found {len(matches)} lucky winner hits in {result_data.get('draw_no_str')} from past week!")
    post = build_winner_post(result_data, matches, matched_days_str)
    if post and draw_no:
        set_last_posted_winner_draw(draw_no)
    return post


