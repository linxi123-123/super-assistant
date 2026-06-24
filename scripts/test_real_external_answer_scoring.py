from __future__ import annotations

import json
import os

import httpx


QUESTIONS = [
    "今天深圳天气怎么样",
    "今天 AI 有什么最新资讯",
    "OpenAI 最近有什么更新",
    "NVDA 今天怎么样",
    "今天股市怎么样",
    "我昨天问了什么",
]


def clip(value: str, limit: int = 600) -> str:
    return " ".join(str(value or "").split())[:limit]


def main() -> int:
    base_url = os.getenv("ADVISOR_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    for question in QUESTIONS:
        response = httpx.post(f"{base_url}/api/advisor/chat", json={"message": question}, timeout=45, trust_env=False)
        response.raise_for_status()
        payload = response.json()
        score = payload.get("answer_score", {})
        print("=" * 60)
        print(f"question={question}")
        print(f"task_type={payload.get('task_type')}")
        print(f"external_data_status={payload.get('external_data_status')}")
        print(f"external_data_type={payload.get('external_data_type')}")
        print(f"source_count={payload.get('source_count')}")
        print(f"freshness_summary={payload.get('freshness_summary')}")
        print(f"trust_summary={payload.get('trust_summary')}")
        print(f"conflict_summary={payload.get('conflict_summary')}")
        print(f"answer_score.total_score={score.get('total_score')}")
        print(f"answer_score.grade={score.get('grade')}")
        needs_review = int(score.get("total_score", 0)) < 38 or score.get("grade") != "pass" or bool(payload.get("was_downgraded"))
        print(f"needs_review={str(needs_review).lower()}")
        print(f"was_downgraded={payload.get('was_downgraded')}")
        print(f"downgrade_type={payload.get('downgrade_type')}")
        print(f"downgrade_reason={payload.get('downgrade_reason')}")
        print(f"warnings={json.dumps(payload.get('warnings', []), ensure_ascii=False)}")
        print(f"answer_600={clip(payload.get('answer', ''))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
