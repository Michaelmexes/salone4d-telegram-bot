#!/usr/bin/env python3
# ==========================================================
#   Salone4D Service - Unified Runner for Render Cloud
#   Runs Web Health Server + Auto Poster + Customer Care Bot
# ==========================================================

import os
import sys
import time
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
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


class HealthCheckHandler(BaseHTTPRequestHandler):
    """Minimal HTTP handler to satisfy Render Web Service health checks."""

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        response_msg = (
            f"Salone4D Bot & Scheduler is running!\n"
            f"Target Channel: {config.CHANNEL_ID}\n"
            f"Mode: {os.getenv('RUN_MODE', 'all')}\n"
            f"Status: OK\n"
        )
        self.wfile.write(response_msg.encode("utf-8"))

    def log_message(self, format, *args):
        # Silence routine health check access logs
        return


def run_web_server(port: int):
    """Run lightweight HTTP server in background thread."""
    server_address = ("0.0.0.0", port)
    httpd = HTTPServer(server_address, HealthCheckHandler)
    logger.info(f"🌐 Web health server listening on port {port}")
    httpd.serve_forever()


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
    port = getattr(config, "PORT", 10000)

    logger.info("=" * 60)
    logger.info("🚀 SALONE 4D — Render Deployment Starting")
    logger.info(f"   Target Channel : {config.CHANNEL_ID}")
    logger.info(f"   Run Mode       : {mode}")
    logger.info(f"   HTTP Port      : {port}")
    logger.info("=" * 60)

    # 1. Start HTTP Server for Render health check
    web_thread = threading.Thread(target=run_web_server, args=(port,), daemon=True)
    web_thread.start()

    # 2. Start Scheduler if mode is 'all' or 'scheduler'
    if mode in ("all", "scheduler"):
        sched_thread = threading.Thread(target=run_scheduler_job, daemon=True)
        sched_thread.start()

    # 3. Start Customer Service Bot if mode is 'all' or 'bot'
    if mode in ("all", "bot"):
        # Run bot on the main thread (runs asyncio event loop)
        run_customer_bot()
    else:
        # Keep main thread alive if bot is disabled
        while True:
            time.sleep(3600)


if __name__ == "__main__":
    main()
