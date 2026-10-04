#!/usr/bin/env python3
# ==========================================================
#   Salone4D Service - Unified Runner for Render Cloud
#   Runs Flask Web Server + Auto Poster + Customer Care Bot + Keep-Alive
# ==========================================================

import os
import sys
import time
import logging
import threading
from datetime import datetime
import pytz
import requests
from flask import Flask, jsonify, render_template_string
import config

# Force UTF-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("RenderApp")
MYANMAR_TZ = pytz.timezone("Asia/Yangon")


# ══════════════════════════════════════════════════════════════
#   Flask Web Server (Keep-Alive & Health Monitoring)
# ══════════════════════════════════════════════════════════════
flask_app = Flask(__name__)

HTML_DASHBOARD = """
<!DOCTYPE html>
<html lang="my">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Salone4D Bot Server - Render Keep-Alive</title>
    <style>
        :root {
            --bg: #0f172a;
            --card-bg: #1e293b;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --accent: #10b981;
            --accent-glow: rgba(16, 185, 129, 0.2);
            --border: #334155;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body {
            background-color: var(--bg);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 1rem;
        }
        .container {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 2rem;
            max-width: 480px;
            width: 100%;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
            text-align: center;
        }
        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: var(--accent-glow);
            color: var(--accent);
            border: 1px solid var(--accent);
            padding: 6px 14px;
            border-radius: 9999px;
            font-size: 0.875rem;
            font-weight: 600;
            margin-bottom: 1.25rem;
        }
        .pulse-dot {
            width: 8px;
            height: 8px;
            background: var(--accent);
            border-radius: 50%;
            box-shadow: 0 0 10px var(--accent);
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.4; transform: scale(0.85); }
        }
        h1 { font-size: 1.5rem; margin-bottom: 0.5rem; font-weight: 700; }
        p.subtitle { color: var(--text-muted); font-size: 0.925rem; margin-bottom: 1.5rem; }
        .info-list {
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 1rem;
            text-align: left;
            margin-bottom: 1.5rem;
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
            font-size: 0.9rem;
        }
        .info-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .info-label { color: var(--text-muted); }
        .info-value { font-weight: 600; color: #e2e8f0; }
        .footer {
            font-size: 0.8rem;
            color: var(--text-muted);
            border-top: 1px solid var(--border);
            padding-top: 1rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="status-badge">
            <span class="pulse-dot"></span>
            Online & Keep-Alive Active
        </div>
        <h1>Salone4D Bot Server</h1>
        <p class="subtitle">Render Web Service • 24/7 Running</p>
        
        <div class="info-list">
            <div class="info-row">
                <span class="info-label">Target Channel</span>
                <span class="info-value">{{ channel }}</span>
            </div>
            <div class="info-row">
                <span class="info-label">AI Engine</span>
                <span class="info-value">OpenRouter Free Models</span>
            </div>
            <div class="info-row">
                <span class="info-label">Myanmar Time</span>
                <span class="info-value">{{ current_time }}</span>
            </div>
            <div class="info-row">
                <span class="info-label">Render Sleep Prevention</span>
                <span class="info-value" style="color: var(--accent);">Active (Self-Ping)</span>
            </div>
        </div>

        <div class="footer">
            Salone4D Official Telegram Bot Service
        </div>
    </div>
</body>
</html>
"""

@flask_app.route("/")
def home():
    now_mm = datetime.now(MYANMAR_TZ).strftime("%Y-%m-%d %I:%M:%S %p")
    return render_template_string(
        HTML_DASHBOARD,
        channel=getattr(config, "CHANNEL_ID", "@mexes30salone"),
        current_time=now_mm
    )

@flask_app.route("/ping")
@flask_app.route("/health")
def health():
    now_mm = datetime.now(MYANMAR_TZ).strftime("%Y-%m-%d %I:%M:%S %p")
    return jsonify({
        "status": "ok",
        "service": "salone4d-bot",
        "channel": getattr(config, "CHANNEL_ID", "@mexes30salone"),
        "myanmar_time": now_mm,
        "keep_alive": True,
        "timestamp": int(time.time())
    }), 200


def run_flask_server(port: int):
    """Run lightweight Flask web server."""
    # Suppress werkzeug request access logging to keep console clean
    import logging as py_logging
    w_logger = py_logging.getLogger("werkzeug")
    w_logger.setLevel(py_logging.ERROR)

    logger.info(f"🌐 Flask Keep-Alive Web Server started on port {port}")
    flask_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


def keep_alive_worker(port: int):
    """
    Periodically pings the Render Web Service URL to prevent it from entering Sleep Mode.
    Render free tier sleeps after 15 minutes of inactivity.
    This worker pings every 10 minutes (600 seconds).
    """
    time.sleep(20)  # Initial delay to let the Flask server bind
    while True:
        try:
            # Render automatically sets RENDER_EXTERNAL_URL (e.g., https://salone4d-bot.onrender.com)
            ext_url = os.getenv("RENDER_EXTERNAL_URL") or os.getenv("PING_URL")
            if ext_url:
                target = f"{ext_url.rstrip('/')}/ping"
                r = requests.get(target, timeout=15)
                logger.info(f"🔄 Keep-alive ping sent to {target} (Status: {r.status_code})")
            else:
                # If external URL is not set yet, ping locally
                target = f"http://127.0.0.1:{port}/ping"
                r = requests.get(target, timeout=5)
                logger.info(f"🔄 Local Keep-alive ping OK (Status: {r.status_code})")
        except Exception as e:
            logger.warning(f"⚠️ Keep-alive ping warning: {e}")

        # Sleep for 10 minutes (600s), comfortably before Render's 15min sleep timeout
        time.sleep(600)


def run_scheduler_job():
    """Run master scheduler in background thread."""
    try:
        import scheduler
        logger.info("⏰ Starting Salone4D Master Scheduler...")
        scheduler.start()
    except Exception as e:
        logger.error(f"❌ Scheduler crashed: {e}", exc_info=True)


def run_customer_bot():
    """Run Telegram Customer Care Bot."""
    try:
        import customer_bot
        logger.info("🤖 Starting Salone4D Customer Care Bot...")
        customer_bot.main()
    except Exception as e:
        logger.error(f"❌ Customer Bot crashed: {e}", exc_info=True)


def main():
    mode = os.getenv("RUN_MODE", "all").lower()
    port = int(os.getenv("PORT", getattr(config, "PORT", 10000)))

    logger.info("=" * 60)
    logger.info("🚀 SALONE 4D — Render Deployment Starting")
    logger.info(f"   Target Channel : {config.CHANNEL_ID}")
    logger.info(f"   Run Mode       : {mode}")
    logger.info(f"   HTTP Port      : {port}")
    logger.info("=" * 60)

    # 1. Start Flask Web Server in background thread
    web_thread = threading.Thread(target=run_flask_server, args=(port,), daemon=True)
    web_thread.start()

    # 2. Start Keep-Alive Self-Pinger in background thread
    ping_thread = threading.Thread(target=keep_alive_worker, args=(port,), daemon=True)
    ping_thread.start()

    # 3. Start Scheduler if mode is 'all' or 'scheduler'
    if mode in ("all", "scheduler"):
        sched_thread = threading.Thread(target=run_scheduler_job, daemon=True)
        sched_thread.start()

    # 4. Start Customer Service Bot if mode is 'all' or 'bot'
    if mode in ("all", "bot"):
        # Run bot on the main thread (runs asyncio event loop)
        run_customer_bot()
    else:
        # Keep main thread alive if bot is disabled
        while True:
            time.sleep(3600)


if __name__ == "__main__":
    main()
