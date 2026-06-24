#!/usr/bin/env python3
"""
Deploy super-assistant to remote server via SSH.
Prompts for password securely — never stored, never printed.
"""
import getpass
import sys
import os
from io import StringIO

try:
    import paramiko
except ImportError:
    print("pip install paramiko")
    sys.exit(1)

# ── Config ──────────────────────────────────────────────────
HOST = "8.163.35.221"
PORT = 22
USER = "root"
REMOTE_DIR = "/opt/super-assistant"

# Read token from local .env (never print it)
local_env = {}
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
with open(env_path, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            local_env[k.strip()] = v.strip()

TOKEN = local_env.get("LOCAL_WORKER_TOKEN", "")
if len(TOKEN) < 32:
    print("ERROR: LOCAL_WORKER_TOKEN not found or too short in .env")
    sys.exit(1)
print(f"Token loaded from .env (length={len(TOKEN)}, starts with {TOKEN[:4]}...)")

# ── Server .env content ─────────────────────────────────────
SERVER_ENV = f"""OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
LLM_MODE=mock
SELECTED_LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com
KIMI_API_KEY=
KIMI_MODEL=moonshot-v1-8k
KIMI_BASE_URL=https://api.moonshot.ai/v1
ADVISOR_MASTER_KEY=
WEATHER_PROVIDER=openweather
OPENWEATHER_API_KEY=
OPENWEATHER_BASE_URL=https://api.openweathermap.org
OPENMETEO_BASE_URL=https://api.open-meteo.com
SEARCH_PROVIDER=tavily
TAVILY_API_KEY=
TAVILY_BASE_URL=https://api.tavily.com
NEWS_PROVIDER=search
MARKET_DATA_PROVIDER=finnhub
FINNHUB_API_KEY=
FINNHUB_BASE_URL=https://finnhub.io/api/v1
NEWS_API_KEY=
MEMORY_ENABLED=true
MEMORY_RECENT_LIMIT=5
MEMORY_ALLOW_LLM_CONTEXT=true
APP_ENV=local
LOCAL_CLAUDE_WORKER_ENABLED=true
LOCAL_WORKER_TOKEN={TOKEN}
LOCAL_AGENT_JOB_TIMEOUT_SECONDS=900
"""

# ── SSH ─────────────────────────────────────────────────────
password = getpass.getpass(f"Enter SSH password for {USER}@{HOST}: ")

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    client.connect(HOST, port=PORT, username=USER, password=password, timeout=10)
except Exception as e:
    print(f"SSH connection failed: {e}")
    sys.exit(1)

print("Connected to server.")

# ── Execute commands ────────────────────────────────────────
commands = [
    ("Write .env", f"cat > {REMOTE_DIR}/.env << 'ENVEOF'\n{SERVER_ENV}ENVEOF"),
    ("Verify .env token", f"grep -c LOCAL_WORKER_TOKEN {REMOTE_DIR}/.env"),
    ("Verify worker enabled", f"grep LOCAL_CLAUDE_WORKER_ENABLED {REMOTE_DIR}/.env"),
    ("Create data dir", f"mkdir -p {REMOTE_DIR}/data"),
    ("Kill old uvicorn", "pkill -f 'uvicorn server.main' 2>/dev/null; echo 'cleaned'"),
    ("Start server", f"cd {REMOTE_DIR} && source .venv/bin/activate && nohup uvicorn server.main:app --host 0.0.0.0 --port 8000 > /var/log/super-assistant.log 2>&1 & sleep 2; echo 'started'"),
    ("Check health", "curl -s http://127.0.0.1:8000/api/health"),
]


for label, cmd in commands:
    print(f"\n[{label}]")
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode("utf-8", errors="replace").strip()
    err = stderr.read().decode("utf-8", errors="replace").strip()
    if out:
        print(f"  stdout: {out}")
    if err and "Warning" not in err:
        print(f"  stderr: {err[:200]}")

client.close()
print("\n=== Done ===")
print("Check: http://8.163.35.221:8000/api/health")
print("Verification page: http://8.163.35.221:8000/local-claude-check.html")
