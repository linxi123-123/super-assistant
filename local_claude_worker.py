#!/usr/bin/env python3
"""
Local Claude Worker — 本机 Worker 脚本

功能:
  1. 读取 .env.worker 配置
  2. 主动轮询服务器 /api/local-agent/worker/next 拉取任务
  3. 调用本机 Claude Code 执行深度推理
  4. 回传推理结果到服务器

使用:
  python local_claude_worker.py
  uv run python local_claude_worker.py

依赖:
  pip install requests python-dotenv
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

# Fix Windows console encoding for emoji/Unicode output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ── Config ──────────────────────────────────────────────────

load_dotenv(".env.worker")


def _env(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


SUPER_ASSISTANT_SERVER = _env("SUPER_ASSISTANT_SERVER", "http://127.0.0.1:8000")
LOCAL_WORKER_TOKEN = _env("LOCAL_WORKER_TOKEN", "")
LLM_WIKI_ROOT = _env("LLM_WIKI_ROOT", "")
CLAUDE_COMMAND = _env("CLAUDE_COMMAND", "cmd.exe /d /s /c claude")
CLAUDE_TIMEOUT_SECONDS = int(_env("CLAUDE_TIMEOUT_SECONDS", "900") or "900")
WORKER_POLL_INTERVAL_SECONDS = int(_env("WORKER_POLL_INTERVAL_SECONDS", "3") or "3")

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "worker_logs")

# ── Helpers ─────────────────────────────────────────────────


def log(msg: str) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    line = f"[{ts}] {msg}"
    # Print safely — replace chars that the console can't encode
    try:
        print(line, flush=True)
    except (UnicodeEncodeError, UnicodeDecodeError):
        print(line.encode("ascii", errors="replace").decode("ascii"), flush=True)

    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        log_file = os.path.join(LOG_DIR, "worker.log")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass  # never crash on log write failure


def safe_error(exc: Exception) -> str:
    """Return a safe error string, no secrets."""
    msg = str(exc)[:500]
    # Redact any token-like patterns (crude but effective)
    for secret in [LOCAL_WORKER_TOKEN] if LOCAL_WORKER_TOKEN else []:
        if secret and len(secret) > 8:
            msg = msg.replace(secret, "***")
    return msg


# ── Server communication ───────────────────────────────────


def api_headers() -> dict:
    return {
        "Authorization": f"Bearer {LOCAL_WORKER_TOKEN}",
        "Content-Type": "application/json",
    }


def fetch_next_job() -> dict | None:
    """Fetch the next pending job from the server. Returns job dict or None."""
    try:
        url = f"{SUPER_ASSISTANT_SERVER.rstrip('/')}/api/local-agent/worker/next"
        resp = requests.get(url, headers=api_headers(), timeout=30)
        if resp.status_code == 401:
            log("ERROR: Worker token rejected (401). Check LOCAL_WORKER_TOKEN.")
            return None
        if resp.status_code == 503:
            log("WARN: Local Claude Worker is disabled on server.")
            return None
        if resp.status_code != 200:
            log(f"WARN: Unexpected status {resp.status_code} from worker/next: {resp.text[:200]}")
            return None
        data = resp.json()
        return data.get("job")
    except requests.exceptions.ConnectionError:
        log(f"WARN: Cannot connect to {SUPER_ASSISTANT_SERVER}")
        return None
    except Exception as exc:
        log(f"ERROR: fetch_next_job failed: {safe_error(exc)}")
        return None


def submit_result(job_id: str, status: str, result: dict | None = None, error: str = "") -> bool:
    """Submit job result back to server. Returns True on success."""
    try:
        url = f"{SUPER_ASSISTANT_SERVER.rstrip('/')}/api/local-agent/worker/jobs/{job_id}/result"
        body = {
            "status": status,
            "result": result or {},
            "error": error,
        }
        resp = requests.post(url, json=body, headers=api_headers(), timeout=30)
        if resp.status_code == 200:
            return True
        log(f"ERROR: submit_result got {resp.status_code}: {resp.text[:200]}")
        return False
    except Exception as exc:
        log(f"ERROR: submit_result failed: {safe_error(exc)}")
        return False


# ── Claude Code invocation ──────────────────────────────────


CLAUDE_PROMPT_TEMPLATE = """你是用户的个人超级助理，运行在本机 Claude Code 环境。

## 你的角色
你是推理引擎，不是产品编排器。回答材料由上游 advisor 编排层提供。

