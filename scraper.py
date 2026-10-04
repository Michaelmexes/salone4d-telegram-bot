"""
==========================================
SALONE 4D - Singapore Pools Data Scraper
==========================================
Singapore Pools 4D historical results ကို ဆွဲထုတ်ပြီး CSV မှာ သိမ်းတဲ့ module
"""

import os
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import pandas as pd
from datetime import datetime, date
from bs4 import BeautifulSoup

import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://www.singaporepools.com.sg/',
}

BASE_DATA_URL = "https://www.singaporepools.com.sg/DataFileArchive/Lottery/Output/"
SINGLE_DRAW_URL = "https://www.singaporepools.com.sg/en/product/pages/4d_results.aspx"


def parse_draw_container(container, draw_date_str=None) -> list[dict]:
    """Single draw container (သို့) Top draw table မှ prize numbers အားလုံး ထုတ်ယူသည်"""
    results = []
    tables = container.find_all('table')
    
    current_date = draw_date_str
    
    for table in tables:
        # Check header for date if not provided
        th_date = table.find('th', class_=lambda c: c and 'drawdate' in c.lower())
        if th_date:
            raw_d = th_date.get_text(strip=True) # e.g. "Wed, 30 Sep 2026"
            try:
                parts = raw_d.split(',', 1)
                date_part = parts[1].strip() if len(parts) > 1 else parts[0].strip()
                dt = datetime.strptime(date_part, '%d %b %Y').date()
                current_date = dt.isoformat()
            except Exception:
                pass

        # 1st, 2nd, 3rd Prize check
        td_first = table.find('td', class_='tdFirstPrize')
        td_second = table.find('td', class_='tdSecondPrize')
        td_third = table.find('td', class_='tdThirdPrize')

        if td_first and len(td_first.get_text(strip=True)) == 4:
            results.append({'date': current_date, 'prize_type': '1st', 'number': td_first.get_text(strip=True)})
        if td_second and len(td_second.get_text(strip=True)) == 4:
            results.append({'date': current_date, 'prize_type': '2nd', 'number': td_second.get_text(strip=True)})
        if td_third and len(td_third.get_text(strip=True)) == 4:
            results.append({'date': current_date, 'prize_type': '3rd', 'number': td_third.get_text(strip=True)})

        # Starter & Consolation check
        current_section = None
        for row in table.find_all('tr'):
            th = row.find('th')
            if th:
                th_text = th.get_text(strip=True)
                if 'Starter' in th_text:
                    current_section = 'Starter'
                elif 'Consolation' in th_text:
                    current_section = 'Consolation'

            if current_section:
                for td in row.find_all('td'):
                    val = td.get_text(strip=True)
                    if len(val) == 4 and val.isdigit():
                        results.append({
                            'date': current_date,
                            'prize_type': current_section,
                            'number': val
                        })
                        
    return results


def fetch_top_draws(session: requests.Session) -> list[dict]:
    """နောက်ဆုံးထွက်ထားသော draw (၆) ကြိမ် ရလဒ်များ ဆွဲယူသည်"""
    url = BASE_DATA_URL + 'fourd_result_top_draws_en.html'
    try:
        r = session.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            return parse_draw_container(soup)
    except Exception as e:
        logger.warning(f"Error fetching top draws: {e}")
    return []


def get_available_draw_list(session: requests.Session) -> list[dict]:
    """Singapore Pools မှ ရရှိနိုင်သော historical draw စာရင်းအားလုံးကို ရယူသည်"""
    url = BASE_DATA_URL + 'fourd_result_draw_list_en.html'
    draw_list = []
    try:
        r = session.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            for opt in soup.find_all('option'):
                qs = opt.get('querystring')
                draw_no = opt.get('value')
                text = opt.get_text(strip=True) # e.g. "Wed, 30 Sep 2026"
                if qs:
                    try:
                        parts = text.split(',', 1)
                        date_part = parts[1].strip() if len(parts) > 1 else parts[0].strip()
                        dt = datetime.strptime(date_part, '%d %b %Y').date()
                        iso_d = dt.isoformat()
                    except Exception:
                        iso_d = None
                    draw_list.append({
                        'draw_no': draw_no,
                        'querystring': qs,
                        'date_str': iso_d,
                        'raw_text': text
                    })
    except Exception as e:
        logger.error(f"Error fetching draw list: {e}")
    return draw_list


