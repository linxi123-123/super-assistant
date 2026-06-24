from __future__ import annotations

import json
import os
import sys

import httpx


QUESTIONS = [
    "今天深圳天气怎么样",
    "今天 AI 有什么最新资讯",
    "OpenAI 最近有什么更新",
    "NVDA 今天怎么样",
    "今天股市怎么样",
]


def clip(value: str, limit: int = 500) -> str:
    return " ".join(str(value or "").split())[:limit]


def extra_warnings(payload: dict) -> list[str]:
    warnings: list[str] = []
    answer = payload.get("answer", "")
    if payload.get("source_count", 0) > 0 and "来源" not in answer:
        warnings.append("answer_missing_source_reference")
    denial = any(token in answer for token in ["不能把没有来源的数据当成实时事实", "不编造实时", "不得声称知道最新", "无来源"])
    if payload.get("source_count", 0) == 0 and any(token in answer for token in ["最新", "实时", "当前行情"]) and not denial:
        warnings.append("fresh_or_realtime_claim_without_sources")
    return warnings


def main() -> int:
    base_url = os.getenv("ADVISOR_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    url = f"{base_url}/api/advisor/chat"
    for question in QUESTIONS:
        response = httpx.post(url, json={"message": question}, timeout=30, trust_env=False)
        response.raise_for_status()
        payload = response.json()
        warnings = list(payload.get("warnings", [])) + extra_warnings(payload)
        print("=" * 60)
        print(f"question={question}")
        print(f"task_type={payload.get('task_type')}")
        print(f"provider={payload.get('provider')}")
        print(f"llm_mode={payload.get('llm_mode')}")
        print(f"model={payload.get('model')}")
        print(f"used_external_data={payload.get('used_external_data')}")
        print(f"external_data_status={payload.get('external_data_status')}")
        print(f"external_data_type={payload.get('external_data_type')}")
        print(f"source_count={payload.get('source_count')}")
        print(f"freshness_summary={payload.get('freshness_summary')}")
        print(f"trust_summary={payload.get('trust_summary')}")
        print(f"conflict_summary={payload.get('conflict_summary')}")
        print(f"audit_id={payload.get('audit_id')}")
        print(f"warnings={json.dumps(warnings, ensure_ascii=False)}")
        print(f"answer_500={clip(payload.get('answer', ''))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
