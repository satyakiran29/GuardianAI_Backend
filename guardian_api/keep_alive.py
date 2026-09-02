"""
Autonomous Self-Ping Keep-Alive Worker for Render / Heroku / Cloud Dynos
Sends an external HTTP request every 14 minutes to prevent free-tier servers from sleeping.
"""
import os
import sys
import time
import threading
import logging

logger = logging.getLogger(__name__)

_keep_alive_started = False

def _ping_loop():
    # Initial sleep after server startup before first ping (60 seconds)
    time.sleep(60)
    
    interval_seconds = int(os.getenv('SELF_PING_INTERVAL_SECONDS', 840)) # Default: 14 mins (840s)
    
    while True:
        try:
            # Render automatically sets RENDER_EXTERNAL_URL in environment
            base_url = (
                os.getenv('RENDER_EXTERNAL_URL') or 
                os.getenv('BACKEND_URL') or 
                os.getenv('SELF_PING_URL') or 
                'https://guardianai-backend-pwn5.onrender.com'
            ).rstrip('/')
            
            ping_endpoint = f"{base_url}/api/ping/"
            
            import requests
            response = requests.get(ping_endpoint, timeout=15)
            logger.info(f"⚡ [Self-Ping Keep-Alive] Pinged {ping_endpoint} -> HTTP {response.status_code}")
        except Exception as e:
            logger.warning(f"⚠️ [Self-Ping Keep-Alive] Notice: {e}")
            
        time.sleep(interval_seconds)


def start_keep_alive():
    """
    Spawns background daemon thread to self-ping every 14 minutes.
    Avoids spawning during management commands like migrate/collectstatic.
    """
    global _keep_alive_started
    if _keep_alive_started:
        return

    # Check if running in a command that shouldn't start background loop
    cmd_args = " ".join(sys.argv).lower()
    blocked_commands = ['migrate', 'makemigrations', 'collectstatic', 'seed_demo_data', 'shell', 'test']
    for cmd in blocked_commands:
        if cmd in cmd_args:
            return

    # Avoid duplicate start in Django dev server reload
    if 'runserver' in cmd_args and os.getenv('RUN_MAIN') != 'true':
        return

    _keep_alive_started = True
    thread = threading.Thread(target=_ping_loop, name="GuardianKeepAliveDaemon", daemon=True)
    thread.start()
    logger.info("🚀 GuardianAI autonomous 14-minute self-ping keep-alive daemon initialized!")
