"""
==========================================
SALONE 4D - Data Inspector Tool
==========================================
သိမ်းဆည်းထားသော Singapore Pools 4D Data များကို 
စစ်ဆေးကြည့်ရှုနိုင်သော script
"""

import sys
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import pandas as pd
import config

def inspect(date_query=None, number_query=None):
    try:
        df = pd.read_csv(config.DATA_FILE, dtype={'number': str})
    except Exception as e:
        print(f"Error loading {config.DATA_FILE}: {e}")
        return

    print("=" * 60)
    print("📊 SINGAPORE POOLS 4D - DATA INSPECTION REPORT")
    print("=" * 60)
    print(f"📁 Data File     : {config.DATA_FILE}")
    print(f"🔢 Total Records : {len(df):,} 条 records")
    print(f"📅 Date Range    : {df['date'].dropna().min()} to {df['date'].dropna().max()}")
    print("\n🏆 Prize Types Distribution:")
    print(df['prize_type'].value_counts().to_string())
    print("=" * 60)

    # Search by Date
    if date_query:
        print(f"\n🔍 Results for Date: {date_query}")
        sub = df[df['date'].astype(str).str.contains(date_query)]
        if sub.empty:
            print("  No records found for this date.")
        else:
            print(sub.to_string(index=False))

    # Search by Number
    if number_query:
        print(f"\n🔍 History for 4D Number: {number_query}")
        sub = df[df['number'] == str(number_query)]
        if sub.empty:
            print(f"  Number '{number_query}' has never been drawn since 2023.")
        else:
            print(f"  Appeared {len(sub)} times:")
            print(sub.to_string(index=False))

    # Show Latest 5 Draws
    print("\n📋 Latest Draws Sample (15 records):")
    print(df.tail(15).to_string(index=False))
    print("=" * 60)

if __name__ == '__main__':
    # CLI parameters: python inspect_data.py [date] [number]
    date_arg = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != '-' else None
    num_arg = sys.argv[2] if len(sys.argv) > 2 else None
    inspect(date_arg, num_arg)
