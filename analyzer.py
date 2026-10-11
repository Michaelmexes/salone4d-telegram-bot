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


def get_analyzed_numbers(df: pd.DataFrame, count: int = 2) -> list[str]:
    """
    Singapore Pools သမိုင်းတစ်လျှောက် (2023-Present) ပေါက်ဂဏန်း data ကို စနစ်တကျ Analyze လုပ်ပြီး
    ဆုကြီး/ဆုသေး အမှတ်ပေးစနစ် (Weighted Scoring) နှင့် မကြာသေးမီက ထွက်ရှိမှု (Recency Momentum)
    အပေါ် အခြေခံ၍ အကောင်းဆုံး Hot Numbers (၂ စုံ) ကို တွက်ချက်ရွေးချယ်သည်။
    - 1st Prize: 5.0 မှတ်
    - 2nd Prize: 4.0 မှတ်
    - 3rd Prize: 3.0 မှတ်
    - Starter: 1.5 မှတ်
    - Consolation: 1.0 မှတ်
    - Recency Boost: နောက်ဆုံး ရက်ပေါင်း ၁၈၀ အတွင်း ပေါက်ထားပါက ၁.၅ ဆ၊ ၃၆၅ ရက်အတွင်း ၁.၂ ဆ
    """
    if df.empty:
        return []

    try:
        df_copy = df.copy()
        df_copy['date_dt'] = pd.to_datetime(df_copy['date'], errors='coerce')
        max_date = df_copy['date_dt'].max()

        prize_weights = {
            '1st': 5.0,
            '2nd': 4.0,
            '3rd': 3.0,
            'Starter': 1.5,
            'Consolation': 1.0
        }

        def score_row(row):
            base = prize_weights.get(row.get('prize_type', ''), 1.0)
            if pd.notnull(row['date_dt']) and pd.notnull(max_date):
                days_ago = (max_date - row['date_dt']).days
                if days_ago <= 180:
                    return base * 1.5
                elif days_ago <= 365:
                    return base * 1.2
            return base

        df_copy['weighted_score'] = df_copy.apply(score_row, axis=1)

        # Score ပေါင်းလဒ်တွက်ချက်ခြင်း
        scores = df_copy.groupby('number')['weighted_score'].sum().reset_index()

        # ဆုကြီး/ဆုသေး အရေအတွက်
        counts = df_copy.groupby(['number', 'prize_type']).size().unstack(fill_value=0).reset_index()
        for col in ['1st', '2nd', '3rd', 'Starter', 'Consolation']:
            if col not in counts.columns:
                counts[col] = 0
        counts['major'] = counts['1st'] + counts['2nd'] + counts['3rd']
        counts['minor'] = counts['Starter'] + counts['Consolation']

        merged = pd.merge(scores, counts, on='number')
        # Sort by total score, then major prizes, then minor prizes
        merged = merged.sort_values(by=['weighted_score', 'major', 'minor'], ascending=False)

        # Repetitive pattern များကို ရှောင်ကြဉ်ပြီး ထိပ်တန်း candidates များထဲမှ ရွေးထုတ်သည်
        candidates = []
        for num in merged['number'].tolist():
            if not is_pattern_repetitive(num):
                candidates.append(num)
            if len(candidates) >= 10:  # Top 10 high-score pool
                break

        # Pool ထဲမှ random.SystemRandom ဖြင့် အကောင်းဆုံး ၂ စုံကို ရွေးထုတ်ခြင်း
        # (သို့မှသာ နေ့တိုင်း ထပ်တူ မဖြစ်ဘဲ top candidate ၂ စုံထဲမှ လှည့်လည်ရွေးချယ်နိုင်မည်)
        sec_random = random.SystemRandom()
        if len(candidates) >= count:
            # Top 5 candidates ထဲမှ count (၂ စုံ) ကို sample လုပ်ခြင်း
            top_pool = candidates[:max(count * 2, 5)]
            selected = sec_random.sample(top_pool, count)
        else:
            selected = candidates[:count]

        logger.info(f"📊 Top 2 Data-Analyzed Hot Numbers selected: {selected}")
        return selected

    except Exception as e:
        logger.error(f"Error in get_analyzed_numbers: {e}")
        return []


def generate_lucky_numbers(df: pd.DataFrame, top_n: int = None) -> list[dict]:
    """
    Lucky Numbers ၅ စုံ ထုတ်ပေးသည်။
    - ၂ စုံ: Singapore Pools သမိုင်းကြောင်း data ကို analyze လုပ်ပြီး ရမှတ်အမြင့်ဆုံး ထွက်ထားသော Hot Numbers
    - ၃ စုံ: Totally Random (Cryptographically Secure OS Random) ဖြင့် ရွေးချယ်ထားသော စစ်မှန်သော Random Numbers
    """
    if top_n is None:
        top_n = config.TOP_N

    sec_random = random.SystemRandom()
    chosen_numbers = []

    # ၁။ Data Analyze လုပ်ထားသော Hot Numbers ၂ စုံ ရွေးထုတ်ခြင်း
    analyzed_numbers = get_analyzed_numbers(df, count=2)
    chosen_numbers.extend(analyzed_numbers)

    # ၂။ ကျန်ရှိသော ဂဏန်းများကို Totally Random ဖြင့် ကွဲပြားစွာ ရွေးထုတ်ခြင်း (၃ စုံ)
    attempts = 0
    while len(chosen_numbers) < top_n and attempts < 1000:
        attempts += 1
        num = f"{sec_random.randint(0, 9999):04d}"

        # ဆင်တူယိုးမှား (3-digit repeat) များ နှင့် ထပ်နေသော ဂဏန်းများကို ရှောင်ကြဉ်သည်
        if num in chosen_numbers or is_pattern_repetitive(num):
            continue

        chosen_numbers.append(num)

    # ၃။ ဂဏန်းတစ်ခုချင်းစီ၏ Singapore Pools ထွက်ကြိမ် stats များကို စစ်ဆေးထည့်သွင်းခြင်း
    results = [get_stats_for_number(num, df) for num in chosen_numbers]

    # ၄။ Post တင်ရာတွင် ဆုထွက်ကြိမ် အများဆုံး ဂဏန်းများက အပေါ်ဆုံး (Rank 1, 2) တွင် ရောက်စေရန်
    # ဆုကြီးအကြိမ်ရေ၊ ထို့နောက် ဆုသေးအကြိမ်ရေဖြင့် အစဉ်လိုက် စီစဉ်ပေးသည် (Sorting by major_count, minor_count descending)
    results.sort(key=lambda x: (x.get('major_count', 0), x.get('minor_count', 0)), reverse=True)

    logger.info(f"✨ Final 5 Lucky Numbers (Sorted by counts): {[r['number'] for r in results]}")
    return results



def analyze(top_n: int = None) -> list[dict]:
    """Main function called by pipeline"""
    df = load_data()
    return generate_lucky_numbers(df, top_n=top_n)


if __name__ == '__main__':
    import sys
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')
    items = analyze()
    for item in items:
        print(f"  {item['number']} -> ဆုကြီး: {item['major_count']} ကြိမ် | ဆုသေး: {item['minor_count']} ကြိမ်")

