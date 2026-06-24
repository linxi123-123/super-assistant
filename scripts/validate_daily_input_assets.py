from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def record(condition: bool, label: str, blocking: list[str], warnings: list[str], warn: bool = False) -> None:
    status = "PASS" if condition else "WARN" if warn else "FAIL"
    print(f"{status}: {label}")
    if not condition:
        if warn:
            warnings.append(label)
        else:
            blocking.append(label)


def main() -> None:
    blocking: list[str] = []
    warnings: list[str] = []

    html_path = ROOT / "app" / "daily_input.html"
    css_path = ROOT / "app" / "daily_input.css"
    record(html_path.exists(), "exists app/daily_input.html", blocking, warnings)
    record(css_path.exists(), "exists app/daily_input.css", blocking, warnings)

    html = read("app/daily_input.html") if html_path.exists() else ""
    css = read("app/daily_input.css") if css_path.exists() else ""
    combined = (html + "\n" + css).lower()

    required_tokens = [
        "每日作战输入包",
        "input_date",
        "key_event",
        "current_question",
        "project_state_change",
        "committed_action",
        "constraints_or_forbidden",
        "evidence_note",
        "sensitivity",
        "use_for_today_judgment",
        "当前局势一句话",
        "当前最大矛盾",
        "军师直接判断",
        "今日唯一动作",
        "不要做清单",
        "不得自动长期化",
    ]
    for token in required_tokens:
        record(token.lower() in combined, f"required token present: {token}", blocking, warnings)

    forbidden_tokens = [
        "<input",
        "<textarea",
        "<form",
        "contenteditable",
        "localstorage",
        "fetch(",
        "xmlhttprequest",
        "http://",
        "https://",
        ".sqlite",
        ".db",
        "opendatabase",
        "insert into",
        "update ",
        "delete from",
        "post",
        "method: \"put\"",
        "method: 'put'",
        "method: \"delete\"",
        "method: 'delete'",
        "upload",
        "sync",
        "login",
        "react",
        "vue",
        "next.js",
        "cdn",
        "node_modules",
    ]
    found = [token for token in forbidden_tokens if token in combined]
    record(not found, f"no forbidden tokens found: {found}", blocking, warnings)

    record("@media" in css, "responsive CSS exists", blocking, warnings)
    record("grid-template-columns" in css, "stable grid layout exists", blocking, warnings)

    print(f"blocking_issues_count: {len(blocking)}")
    print(f"warnings_count: {len(warnings)}")
    print(f"allow_w7e_manual_acceptance: {str(not blocking).lower()}")

    if blocking:
        print("blocking issues:")
        for item in blocking:
            print(f"- {item}")
        raise SystemExit("FAIL")

    if warnings:
        print("warnings:")
        for item in warnings:
            print(f"- {item}")

    print("PASS")


if __name__ == "__main__":
    main()
