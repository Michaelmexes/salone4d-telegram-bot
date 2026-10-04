"""
==========================================
SALONE 4D - Main Runner
==========================================
Scrape → Analyze → Format → Post လုပ်တဲ့ main pipeline
"""

import logging
import os
import sys
from datetime import datetime

# Windows console UTF-8 fix
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

import config
import scraper
import analyzer
import formatter
import bot

os.makedirs('data', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('data/salone4d.log', encoding='utf-8'),
    ]
)
logger = logging.getLogger(__name__)


def run():
    """Main pipeline: Scrape → Analyze → Format → Post"""
    logger.info("=" * 50)
    logger.info("🚀 SALONE 4D — Starting pipeline...")
    logger.info(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)

    # ── Step 1: Update data ──
    logger.info("\n📥 Step 1: Updating Singapore Pools data...")
    try:
        scraper.update_latest()
    except Exception as e:
        logger.error(f"❌ Scraping failed: {e}")
        return False

    # ── Step 2: Analyze hot numbers ──
    logger.info("\n📊 Step 2: Analyzing hot numbers...")
    try:
        hot_numbers = analyzer.analyze(top_n=config.TOP_N)
        if not hot_numbers:
            logger.error("❌ No hot numbers found. Data file စစ်ဆေးပါ။")
            return False
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        return False

    # ── Step 3: Format post ──
    logger.info("\n✍️  Step 3: Formatting post...")
    try:
        message = formatter.build_post(hot_numbers)
        logger.info("\n─── Preview ───────────────────────────")
        print(message)
        logger.info("───────────────────────────────────────\n")
    except Exception as e:
        logger.error(f"❌ Formatting failed: {e}")
        return False

    # ── Step 4: Send to Telegram ──
    logger.info("📤 Step 4: Sending to Telegram channel...")
    try:
        success = bot.send_message(message)
        if success:
            logger.info("✅ Pipeline completed successfully!")
        else:
            logger.error("❌ Failed to send message.")
        return success
    except Exception as e:
        logger.error(f"❌ Send failed: {e}")
        return False


def run_test():
    """Real API call မလုပ်ဘဲ post format ကိုသာ စစ်ဆေးသည်"""
    logger.info("🧪 Running TEST mode (no Telegram post)...")

    # Sample data သုံးပြမယ်
    sample_hot = [
        {'number': '4823', 'count': 45},
        {'number': '7156', 'count': 42},
        {'number': '3091', 'count': 39},
        {'number': '6748', 'count': 37},
        {'number': '2365', 'count': 35},
    ]

    message = formatter.build_post(sample_hot)
    print("\n─── Sample Post Preview ───────────────")
    print(message)
    print("───────────────────────────────────────\n")
    logger.info("✅ Test mode complete.")


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        run_test()
    else:
        run()
