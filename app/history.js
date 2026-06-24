const SNAPSHOT_PATH = "../data/history_snapshot_v1.json";

const state = {
  snapshot: null,
  selectedIndex: 0,
};

const sections = [
  "test_case",
  "event",
  "candidate_memory",
  "hypothesis",
  "signal",
  "touchpoint",
  "feedback",
  "outcome",
  "model_revision",
  "phase_context",
  "evidence_chain",
  "revision_explanation",
  "audit_readiness",
];

const evidenceOrder = [
  "source_input",
  "event_evidence",
  "hypothesis_evidence",
  "signal_evidence",
  "touchpoint_evidence",
  "feedback_evidence",
  "outcome_evidence",
  "revision_evidence",
];

function byId(id) {
  return document.getElementById(id);
}

function text(value) {
  if (value === null || value === undefined || value === "") return "not_available_in_v1_snapshot";
  if (typeof value === "object") return JSON.stringify(value, null, 2);
  return String(value);
}

function short(value, size = 90) {
  const content = text(value).replace(/\s+/g, " ").trim();
  if (content.length <= size) return content;
  return `${content.slice(0, size)}...`;
}

function escapeHtml(value) {
  return text(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function formatScore(value) {
  const num = Number(value);
  if (!Number.isFinite(num)) return "not_available_in_v1_snapshot";
  return num.toFixed(2);
}

function yesNo(value) {
  return value === true ? "true" : value === false ? "false" : "not_available_in_v1_snapshot";
}

function renderMetric(label, value) {
  return `<div class="metric"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`;
}

function countComplete(cases, key) {
  return cases.filter((item) => Boolean(item[key])).length;
}

function percent(count, total) {
  if (!total) return "0%";
  return `${Math.round((count / total) * 100)}%`;
}

function countBy(cases, predicate) {
  return cases.filter(predicate).length;
}

function blockerCount(item) {
  return item.audit_readiness?.audit_blockers?.length || 0;
}

function averageAuditScore(cases) {
  const values = cases
    .map((item) => Number(item.audit_readiness?.audit_score_estimate))
    .filter((value) => Number.isFinite(value));
  if (!values.length) return "not_available_in_v1_snapshot";
  return (values.reduce((sum, value) => sum + value, 0) / values.length).toFixed(2);
}

function highValueSignalsComplete(cases) {
  const highValue = new Set([
    "judgment_quality_risk",
    "platform_competition_risk",
    "scope_creep_risk",
    "commitment_gate",
    "progress_signal",
    "stage_transition_signal",
  ]);
  const highCases = cases.filter((item) => highValue.has(item.signal?.signal_type));
  const touched = highCases.filter((item) => Boolean(item.touchpoint)).length;
  return `${touched}/${highCases.length}`;
}

function renderSummary(snapshot) {
  const summary = snapshot.summary || {};
  const cases = snapshot.cases || [];
  const total = cases.length;
  const run = snapshot.test_run || {};
  const blockers = cases.reduce((sum, item) => sum + blockerCount(item), 0);
  byId("summary-grid").innerHTML = [
    renderMetric("test_run", run.test_name || run.id || "-"),
    renderMetric("cases", summary.case_count ?? total),
    renderMetric("average_score", formatScore(summary.average_score)),
    renderMetric("signal_score", formatScore(summary.signal_recognition_average || run.signal_score)),
    renderMetric("anti_compliance", formatScore(summary.counter_alignment_average || run.counter_alignment_score)),
    renderMetric("high_value_touchpoints", highValueSignalsComplete(cases)),
    renderMetric("phase_context", percent(countComplete(cases, "phase_context"), total)),
    renderMetric("evidence_chain", percent(countComplete(cases, "evidence_chain"), total)),
    renderMetric("revision_explanation", percent(countComplete(cases, "revision_explanation"), total)),
    renderMetric(
      "follow_up_validation",
      percent(countBy(cases, (item) => Boolean(item.revision_explanation?.follow_up_validation)), total),
    ),
    renderMetric("audit_blockers", blockers),
    renderMetric("avg_audit_score", averageAuditScore(cases)),
  ].join("");
}

function renderDistribution(id, distribution) {
  const entries = Object.entries(distribution || {});
  if (!entries.length) {
    byId(id).innerHTML = '<p class="empty">暂无分布数据。</p>';
    return;
  }
  byId(id).innerHTML = `<ul class="dist-list">${entries
    .map(([key, value]) => `<li><span>${escapeHtml(key)}</span><strong>${escapeHtml(value)}</strong></li>`)
    .join("")}</ul>`;
}

function revisionReasonById() {
  const result = {};
  (state.snapshot?.cases || []).forEach((item) => {
    const id = item.model_revision?.id;
    if (id) result[id] = item.revision_explanation?.confidence_delta_reason || "not_available_in_v1_snapshot";
  });
  return result;
}

function renderConfidenceChanges(changes) {
  const reasons = revisionReasonById();
  const rows = (changes || [])
    .map(
      (item) => `<tr>
        <td>${escapeHtml(item.id)}</td>
        <td>${escapeHtml(item.hypothesis_key)}</td>
        <td class="confidence-change">${escapeHtml(formatScore(item.old_confidence))} -> ${escapeHtml(formatScore(item.new_confidence))}</td>
        <td>${escapeHtml(item.revision_type)}</td>
        <td>${escapeHtml(short(reasons[item.id], 160))}</td>
      </tr>`,
    )
    .join("");
  byId("confidence-changes").innerHTML = rows || '<tr><td colspan="5">暂无置信度变化。</td></tr>';
}

function caseInput(item) {
  return item.test_case?.input_text || item.event?.raw_input || item.event?.content || "";
}

function renderCases(cases) {
  const rows = cases
    .map((item, index) => {
      const selected = index === state.selectedIndex ? "selected" : "";
      return `<tr class="${selected}" data-index="${index}">
        <td><button type="button" data-index="${index}">${escapeHtml(item.test_case?.id || `case_${index + 1}`)}</button></td>
        <td>${escapeHtml(short(caseInput(item)))}</td>
        <td>${escapeHtml(formatScore(item.test_case?.total_score))}</td>
        <td>${escapeHtml(item.signal?.signal_type)}</td>
        <td>${escapeHtml(formatScore(item.audit_readiness?.audit_score_estimate))}</td>
        <td>${escapeHtml(yesNo(item.audit_readiness?.has_phase_context))}</td>
        <td>${escapeHtml(yesNo(item.audit_readiness?.has_specific_revision_explanation))}</td>
        <td>${escapeHtml(yesNo(item.audit_readiness?.has_follow_up_validation))}</td>
        <td>${escapeHtml(blockerCount(item))}</td>
      </tr>`;
    })
    .join("");
  byId("case-list").innerHTML = rows || '<tr><td colspan="9">暂无 case。</td></tr>';
  byId("case-list").querySelectorAll("button[data-index]").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedIndex = Number(button.dataset.index);
      renderCases(state.snapshot.cases || []);
      renderCaseDetail(state.snapshot.cases[state.selectedIndex]);
    });
  });
}

