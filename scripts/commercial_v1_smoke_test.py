from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


QUESTIONS = [
    ("今天股市怎么样", "market_advisor"),
    ("腾讯今天怎么样", "market_advisor"),
    ("我这个项目下一步该怎么做", "project_advisor"),
    ("我纠结要不要继续做这个产品", "decision_advisor"),
    ("我今天很烦，不知道该先做什么", "general_advisor"),
]


def post_http(base_url: str, payload: dict) -> dict:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/advisor/chat",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def post_testclient(payload: dict) -> dict:
    from fastapi.testclient import TestClient

    from server.main import app

    with TestClient(app) as client:
        response = client.post("/api/advisor/chat", json=payload)
        response.raise_for_status()
        return response.json()


def run() -> int:
    base_url = os.getenv("ADVISOR_BASE_URL", "").strip()
    audit_ids: set[str] = set()
    failures: list[str] = []

    for question, expected_task_type in QUESTIONS:
        try:
            payload = post_http(base_url, {"message": question}) if base_url else post_testclient({"message": question})
        except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
            failures.append(f"{question}: request failed: {exc}")
            continue

        checks = {
            "answer_nonempty": bool(payload.get("answer")),
            "task_type": payload.get("task_type") == expected_task_type,
            "audit_unique": payload.get("audit_id") and payload.get("audit_id") not in audit_ids,
            "provider_visible": "provider" in payload and "model" in payload and "llm_mode" in payload,
            "judge_visible": bool(payload.get("local_judge_status")),
            "quality_visible": isinstance(payload.get("answer_score"), dict),
            "memory_visible": "memory_status" in payload and "excluded_memory_count" in payload,
        }
        if payload.get("audit_id"):
            audit_ids.add(payload["audit_id"])
        if not all(checks.values()):
            failures.append(f"{question}: failed checks={checks}")
        print(
            f"{question} | task_type={payload.get('task_type')} | provider={payload.get('provider')}/"
            f"{payload.get('model')} | llm_mode={payload.get('llm_mode')} | "
            f"judge={payload.get('local_judge_status')} | audit_id={payload.get('audit_id')}"
        )

    if failures:
        print("\nCOMMERCIAL-V1 smoke test failed:")
        for item in failures:
            print(f"- {item}")
        return 1

    print("\nCOMMERCIAL-V1 smoke test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