## 可用材料（在额外上下文中）
- **system_prompt**: 产品人格设定，必须遵守
- **intent_type**: 问题意图类型
- **task_type**: 任务分类
- **memory_context**: 用户的长期记忆（由服务器从 LLM Wiki / 记忆库检索）
- **external_context**: 服务器的公开资料检索结果（已通过 Tavily 搜索）
- **profile_context**: 用户画像和项目背景

## 回答规则
1. 优先使用 external_context 中的公开资料来回答公开知识问题
2. 使用 memory_context 来关联用户个人背景
3. external_context 有结果时，不要忽视它，要基于这些资料组织回答
4. external_context 没有结果且问题不是公开知识时，不需要强调"没有搜索结果"
5. 回答风格：中文，自然对话，像老朋友。区分事实和推断。不要说"我的知识截止到"。
6. 不要输出审计报告口吻
7. 不要说"Wiki 没有所以无法回答"——如果 external_context 有资料就基于它回答
8. 输出必须是 JSON

## system_prompt（必须遵守的人格）:
{system_prompt}

用户问题：
{question}

额外上下文：
{context_json}

请严格输出 JSON（不要 markdown 代码块，answer_mode 必填不能为空）：

{{
  "answer_mode": "personal_memory | public_research | mixed | task_execution | casual_chat",
  "answer": "给用户看的完整中文答案",
  "summary": "简洁推理摘要",
  "sources": [
    {{
      "title": "来源标题",
      "url": "来源链接",
      "source": "Tavily | LLM Wiki | 用户记忆"
    }}
  ],
  "confidence": "high|medium|low",
  "confidence_reason": "为什么是这个置信度",
  "next_actions": ["下一步建议"],
  "memory_updates": [
    {{
      "target": "建议写入的 wiki 文件路径",
      "content": "建议写入的内容",
      "reason": "为什么建议写入"
    }}
  ],
  "warnings": []
}}"""


def _windows_cmd_to_args(base_command: str) -> list[str]:
    """Parse a Windows-style command string into a list of arguments.

    For 'cmd.exe /d /s /c claude', returns ['cmd.exe', '/d', '/s', '/c', 'claude'].
    The entire string is the base command; Claude args are appended after this.
    """
    tokens = base_command.strip()

    if tokens.startswith("cmd.exe ") or tokens.startswith("cmd "):
        try:
            return shlex.split(tokens, posix=False)
        except ValueError:
            return tokens.split()

    return []


def _get_base_cmd() -> list[str]:
    """Parse CLAUDE_COMMAND into the base command prefix (cmd.exe wrapper or claude)."""
    base = CLAUDE_COMMAND.strip()
    if base.startswith("cmd.exe ") or base.startswith("cmd "):
        return _windows_cmd_to_args(base)
    try:
        return shlex.split(base, posix=False)
    except ValueError:
        return base.split()


def build_claude_args(base_command: str, prompt: str) -> list[str]:
    """Build the argument list for calling Claude Code.

    Handles both direct claude calls and cmd.exe-wrapped calls.
    """
    base = base_command.strip()
    prompt = prompt.strip()

    # Claude CLI arguments (without the command prefix)
    claude_args = [
        "-p", prompt,
        "--output-format", "json",
        "--permission-mode", "bypassPermissions",
    ]

    # Check if it's a cmd.exe wrapper
    if base.startswith("cmd.exe ") or base.startswith("cmd "):
        cmd_prefix = _windows_cmd_to_args(base)
        return cmd_prefix + claude_args

    # Direct claude call
    return shlex.split(base, posix=False) + claude_args


def _do_public_research(question: str, job_id: str) -> str:
    """Call server-side public research API and return formatted results."""
    try:
        url = f"{SUPER_ASSISTANT_SERVER.rstrip('/')}/api/public-research/search"
        resp = requests.post(
            url,
            json={"query": question, "max_results": 5},
            headers=api_headers(),
            timeout=30,
        )
        if resp.status_code != 200:
            log(f"JOB {job_id}: Public research API returned {resp.status_code}")
            return ""
        data = resp.json()
        if data.get("status") == "disabled":
            log(f"JOB {job_id}: Public research disabled (no API key configured)")
            return ""
        results = data.get("results", [])
        if not results:
            log(f"JOB {job_id}: Public research returned 0 results")
            return ""

        lines = [f"共检索到 {len(results)} 条公开资料：\n"]
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. **{r.get('title', '无标题')}**")
            if r.get("snippet"):
                lines.append(f"   摘要: {r.get('snippet')}")
            if r.get("url"):
                lines.append(f"   链接: {r.get('url')}")
            lines.append(f"   来源: {r.get('source', 'Tavily')}")
            lines.append("")

        log(f"JOB {job_id}: Public research returned {len(results)} results")
        return "\n".join(lines)
    except Exception as exc:
        log(f"JOB {job_id}: Public research failed: {safe_error(exc)}")
        return ""


def run_claude(job: dict) -> dict:
    """Run Claude Code for a job and return parsed result JSON.

    Returns dict with keys: answer, summary, next_actions, memory_updates, confidence, warnings
    """
    question = job.get("question", "")
    context = job.get("context", {})
    task_type = job.get("task_type", "deep_reasoning")
    job_id = job.get("job_id", "unknown")

    # If public research is enabled, fetch results from server before calling Claude
    public_research_results = ""
    if context.get("allow_public_research"):
        public_research_results = _do_public_research(question, job_id)

    context_json = json.dumps(context, ensure_ascii=False, indent=2)
    system_prompt = context.get("system_prompt", "你是用户的个人超级助理。中文自然对话风格，像老朋友。")
    prompt = CLAUDE_PROMPT_TEMPLATE.format(
        question=question,
        context_json=context_json,
        system_prompt=system_prompt,
    )

    # Append public research results to the prompt
    if public_research_results:
        prompt += "\n\n## 公开资料检索结果\n\n以下是服务器端通过 Tavily 搜索获取的公开资料，请综合这些结果进行回答：\n\n" + public_research_results

    # Work out the working directory
    cwd = LLM_WIKI_ROOT if LLM_WIKI_ROOT and os.path.isdir(LLM_WIKI_ROOT) else os.getcwd()
    if LLM_WIKI_ROOT and not os.path.isdir(LLM_WIKI_ROOT):
        log(f"WARN: LLM_WIKI_ROOT '{LLM_WIKI_ROOT}' does not exist, using current directory.")

    # Write prompt to temp file for debugging & as a safe stdin source
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        prompt_file = os.path.join(LOG_DIR, f"prompt_{job_id}.txt")
        with open(prompt_file, "w", encoding="utf-8") as f:
            f.write(prompt)
    except Exception:
        prompt_file = None

    # Build command: -p for non-interactive, --output-format json for structured output.
    # --permission-mode bypassPermissions needed for WebSearch/WebFetch in non-interactive mode.
    # Prompt is piped via stdin to avoid issues with multi-line prompts and cmd.exe quoting.
    base_cmd = _get_base_cmd()
    safe_args = base_cmd + ["-p", "--output-format", "json", "--permission-mode", "bypassPermissions"]
    log(f"JOB {job_id}: Running Claude with task_type={task_type} in {cwd}")
    log(f"JOB {job_id}: Command: {' '.join(safe_args)} (prompt via stdin, {len(prompt)} chars)")

    try:
        # Run Claude with prompt piped via stdin
        proc = subprocess.run(
            safe_args,
            cwd=cwd,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=CLAUDE_TIMEOUT_SECONDS,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.TimeoutExpired:
        log(f"JOB {job_id}: Claude timed out after {CLAUDE_TIMEOUT_SECONDS}s")
        raise RuntimeError(f"claude_timeout: exceeded {CLAUDE_TIMEOUT_SECONDS}s")

    # Save raw output for debugging
    try:
        out_file = os.path.join(LOG_DIR, f"output_{job_id}.txt")
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(f"=== STDOUT ===\n{proc.stdout}\n\n=== STDERR ===\n{proc.stderr}\n\n=== RC: {proc.returncode}")
    except Exception:
        pass

    if proc.returncode != 0:
        err = proc.stderr[:500] if proc.stderr else f"exit_code={proc.returncode}"
        log(f"JOB {job_id}: Claude exited with code {proc.returncode}: {err}")
        raise RuntimeError(f"claude_exit_error: {err}")

    # Try to parse JSON from output
    stdout = proc.stdout.strip()
    if not stdout:
        raise RuntimeError("claude_empty_output")

    # Claude may wrap JSON in markdown code blocks or have surrounding text
    return _extract_json(stdout, job_id)


def _extract_json(text: str, job_id: str) -> dict:
    """Try to extract a valid JSON object from Claude's output.

    When using --output-format json, Claude Code wraps the model output in:
    {"type":"result","subtype":"success","result":"...model text...","session_id":"..."}
    The actual model response is in the 'result' field.
    """
    # Strategy 0: Parse Claude Code wrapper JSON, extract model result
    try:
        wrapper = json.loads(text)
        if isinstance(wrapper, dict) and "result" in wrapper:
            model_text = wrapper["result"]
            log(f"JOB {job_id}: Extracted model text from Claude Code wrapper JSON.")
            # Try to parse the model text as JSON
            parsed = _try_parse_model_json(model_text, job_id)
            if parsed is not None:
                return parsed
            # If model text is not JSON, wrap it
            return {
                "answer": model_text[:10000],
                "summary": "Claude 返回了非 JSON 格式的回答",
                "next_actions": [],
                "memory_updates": [],
                "confidence": "low",
                "warnings": ["claude_output_not_json"],
            }
    except json.JSONDecodeError:
        pass

    # Strategy 1: Direct parse (fallback for non-JSON-output-format)
    parsed = _try_parse_model_json(text, job_id)
    if parsed is not None:
        return parsed

    # Strategy 2: Wrap raw text as answer
    log(f"JOB {job_id}: Could not parse JSON, treating as plain text answer.")
    return {
        "answer": text[:10000],
        "summary": "Claude 返回了非 JSON 格式的回答",
        "next_actions": [],
        "memory_updates": [],
        "confidence": "low",
        "warnings": ["claude_output_not_json"],
    }


def _try_parse_model_json(text: str, job_id: str) -> dict | None:
    """Try to extract { ... } JSON from model text output."""
    import re

    # Direct parse
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict) and "answer" in parsed:
            log(f"JOB {job_id}: Model output parsed as JSON directly.")
            return parsed
    except (json.JSONDecodeError, ValueError):
        pass

    # Find JSON between ```json and ```
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        try:
            parsed = json.loads(m.group(1))
            if isinstance(parsed, dict) and "answer" in parsed:
                log(f"JOB {job_id}: Model output parsed from markdown code block.")
                return parsed
        except (json.JSONDecodeError, ValueError):
            pass

    # Find first { and last }
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            parsed = json.loads(text[start:end + 1])
            if isinstance(parsed, dict):
                log(f"JOB {job_id}: Model output parsed by extracting between braces.")
                return parsed
        except (json.JSONDecodeError, ValueError):
            pass

    return None


# ── Main loop ───────────────────────────────────────────────


def main() -> None:
    log("=" * 60)
    log("Local Claude Worker starting...")
    log(f"  Server:   {SUPER_ASSISTANT_SERVER}")
    log(f"  Wiki:     {LLM_WIKI_ROOT or '(current directory)'}")
    log(f"  Claude:   {CLAUDE_COMMAND}")
    log(f"  Timeout:  {CLAUDE_TIMEOUT_SECONDS}s")
    log(f"  Poll:     {WORKER_POLL_INTERVAL_SECONDS}s")
    log("=" * 60)

    # Validate config
    if not LOCAL_WORKER_TOKEN:
        log("ERROR: LOCAL_WORKER_TOKEN is not set. Create .env.worker with a valid token.")
        log("  cp .env.worker.example .env.worker")
        log("  Edit .env.worker with your actual values.")
        sys.exit(1)

    if not SUPER_ASSISTANT_SERVER:
        log("ERROR: SUPER_ASSISTANT_SERVER is not set.")
        sys.exit(1)

    # Main polling loop
    consecutive_errors = 0
    while True:
        try:
            job = fetch_next_job()

            if not job:
                consecutive_errors = 0
                time.sleep(WORKER_POLL_INTERVAL_SECONDS)
                continue

            job_id = job.get("job_id", "unknown")
            log(f"JOB {job_id}: Claimed! task_type={job.get('task_type')}")

            try:
                result = run_claude(job)
                submit_result(job_id, "succeeded", result=result)
                log(f"JOB {job_id}: SUCCEEDED, answer preview: {result.get('answer', '')[:100]}...")
            except Exception as exc:
                err_msg = safe_error(exc)
                log(f"JOB {job_id}: FAILED — {err_msg}")
                submit_result(job_id, "failed", result={}, error=err_msg)

            consecutive_errors = 0

        except KeyboardInterrupt:
            log("Worker stopped by user.")
            break
        except Exception as exc:
            consecutive_errors += 1
            log(f"ERROR (main loop #{consecutive_errors}): {safe_error(exc)}")
            if consecutive_errors > 10:
                log("Too many consecutive errors, exiting.")
                break
            time.sleep(min(WORKER_POLL_INTERVAL_SECONDS * (consecutive_errors + 1), 60))


if __name__ == "__main__":
    main()
