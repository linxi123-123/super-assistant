from __future__ import annotations

import json
import urllib.error
import urllib.request


API_URL = "http://127.0.0.1:8000/api/advisor/chat"

QUESTIONS = [
    "今天股市怎么样",
    "腾讯今天怎么样",
    "我这个项目下一步该怎么做",
    "我纠结要不要继续做这个产品",
    "我今天很烦，不知道该先做什么",
]


def post_question(question: str) -> dict:
    body = json.dumps({"message": question}, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    print("FAST-E2R DeepSeek real-call acceptance smoke test")
    print("This script never reads or prints API keys.")
    print(f"Target API: {API_URL}")
    print("")

    any_real_like = False
    for index, question in enumerate(QUESTIONS, start=1):
        print(f"===== Case {index}: {question} =====")
        try:
            payload = post_question(question)
        except urllib.error.URLError as exc:
            print(f"request_error: {exc.__class__.__name__}")
            print("请确认后端已启动：python -m uvicorn server.main:app --host 127.0.0.1 --port 8000")
            return 1

        answer = str(payload.get("answer", ""))
        llm_mode = payload.get("llm_mode", "")
        provider = payload.get("provider", "")
        warnings = payload.get("warnings", [])

        print(f"task_type: {payload.get('task_type')}")
        print(f"llm_mode: {llm_mode}")
        print(f"provider: {provider}")
        print(f"model: {payload.get('model')}")
        print(f"local_judge_status: {payload.get('local_judge_status')}")
        print(f"audit_id: {payload.get('audit_id')}")
        print(f"warnings: {warnings}")
        print("answer_preview:")
        print(answer[:500])

        if llm_mode == "openai" and provider == "deepseek" and answer:
            any_real_like = True
            print("真实模型路径疑似可用，请人工检查回答质量。")
        else:
            print("当前疑似 fallback mock，未完成真实 DeepSeek 调用。")
        print("")

    if any_real_like:
        print("Overall: DeepSeek real-call path appears available. Please score answers manually.")
    else:
        print("Overall: No confirmed real DeepSeek response. Check .env and backend restart.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
