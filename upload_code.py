"""Upload new feature files to server via SFTP."""
import getpass, sys, os, io
import paramiko

HOST, PORT, USER = "8.163.35.221", 22, "admin"
REMOTE_DIR = "/opt/super-assistant"
LOCAL_ROOT = os.path.dirname(os.path.abspath(__file__))

# Files to upload: (local_relative_path, remote_relative_path)
FILES = [
    ("server/config.py", "server/config.py"),
    ("server/database.py", "server/database.py"),
    ("server/main.py", "server/main.py"),
    ("server/services/profile_service.py", "server/services/profile_service.py"),
    ("server/routers/local_agent_router.py", "server/routers/local_agent_router.py"),
    ("server/schemas/local_agent_schemas.py", "server/schemas/local_agent_schemas.py"),
    ("server/services/local_agent_job_service.py", "server/services/local_agent_job_service.py"),
    ("local_claude_worker.py", "local_claude_worker.py"),
    ("app/local-claude-check.html", "app/local-claude-check.html"),
]

# Read token
env_path = os.path.join(LOCAL_ROOT, ".env")
token = ""
with open(env_path, "r", encoding="utf-8") as f:
    for line in f:
        if line.startswith("LOCAL_WORKER_TOKEN="):
            token = line.strip().split("=", 1)[1]
            break
if len(token) < 32:
    print("ERROR: token not found")
    sys.exit(1)
print(f"Token OK (len={len(token)})")

# Server .env
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
LOCAL_WORKER_TOKEN={token}
LOCAL_AGENT_JOB_TIMEOUT_SECONDS=900
"""

password = getpass.getpass(f"SSH password for {USER}@{HOST}: ")

# Connect
transport = paramiko.Transport((HOST, PORT))
transport.connect(username=USER, password=password)
sftp = paramiko.SFTPClient.from_transport(transport)
ssh = paramiko.SSHClient()
ssh._transport = transport

print("Connected. Uploading files...")

# Upload each file
for local_path, remote_path in FILES:
    local_full = os.path.join(LOCAL_ROOT, local_path)
    remote_full = f"{REMOTE_DIR}/{remote_path}"
    try:
        # Ensure remote directory exists
        remote_dir = os.path.dirname(remote_full)
        try:
            sftp.stat(remote_dir)
        except FileNotFoundError:
            # Create directory
            ssh.exec_command(f"mkdir -p {remote_dir}")
        sftp.put(local_full, remote_full)
        print(f"  OK: {remote_path}")
    except Exception as e:
        print(f"  FAIL: {remote_path} — {e}")

# Write .env
print("Writing .env...")
sftp.putfo(io.BytesIO(SERVER_ENV.encode("utf-8")), f"{REMOTE_DIR}/.env")
print("  OK: .env")

# Restart server
print("Restarting server...")
cmds = [
    "sudo pkill -f uvicorn || echo 'no_process'",
    "sleep 1",
    f"cd {REMOTE_DIR} && nohup python3 -m uvicorn server.main:app --host 0.0.0.0 --port 8000 > /var/log/super-assistant.log 2>&1 &",
    "sleep 2",
    "curl -s http://127.0.0.1:8000/api/health",
]
for cmd in cmds:
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode("utf-8", errors="replace").strip()
    err = stderr.read().decode("utf-8", errors="replace").strip()
    if out:
        print(f"  [{cmd[:50]}]: {out[:200]}")
    if err:
        print(f"  stderr: {err[:200]}")

sftp.close()
transport.close()
print("\nDone. Check: http://8.163.35.221:8000/api/health")
