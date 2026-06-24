from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    ROOT / "app" / "history.html",
    ROOT / "app" / "history.js",
    ROOT / "app" / "history.css",
    ROOT / "data" / "history_snapshot_v1.json",
]
PACKAGE_FILES = [
    ROOT / "package.json",
    ROOT / "package-lock.json",
    ROOT / "yarn.lock",
    ROOT / "pnpm-lock.yaml",
]


def check(condition: bool, label: str, failures: list[str], detail: str = ""):
    status = "passed" if condition else "failed"
    suffix = f" - {detail}" if detail else ""
    print(f"{label}: {status}{suffix}")
    if not condition:
        failures.append(f"{label}: {detail or 'failed'}")


def main():
    failures: list[str] = []
    for path in REQUIRED:
      check(path.exists(), f"exists {path.relative_to(ROOT)}", failures)

    history_js = (ROOT / "app" / "history.js").read_text(encoding="utf-8") if (ROOT / "app" / "history.js").exists() else ""
    history_html = (ROOT / "app" / "history.html").read_text(encoding="utf-8") if (ROOT / "app" / "history.html").exists() else ""
    history_css = (ROOT / "app" / "history.css").read_text(encoding="utf-8") if (ROOT / "app" / "history.css").exists() else ""

    check("history_snapshot_v1.json" in history_js, "history.js references history_snapshot_v1.json", failures)
    check("fetch(" in history_js, "history.js uses fetch", failures)
    for field in ["phase_context", "evidence_chain", "revision_explanation", "audit_readiness"]:
        check(field in history_js, f"history.js renders {field}", failures)
    for label in ["Phase Context", "Evidence Chain", "Revision Explanation", "Audit Readiness"]:
        check(label in history_html or label.lower().replace(" ", "_") in history_js, f"history page has {label} module", failures)
    check(".audit-module" in history_css, "history.css has audit module style", failures)
    forbidden_js_tokens = [
        "sqlite",
        "sql.js",
        ".db",
        "openDatabase",
        "indexedDB",
        "localStorage.setItem",
        "sessionStorage.setItem",
        "XMLHttpRequest",
        "method: \"POST\"",
        "method: 'POST'",
        "method: \"PUT\"",
        "method: 'PUT'",
        "method: \"DELETE\"",
        "method: 'DELETE'",
        ".open(\"POST\"",
        ".open('POST'",
        ".open(\"PUT\"",
        ".open('PUT'",
        ".open(\"DELETE\"",
        ".open('DELETE'",
    ]
    found_forbidden = [token for token in forbidden_js_tokens if token.lower() in history_js.lower()]
    check(not found_forbidden, "history.js has no database/write logic", failures, f"found={found_forbidden}")
    check("history.js" in history_html and "history.css" in history_html, "history.html links assets", failures)

    existing_packages = [path for path in PACKAGE_FILES if path.exists()]
    check(not existing_packages, "no package manager files", failures, ", ".join(str(p.relative_to(ROOT)) for p in existing_packages))

    node_modules = ROOT / "node_modules"
    check(not node_modules.exists(), "no node_modules directory", failures)

    print("validation_status:", "passed" if not failures else "failed")
    if failures:
        print("failure_reasons:")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