function renderValue(value) {
  if (Array.isArray(value)) {
    if (!value.length) return '<p class="empty">not_available_in_v1_snapshot</p>';
    return `<ul class="value-list">${value.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
  }
  if (typeof value === "boolean") return `<pre>${escapeHtml(yesNo(value))}</pre>`;
  return `<pre>${escapeHtml(text(value))}</pre>`;
}

function renderObject(value, preferredOrder = []) {
  if (!value) return '<p class="empty">missing</p>';
  const keys = [
    ...preferredOrder.filter((key) => Object.prototype.hasOwnProperty.call(value, key)),
    ...Object.keys(value).filter((key) => !preferredOrder.includes(key)),
  ];
  const rows = keys
    .map((key) => `<div class="kv"><span>${escapeHtml(key)}</span>${renderValue(value[key])}</div>`)
    .join("");
  return `<div class="kv-list">${rows}</div>`;
}

function sectionOrder(section) {
  if (section === "phase_context") {
    return [
      "current_phase",
      "phase_goal",
      "forbidden_until_passed",
      "entry_gate",
      "current_best_action",
      "why_this_case_matters_in_phase",
    ];
  }
  if (section === "evidence_chain") return evidenceOrder;
  if (section === "revision_explanation") {
    return [
      "original_hypothesis",
      "feedback_type",
      "feedback_impact",
      "confidence_change",
      "confidence_delta_reason",
      "follow_up_validation",
      "future_judgment_impact",
    ];
  }
  if (section === "audit_readiness") {
    return [
      "has_explicit_evidence_chain",
      "has_phase_context",
      "has_specific_revision_explanation",
      "has_follow_up_validation",
      "has_future_judgment_impact",
      "audit_score_estimate",
      "audit_blockers",
    ];
  }
  return [];
}

function renderCaseDetail(item) {
  if (!item) {
    byId("case-detail").textContent = "请选择一条 case 查看完整链路。";
    return;
  }
  byId("case-detail").innerHTML = sections
    .map((section) => {
      const enhanced = ["phase_context", "evidence_chain", "revision_explanation", "audit_readiness"].includes(section)
        ? " audit-module"
        : "";
      return `<article class="chain-block${enhanced}"><h3>${escapeHtml(section)}</h3>${renderObject(item[section], sectionOrder(section))}</article>`;
    })
    .join("");
}

function renderAuditFlags(flags) {
  if (!flags || !flags.length) {
    byId("audit-flags").innerHTML = '<p class="ok">未发现阻断性审计问题。</p>';
    return;
  }
  const high = flags.filter((flag) => flag.severity === "high").length;
  const intro = high
    ? `<p class="warn">发现 ${high} 个高严重度审计问题。</p>`
    : '<p class="ok">未发现阻断性审计问题。</p>';
  const items = flags
    .map(
      (flag) => `<li>
        <strong>${escapeHtml(flag.type)}</strong>
        <span>${escapeHtml(flag.severity || "-")}</span>
        <p>${escapeHtml(flag.case_id || flag.note || "-")}</p>
      </li>`,
    )
    .join("");
  byId("audit-flags").innerHTML = `${intro}<ul class="flag-list">${items}</ul>`;
}

function render(snapshot) {
  state.snapshot = snapshot;
  state.selectedIndex = 0;
  renderSummary(snapshot);
  renderDistribution("signal-distribution", snapshot.signal_distribution);
  renderDistribution("hypothesis-distribution", snapshot.hypothesis_distribution);
  renderConfidenceChanges(snapshot.confidence_changes);
  renderCases(snapshot.cases || []);
  renderCaseDetail((snapshot.cases || [])[0]);
  renderAuditFlags(snapshot.audit_flags || []);
  byId("load-status").textContent = "历史快照已加载。";
}

async function loadSnapshot() {
  try {
    const response = await fetch(SNAPSHOT_PATH, { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const snapshot = await response.json();
    render(snapshot);
  } catch (error) {
    byId("load-status").innerHTML =
      "无法读取 history_snapshot_v1.json。请通过本地静态服务器访问，例如 http://127.0.0.1:8766/app/history.html 或调整服务器根目录。";
  }
}

loadSnapshot();
