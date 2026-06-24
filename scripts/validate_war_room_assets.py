from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def record(
    condition: bool,
    label: str,
    blocking: list[str],
    warnings: list[str],
    *,
    warn: bool = False,
    detail: str = "",
) -> None:
    status = "PASS" if condition else "WARN" if warn else "FAIL"
    suffix = f" - {detail}" if detail else ""
    print(f"{status}: {label}{suffix}")
    if not condition:
        if warn:
            warnings.append(label)
        else:
            blocking.append(label)


def contains_any(text: str, tokens: list[str]) -> list[str]:
    lowered = text.lower()
    return [token for token in tokens if token.lower() in lowered]


def contains_external_url(text: str) -> list[str]:
    lowered = text.lower()
    found = []
    for token in ["http://", "https://", "//unpkg", "//cdn"]:
        if token in lowered:
            found.append(token)
    return found


def main() -> None:
    blocking: list[str] = []
    warnings: list[str] = []

    required_files = [
        "app/war_room.html",
        "app/war_room.js",
        "app/war_room.css",
        "data/real_war_room_snapshot_v1.json",
        "data/war_room_snapshot_v1.json",
    ]
    for rel in required_files:
        record((ROOT / rel).exists(), f"exists {rel}", blocking, warnings)

    html = read("app/war_room.html") if (ROOT / "app/war_room.html").exists() else ""
    js = read("app/war_room.js") if (ROOT / "app/war_room.js").exists() else ""
    css = read("app/war_room.css") if (ROOT / "app/war_room.css").exists() else ""

    module_labels = [
        "Current Situation",
        "Advisor Brief",
        "Today",
        "High-value Signals",
        "Personal Model Hypotheses",
        "Commitments &amp; Gates",
        "Recent History",
        "Audit Entry",
        "Source Metadata &amp; Snapshot Audit",
    ]
    for label in module_labels:
        record(label in html, f"module present: {label}", blocking, warnings)

    w6d_markers = [
        (["current_stage_label", "当前阶段"], "W6D current_stage_label or 当前阶段 marker"),
        (["judgment_generated_at", "判断生成时间"], "W6D judgment_generated_at or 判断生成时间 marker"),
        (["judgment_valid_window", "判断有效期 / 适用窗口"], "W6D judgment_valid_window or 判断有效期 / 适用窗口 marker"),
        (["current_action_label", "当前唯一动作"], "W6D current_action_label or 当前唯一动作 marker"),
        (["historical_context_notice", "历史审计提示"], "W6D historical_context_notice or 历史审计提示 marker"),
        (["next_stage_gate", "下一阶段门槛"], "W6D next_stage_gate or 下一阶段门槛 marker"),
        (["forbidden_now", "当前禁止事项"], "W6D forbidden_now or 当前禁止事项 marker"),
    ]
    for tokens, label in w6d_markers:
        record(any(token in html or token in js for token in tokens), label, blocking, warnings)

    record(
        'const REAL_SNAPSHOT_PATH = "../data/real_war_room_snapshot_v1.json"' in js,
        "real snapshot path is exact allowed relative file",
        blocking,
        warnings,
    )
    record(
        'const SNAPSHOT_PATH = "../data/war_room_snapshot_v1.json"' in js,
        "historical snapshot path is exact allowed relative file",
        blocking,
        warnings,
    )
    record(
        js.count("fetch(") == 2 and "fetch(REAL_SNAPSHOT_PATH)" in js and "fetch(SNAPSHOT_PATH)" in js,
        "only fetches two local snapshots",
        blocking,
        warnings,
    )

    forbidden_js_tokens = [
        "sqlite",
        "openDatabase",
        "indexedDB",
        "localStorage.setItem",
        "sessionStorage.setItem",
        "WebSocket",
        "INSERT INTO",
        "UPDATE ",
        "DELETE FROM",
        "contenteditable",
        'createElement("form")',
        "textarea",
        "<input",
        "submit",
        "XMLHttpRequest",
        "axios",
        "React",
        "Vue",
        "Next.js",
        "import ",
        "require(",
    ]
    found_js = contains_any(js, forbidden_js_tokens)
    record(not found_js, "no JS write/database/framework/input logic", blocking, warnings, detail=f"found={found_js}")

    write_methods = ["post", "put", "delete", "patch"]
    write_found = contains_any(js, [f'method: "{method}"' for method in write_methods] + [f"method: '{method}'" for method in write_methods])
    record(not write_found, "no POST / PUT / DELETE / PATCH methods", blocking, warnings, detail=f"found={write_found}")

    sqlite_found = contains_any(html + js + css, ["sqlite", ".db", ".sqlite", "openDatabase", "INSERT INTO", "UPDATE ", "DELETE FROM"])
    record(not sqlite_found, "no SQLite related read/write references", blocking, warnings, detail=f"found={sqlite_found}")

    external_found = contains_external_url(html + js + css)
    record(not external_found, "no external URLs in war_room assets", blocking, warnings, detail=f"found={external_found}")

    forbidden_interactions = [
        "add event",
        "edit",
        "delete",
        "save",
        "send",
        "sync",
        "upload",
        "login",
        "编辑",
        "新增",
        "删除",
        "保存",
        "上传",
        "同步",
        "发送",
        "登录",
    ]
    interaction_found = contains_any(js + html, forbidden_interactions)
    record(
        not interaction_found,
        "no forbidden user action affordances",
        blocking,
        warnings,
        detail=f"found={interaction_found}",
    )

    package_files = [
        ROOT / "package.json",
        ROOT / "package-lock.json",
        ROOT / "yarn.lock",
        ROOT / "pnpm-lock.yaml",
    ]
    for path in package_files:
        record(not path.exists(), f"no {path.name}", blocking, warnings)
    record(not (ROOT / "node_modules").exists(), "no node_modules directory", blocking, warnings)

    forbidden_html_tokens = [
        "https://",
        "http://",
        "unpkg",
        "cdn",
        "react",
        "vue",
        "bootstrap",
        "tailwind",
        "fonts.googleapis",
    ]
    html_found = contains_any(html, forbidden_html_tokens)
    record(
        not html_found,
        "no HTML external assets or third-party libraries",
        blocking,
        warnings,
        detail=f"found={html_found}",
    )
    record("@import" not in css and "https://" not in css and "http://" not in css, "no CSS external imports", blocking, warnings)

    form_tokens = ["<input", "<textarea", "contenteditable", "type=\"submit\"", "type='submit'", "<form"]
    form_found = contains_any(html + js, form_tokens)
    record(not form_found, "no input / textarea / contenteditable / submit affordances", blocking, warnings, detail=f"found={form_found}")

    allowed_interactions = [
        ("toggle-module" in html and "setupModuleControls" in js and "aria-expanded" in html, "collapse/expand controls exist"),
        ("module-nav" in html and "setupNavigation" in js, "module navigation exists"),
        ("details" in js and "summary" in js, "case detail read-only expansion exists"),
        ("important-field" in js and "important-field" in css, "important field highlight exists"),
        ("flow-map" in js and "flow-map" in css, "hierarchy visualization exists"),
    ]
    for condition, label in allowed_interactions:
        record(condition, label, blocking, warnings)

    render_targets = [
        "high_value_signals",
        "personal_model_hypotheses",
        "recent_history",
        "advisor_brief",
        "current_situation",
        "todays_action",
        "commitments_and_gates",
        "audit_entry",
        "snapshot_audit",
    ]
    for target in render_targets:
        record(target in js, f"render target supported: {target}", blocking, warnings)

    accessibility_tokens = [
        ("aria-expanded" in html and "aria-expanded" in js, "aria-expanded is present and updated"),
        ("<button" in html, "buttons are present"),
        ("<nav" in html, "nav is present"),
        ("<main" in html, "main is present"),
        ("<section" in html, "sections are present"),
        ("<h1" in html and "<h2" in html and "<h3" in js, "headings h1-h3 are present"),
        (
            "real_war_room_snapshot_v1.json" in js and "scripts/build_real_war_room_snapshot.py" in js,
            "clear real snapshot read error exists",
        ),
    ]
    for condition, label in accessibility_tokens:
        record(condition, label, blocking, warnings)

    record(
        "blocking_issues" in js and "warnings" in js and "known_limitations" in js and "can_enter_w2" in js,
        "audit fields visible",
        blocking,
        warnings,
    )
    record("@media" in css, "responsive CSS exists", blocking, warnings)

    first_screen_markers = [
        ("real-war-room-brief" in html, "W5D real brief container exists"),
        ("real-one-sentence" in html, "W5D one sentence situation exists"),
        ("real-direct-judgment" in html, "W5D direct judgment exists"),
        ("real-only-action" in html, "W5D only action exists"),
        ("real-avoid-list" in html, "W5D avoid list exists"),
        ("real-main-tension" in html, "W5D main tension exists"),
        ("historical-shell" in html, "W5D historical secondary area exists"),
        ("real_war_room_snapshot_v1.json" in js, "W5D JS reads real snapshot"),
        ("war_room_snapshot_v1.json" in js, "W5D JS retains historical snapshot"),
    ]
    for condition, label in first_screen_markers:
        record(condition, label, blocking, warnings)

    print(f"blocking_issues_count: {len(blocking)}")
    print(f"warnings_count: {len(warnings)}")
    print(f"allow_next_stage: {str(not blocking).lower()}")
    print(f"recommend_w6e_manual_acceptance: {str(not blocking).lower()}")

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
