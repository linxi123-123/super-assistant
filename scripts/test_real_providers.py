from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from server.services.external_intelligence_service import get_external_context  # noqa: E402


CASES = [
    ("OpenWeather", "今天深圳天气怎么样", "general_advisor"),
    ("Tavily", "今天 AI 有什么最新资讯", "general_advisor"),
    ("Finnhub", "NVDA 今天怎么样", "market_advisor"),
]


def clip(value: str, limit: int = 300) -> str:
    return " ".join(str(value or "").split())[:limit]


def main() -> int:
    for provider, question, task_type in CASES:
        result = get_external_context(question, task_type, "")
        pack = result.get("evidence_pack", {})
        summaries = [clip(item.get("summary", "")) for item in result.get("items", [])[:3]]
        print("=" * 60)
        print(f"provider={provider}")
        print(f"data_status={result.get('data_status')}")
        print(f"source_count={pack.get('source_count', 0)}")
        print(f"freshness_summary={pack.get('freshness_summary', 'no_sources')}")
        print(f"trust_summary={pack.get('trust_summary', 'no_sources')}")
        print(f"conflict_summary={pack.get('conflict_summary', '')}")
        print(f"warnings={json.dumps(result.get('warnings', []), ensure_ascii=False)}")
        print(f"summary_300={clip(' | '.join(summaries))}")
        print(f"real_provider_available={str(result.get('data_status') == 'available' and bool(result.get('items'))).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