def fetch_single_draw(qs: str, draw_date_str: str, session: requests.Session) -> list[dict]:
    """ရက်စွဲတစ်ခုချင်းစီ၏ draw result ကို ရယူသည်"""
    url = f"{SINGLE_DRAW_URL}?{qs}"
    try:
        r = session.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            div = soup.find('div', class_='divSingleDraw')
            if div:
                return parse_draw_container(div, draw_date_str)
    except Exception as e:
        logger.warning(f"Failed to fetch draw {draw_date_str} ({qs}): {e}")
    return []


def load_existing_data() -> pd.DataFrame:
    """သိမ်းထားပြီးသား CSV data ကို load လုပ်သည်"""
    os.makedirs('data', exist_ok=True)
    if os.path.exists(config.DATA_FILE):
        try:
            df = pd.read_csv(config.DATA_FILE, dtype={'number': str})
            df['date'] = pd.to_datetime(df['date']).dt.date
            logger.info(f"✅ Loaded {len(df)} existing records from {config.DATA_FILE}.")
            return df
        except Exception as e:
            logger.warning(f"Error loading {config.DATA_FILE}: {e}")
    return pd.DataFrame(columns=['date', 'prize_type', 'number'])


def save_data(df: pd.DataFrame):
    """DataFrame ကို CSV မှာ သိမ်းသည်"""
    os.makedirs('data', exist_ok=True)
    df_save = df.copy()
    df_save['date'] = df_save['date'].astype(str)
    df_save.to_csv(config.DATA_FILE, index=False)
    logger.info(f"💾 Saved {len(df_save)} records → {config.DATA_FILE}")


def scrape_all(force_refresh: bool = False, max_workers: int = 5) -> pd.DataFrame:
    """
    2023 မှစ၍ ယနေ့အထိ Draw Data အားလုံးကို အပြည့်အစုံ ဆွဲယူ သိမ်းဆည်းသည်
    """
    existing_df = load_existing_data()
    scraped_dates = set()
    if not force_refresh and not existing_df.empty:
        scraped_dates = set(str(d) for d in existing_df['date'].unique())

    all_records = []
    
    with requests.Session() as session:
        # 1. Top draws (latest) အမြဲရယူ
        top_records = fetch_top_draws(session)
        if top_records:
            all_records.extend(top_records)

        # 2. Historical draw list ရယူ
        draw_list = get_available_draw_list(session)
        logger.info(f"📋 Total historical draws found on Singapore Pools: {len(draw_list)}")
        
        # Filter by year and existing
        from_year = config.SCRAPE_FROM_YEAR
        pending = []
        for item in draw_list:
            if item['date_str']:
                dt_obj = datetime.strptime(item['date_str'], '%Y-%m-%d').date()
                if dt_obj.year >= from_year and item['date_str'] not in scraped_dates:
                    pending.append(item)

        logger.info(f"📥 Draws to scrape (from {from_year} onward, missing): {len(pending)}")

        if pending:
            def worker(d_item):
                s = requests.Session()
                time.sleep(0.1)
                return fetch_single_draw(d_item['querystring'], d_item['date_str'], s)

            completed_count = 0
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(worker, item): item for item in pending}
                for f in as_completed(futures):
                    res = f.result()
                    if res:
                        all_records.extend(res)
                    completed_count += 1
                    if completed_count % 20 == 0 or completed_count == len(pending):
                        logger.info(f"  Progress: [{completed_count}/{len(pending)}] draws fetched...")

    if all_records:
        new_df = pd.DataFrame(all_records)
        new_df['date'] = pd.to_datetime(new_df['date']).dt.date
        combined = pd.concat([existing_df, new_df], ignore_index=True)
        combined = combined.dropna(subset=['number'])
        combined['number'] = combined['number'].astype(str)
        combined = combined.drop_duplicates(subset=['date', 'prize_type', 'number'])
        combined = combined.sort_values('date')
        save_data(combined)
        logger.info(f"✅ Scraping completed! Total unique records: {len(combined)}")
        return combined
    else:
        logger.info("✅ Data is already up-to-date.")
        return existing_df


def update_latest() -> pd.DataFrame:
    """နောက်ဆုံးထွက် draw အသစ်များကိုသာ update ပြုလုပ်သည်"""
    return scrape_all(force_refresh=False)


if __name__ == '__main__':
    df = scrape_all()
    print(df.tail(15))
