import getpass, sys
import paramiko

HOST, PORT, USER = "8.163.35.221", 22, "root"
REMOTE_DIR = "/opt/super-assistant"

password = getpass.getpass(f"SSH password for {USER}@{HOST}: ")
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    client.connect(HOST, port=PORT, username=USER, password=password, timeout=10)
except Exception as e:
    print(f"SSH failed: {e}")
    sys.exit(1)

cmds = [
    ("Check uvicorn process", "ps aux | grep uvicorn | grep -v grep || echo 'NO_UVICORN'"),
    ("Check port 8000", "ss -tlnp | grep 8000 || echo 'NO_PORT'"),
    ("Recent log", "tail -20 /var/log/super-assistant.log 2>/dev/null || echo 'NO_LOG'"),
    ("Check .env exists", f"ls -la {REMOTE_DIR}/.env 2>/dev/null && head -3 {REMOTE_DIR}/.env || echo 'NO_ENV'"),
    ("Check code version", f"cd {REMOTE_DIR} && git branch --show-current 2>/dev/null || echo 'NO_GIT'"),
    ("Try start uvicorn directly", f"cd {REMOTE_DIR} && source .venv/bin/activate && python -c 'from server.main import app; print(\"import OK\")' 2>&1 | tail -5"),
]

for label, cmd in cmds:
    print(f"\n[{label}]")
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode("utf-8", errors="replace").strip()
    err = stderr.read().decode("utf-8", errors="replace").strip()
    if out:
        print(out)
    if err:
        print(f"  stderr: {err[:300]}")

client.close()
