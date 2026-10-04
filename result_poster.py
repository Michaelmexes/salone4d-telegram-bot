"""
==========================================
SALONE 4D - Result Formatter & Fetcher
==========================================
Singapore Pools မှ နောက်ဆုံးထွက် 4D Result ကို ဆွဲယူပြီး 
Telegram post format အဖြစ် ပြုလုပ်ပေးသော module
"""

import requests
import logging
from bs4 import BeautifulSoup
from datetime import datetime
import config

logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.singaporepools.com.sg/',
}

TOP_DRAWS_URL = "https://www.singaporepools.com.sg/DataFileArchive/Lottery/Output/fourd_result_top_draws_en.html"


def fetch_latest_result() -> dict:
    """Singapore Pools မှ အသစ်ဆုံး 4D ထွက်ဂဏန်း အချက်အလက်များကို ဆွဲယူသည်"""
    try:
        r = requests.get(TOP_DRAWS_URL, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            logger.error(f"Failed to fetch top draws: HTTP {r.status_code}")
            return None

        soup = BeautifulSoup(r.text, 'html.parser')
        tables = soup.find_all('table')
        if len(tables) < 3:
            return None

        t0 = tables[0]
        th_date = t0.find('th', class_='drawDate')
        th_no = t0.find('th', class_='drawNumber')

        raw_date_str = th_date.get_text(strip=True) if th_date else "" # e.g. "Wed, 30 Sep 2026"
        draw_no_str = th_no.get_text(strip=True) if th_no else ""      # e.g. "Draw No. 5542"

        # Parse date
        dt = None
        try:
            parts = raw_date_str.split(',', 1)
            date_part = parts[1].strip() if len(parts) > 1 else parts[0].strip()
            dt = datetime.strptime(date_part, '%d %b %Y')
        except Exception:
            dt = datetime.now()

        prizes = {
            '1st': '',
            '2nd': '',
            '3rd': '',
            'starter': [],
            'consolation': []
        }

        # 1st, 2nd, 3rd from Table 0
        td_first = t0.find('td', class_='tdFirstPrize')
        td_second = t0.find('td', class_='tdSecondPrize')
        td_third = t0.find('td', class_='tdThirdPrize')

        if td_first: prizes['1st'] = td_first.get_text(strip=True)
        if td_second: prizes['2nd'] = td_second.get_text(strip=True)
        if td_third: prizes['3rd'] = td_third.get_text(strip=True)

        # Starter from Table 1
        t1 = tables[1]
        for td in t1.find_all('td'):
            val = td.get_text(strip=True)
            if len(val) == 4 and val.isdigit():
                prizes['starter'].append(val)

        # Consolation from Table 2
        t2 = tables[2]
        for td in t2.find_all('td'):
            val = td.get_text(strip=True)
            if len(val) == 4 and val.isdigit():
                prizes['consolation'].append(val)

        return {
            'draw_date': dt,
            'draw_no_str': draw_no_str,
            'prizes': prizes
        }

    except Exception as e:
        logger.error(f"Error extracting latest 4D result: {e}")
        return None


def format_english_spaced(num_str: str) -> str:
    """'3096' ကို '3 0 9 6' အဖြစ် English number ဖြင့် space ခွာသည်"""
    return " ".join(list(num_str))


def get_myanmar_date_str(dt: datetime) -> str:
    """Myanmar date format ပြုလုပ်သည်"""
    day_name = config.MYANMAR_DAYS.get(dt.strftime('%A'), dt.strftime('%A'))
    day_num = config.MYANMAR_DIGITS.get(str(dt.day).zfill(2)[0], '') + config.MYANMAR_DIGITS.get(str(dt.day).zfill(2)[1], '')
    month_name = config.MYANMAR_MONTHS.get(dt.month, str(dt.month))
    year_str = "".join([config.MYANMAR_DIGITS.get(c, c) for c in str(dt.year)])
    return f"{day_name} ၊ {day_num} {month_name} {year_str}"


def build_result_post(result_data: dict) -> str:
    """တောင်းဆိုထားသော ပုံစံ ၁ အတိုင်း Telegram post message ဖန်တီးသည်"""
    dt = result_data['draw_date']
    date_formatted = get_myanmar_date_str(dt)
    draw_no = result_data['draw_no_str'] # e.g. "Draw No. 5542"
    p = result_data['prizes']

    first_spaced = format_english_spaced(p['1st'])
    second_spaced = format_english_spaced(p['2nd'])
    third_spaced = format_english_spaced(p['3rd'])

    # Starter list (5 per line)
    starter = p['starter']
    line1_starter = " • ".join(starter[:5]) if len(starter) >= 5 else ""
    line2_starter = " • ".join(starter[5:10]) if len(starter) >= 10 else ""
    starter_text = f"{line1_starter}\n{line2_starter}" if line2_starter else line1_starter

    # Consolation list (5 per line)
    consolation = p['consolation']
    line1_cons = " • ".join(consolation[:5]) if len(consolation) >= 5 else ""
    line2_cons = " • ".join(consolation[5:10]) if len(consolation) >= 10 else ""
    cons_text = f"{line1_cons}\n{line2_cons}" if line2_cons else line1_cons

    post = (
        "🎯 SALONE4D 🎯\n"
        f"📅 {date_formatted}\n"
        f"🔢 {draw_no} ရလဒ်များ\n"
        "────────────────────\n\n"
        f"🥇 ပထမဆု   ➤  【 {first_spaced} 】\n"
        f"🥈 ဒုတိယဆု  ➤  【 {second_spaced} 】\n"
        f"🥉 တတိယဆု  ➤  【 {third_spaced} 】\n\n"
        "🎖️ Starter Prizes (အထူးဆု ၁၀ စုံ)\n"
        f"{starter_text}\n\n"
        "🎖️ Consolation Prizes (နှစ်သိမ့်ဆု ၁၀ စုံ)\n"
        f"{cons_text}\n\n"
        "────────────────────\n"
        "Singapore Pools 4D Official Result\n"
        "🍀 ကံထူးရှင်များအားလုံး ဂုဏ်ယူပါသည်! 🍀\n"
        f"{getattr(config, 'TELEGRAM_CHANNEL', '@mexes30salone')}"
    )
    return post


if __name__ == '__main__':
    data = fetch_latest_result()
    if data:
        print(build_result_post(data))
    else:
        print("Failed to fetch result.")
