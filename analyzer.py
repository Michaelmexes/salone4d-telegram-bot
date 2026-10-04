"""
==========================================
SALONE 4D - Lucky Number Generator & Analyzer
==========================================
၁။ Totally Random (Cryptographically Secure OS Random) ဖြင့် 
   ဂဏန်းများကို စစ်မှန်စွာ ကွဲပြားပြီး သဘာဝကျကျ ရွေးချယ်ခြင်း
၂။ ထပ်ခါတလဲလဲ ဂဏန်းများ (ဥပမာ 9990, 5551 စသော repetitive pattern များ) ကို 
   စစ်ဆေးပြီး စစ်မှန်သော 4D ပေါက်ဂဏန်း သဘာဝအတိုင်း မျှတစွာ ကွဲပြားစေခြင်း
၃။ သမိုင်းတစ်လျှောက် ဆုကြီး (သို့) ဆုသေး ၅ ကြိမ်နှင့်အထက် ပေါက်ထားသော 
   အလွန်အရှိန်ကောင်းသည့် အထူးဂဏန်း (၁) စုံ သေချာပေါက် ပါဝင်စေခြင်း
၄။ Singapore Pools သမိုင်းကြောင်းမှ ဆုကြီး/ဆုသေး ထွက်ကြိမ် ပြန်လည်စစ်ဆေးပြသခြင်း
"""

import os
import random
import logging
from datetime import datetime, date
import pandas as pd

import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_data() -> pd.DataFrame:
    """CSV မှ data load လုပ်သည်"""
    try:
        df = pd.read_csv(config.DATA_FILE, dtype={'number': str})
        df['number'] = df['number'].astype(str).str.zfill(4)
        return df
    except FileNotFoundError:
        logger.error(f"❌ Data file not found: {config.DATA_FILE}")
        return pd.DataFrame()


def get_stats_for_number(num: str, df: pd.DataFrame) -> dict:
    """ဂဏန်းတစ်ခု၏ ဆုကြီး နှင့် ဆုသေး ထွက်ကြိမ်အရေအတွက်ကို စစ်ဆေးသည်"""
    major_count = 0
    minor_count = 0
    total_count = 0

    if not df.empty:
        matches = df[df['number'] == num]
        total_count = len(matches)
        for _, row in matches.iterrows():
            pt = str(row.get('prize_type', ''))
            if pt in ['1st', '2nd', '3rd']:
                major_count += 1
            elif pt in ['Starter', 'Consolation']:
                minor_count += 1

    return {
        'number': num,
        'major_count': major_count,
        'minor_count': minor_count,
        'total_count': total_count
    }


def is_pattern_repetitive(num: str) -> bool:
    """
    ၃ လုံးထပ်၊ ၄ လုံးထပ် (ဥပမာ 9990, 5551, 0000) စသော 
    ထူးဆန်းသည့် pattern များကို ပုံမှန် random ထဲတွင် မပါစေရန် စစ်ထုတ်သည်
    """
    # ၄ လုံးစလုံးတူနေခြင်း
    if len(set(num)) == 1:
        return True
    # ၃ လုံး ထပ်တူကျနေခြင်း (ဥပမာ 9990, 0999, 5551)
    for digit in num:
        if num.count(digit) >= 3:
            return True
    return False


def generate_lucky_numbers(df: pd.DataFrame, top_n: int = None) -> list[dict]:
    """
    Totally Random (True Random) ဖြင့် ဂဏန်း ၅ စုံ ထုတ်ပေးသည်။
    - အနည်းဆုံး ၁ စုံသည် ဆုကြီး (သို့) ဆုသေး ၅ ကြိမ်အထက် ထွက်ဖူးသော ဂဏန်း ဖြစ်ရမည်။
    - ကျန်ဂဏန်းများသည် ဆင်တူယိုးမှား မဖြစ်စေဘဲ စစ်မှန်သော Random ဖြစ်ရမည်။
    """
    if top_n is None:
        top_n = config.TOP_N

    # System Random (Hardware entropy / True Random)
    sec_random = random.SystemRandom()

    chosen_numbers = []

    # ၁။ ဆုကြီး (သို့) ဆုသေး ၅ ကြိမ်နှင့်အထက် ရှိသော pool ထဲမှ ၁ စုံ သေချာပေါက် ရွေးထုတ်ခြင်း
    if not df.empty:
        counts = df.groupby(['number', 'prize_type']).size().unstack(fill_value=0)
        major_sum = pd.Series(0, index=counts.index)
        for pt in ['1st', '2nd', '3rd']:
            if pt in counts.columns:
                major_sum += counts[pt]

        minor_sum = pd.Series(0, index=counts.index)
        for pt in ['Starter', 'Consolation']:
            if pt in counts.columns:
                minor_sum += counts[pt]

        # ၅ ကြိမ်နှင့်အထက် ပေါက်ထားသော High Performer ဂဏန်းများ
        high_perf_pool = counts[(major_sum >= 5) | (minor_sum >= 5)].index.tolist()
        if high_perf_pool:
            special_num = sec_random.choice(high_perf_pool)
            chosen_numbers.append(special_num)
            logger.info(f"🌟 Guaranteed 5+ Prize Number selected: {special_num}")

    # ၂။ ကျန်ရှိသော ဂဏန်းများကို Totally Random ဖြင့် ကွဲပြားစွာ ရွေးထုတ်ခြင်း
    attempts = 0
    while len(chosen_numbers) < top_n and attempts < 1000:
        attempts += 1
        num = f"{sec_random.randint(0, 9999):04d}"

        # ဆင်တူယိုးမှား (3-digit repeat) များ နှင့် ထပ်နေသော ဂဏန်းများကို ရှောင်ကြဉ်သည်
        if num in chosen_numbers or is_pattern_repetitive(num):
            continue

        chosen_numbers.append(num)

    # အစဉ်လိုက် ရောသမမွှေနှောက်သည်
    sec_random.shuffle(chosen_numbers)

    # ၃။ ဂဏန်းတစ်ခုချင်းစီ၏ Singapore Pools ထွက်ကြိမ် stats များကို ပြန်စစ်သည်
    results = [get_stats_for_number(num, df) for num in chosen_numbers]

    logger.info(f"✨ Final 5 Totally Random Lucky Numbers: {[r['number'] for r in results]}")
    return results


def analyze(top_n: int = None) -> list[dict]:
    """Main function called by pipeline"""
    df = load_data()
    return generate_lucky_numbers(df, top_n=top_n)


if __name__ == '__main__':
    items = analyze()
    for item in items:
        print(f"  {item['number']} -> ဆုကြီး: {item['major_count']} ကြိမ် | ဆုသေး: {item['minor_count']} ကြိမ်")
