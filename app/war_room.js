(function () {
  "use strict";

  const REAL_SNAPSHOT_PATH = "../data/real_war_room_snapshot_v1.json";
  const SNAPSHOT_PATH = "../data/war_room_snapshot_v1.json";
  const FALLBACK = "not_available_in_v1_snapshot";
  const W6D_CURRENT_ACTION = "当前唯一动作：完成 W6D 当前语境最小页面改造，并等待 W6E 人工验收。";
  const W6D_VALID_WINDOW = "本判断仅适用于当前 W5E/W6/W6D 验收后的项目推进决策，不代表长期战略判断。";
  const statusEl = document.getElementById("load-status");

  function value(input) {
    if (input === null || input === undefined || input === "") return FALLBACK;
    return input;
  }

  function text(input) {
    return String(value(input));
  }

  function escapeHtml(input) {
    return text(input)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function list(items) {
    if (!Array.isArray(items) || items.length === 0) {
      return `<p class="empty">${FALLBACK}</p>`;
    }
    return `<ul>${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
  }

  function field(label, input) {
    const importantLabels = [
      "current_phase",
      "current_best_action",
      "main_risk",
      "counter_argument",
      "recommended_action",
      "consequence_if_ignored",
      "action",
      "can_enter_next_stage",
      "audit_status",
      "required_sections_present",
      "can_support_w2_static_page",
      "can_enter_w2"
    ];
    const className = importantLabels.includes(label) ? "field important-field" : "field";
    return `
      <div class="${className}">
        <dt>${escapeHtml(label)}</dt>
        <dd>${escapeHtml(input)}</dd>
      </div>
    `;
  }

  function score(label, input) {
    return `<span class="metric"><strong>${escapeHtml(label)}</strong>${escapeHtml(input === null || input === undefined ? FALLBACK : input)}</span>`;
  }

  function renderInto(id, html) {
    const node = document.querySelector(`#${id} .panel-body`);
    if (node) node.innerHTML = html;
  }

  function renderCurrentSituation(data) {
    renderInto("current-situation", `
      <dl class="field-list">
        ${field("current_phase", data.current_phase)}
        ${field("current_goal", data.current_goal)}
        ${field("primary_project", data.primary_project)}
        ${field("main_risk", data.main_risk)}
        ${field("main_opportunity", data.main_opportunity)}
        ${field("current_best_action", data.current_best_action)}
      </dl>
      <h3>evidence</h3>
      ${list(data.evidence)}
    `);
  }

  function renderAdvisorBrief(data) {
    renderInto("advisor-brief", `
      <h3>${escapeHtml(data.title)}</h3>
      <p class="brief-message">${escapeHtml(data.message)}</p>
      <div class="flow-map" aria-label="Advisor brief flow">
        <span>Signal</span>
        <span>Evidence</span>
        <span>Counter</span>
        <span>Action</span>
        <span>Consequence</span>
      </div>
      <dl class="field-list">
        ${field("why_now", data.why_now)}
        ${field("counter_argument", data.counter_argument)}
        ${field("recommended_action", data.recommended_action)}
        ${field("consequence_if_ignored", data.consequence_if_ignored)}
      </dl>
      <h3>evidence_chain</h3>
      ${list(data.evidence_chain)}
    `);
  }

  function renderTodaysAction(data) {
    renderInto("todays-action", `
      <dl class="field-list">
        ${field("action", data.action)}
        ${field("why_this_action", data.why_this_action)}
      </dl>
      <h3>completion_criteria</h3>
      ${list(data.completion_criteria)}
      <h3>not_doing_risks</h3>
      ${list(data.not_doing_risks)}
    `);
  }

  function renderSignals(items) {
    renderInto("high-value-signals", collection(items, (item) => `
      <article class="item">
        <div class="item-head">
          <h3>${escapeHtml(item.signal_type)}</h3>
          <span>${escapeHtml(item.case_id)}</span>
        </div>
        <p>${escapeHtml(item.description)}</p>
        <div class="metrics">
          ${score("importance", item.importance_score)}
          ${score("urgency", item.urgency_score)}
          ${score("actionability", item.actionability_score)}
          ${score("confidence", item.confidence)}
        </div>
        <dl class="field-list">
          ${field("evidence", item.evidence)}
          ${field("recommended_action", item.recommended_action)}
          ${field("counter_argument", item.counter_argument)}
          ${field("touchpoint_summary", item.touchpoint_summary)}
        </dl>
      </article>
    `));
  }

  function renderHypotheses(items) {
    renderInto("personal-model-hypotheses", collection(items, (item) => `
      <article class="item">
        <div class="item-head">
          <h3>${escapeHtml(item.hypothesis_key)}</h3>
          <span>${escapeHtml(item.case_id)}</span>
        </div>
        <p>${escapeHtml(item.content)}</p>
        <div class="flow-map hypothesis-flow" aria-label="Hypothesis revision flow">
          <span>Hypothesis</span>
          <span>Evidence</span>
          <span>Revision</span>
          <span>Validation</span>
          <span>Future Impact</span>
        </div>
        <div class="metrics">
          ${score("confidence", item.confidence)}
          ${score("confidence_change", item.confidence_change)}
        </div>
        <dl class="field-list">
          ${field("evidence", item.evidence)}
          ${field("counter_evidence", item.counter_evidence)}
          ${field("validation_plan", item.validation_plan)}
          ${field("latest_revision_reason", item.latest_revision_reason)}
          ${field("follow_up_validation", item.follow_up_validation)}
          ${field("future_judgment_impact", item.future_judgment_impact)}
        </dl>
      </article>
    `));
  }

  function renderGates(data) {
    renderInto("commitments-gates", `
      <dl class="field-list">
        ${field("current_stage_gate", data.current_stage_gate)}
        ${field("next_stage", data.next_stage)}
        ${field("can_enter_next_stage", data.can_enter_next_stage)}
      </dl>
      <div class="gate-state ${data.can_enter_next_stage ? "gate-open" : "gate-closed"}">
        ${data.can_enter_next_stage ? "允许进入下一阶段" : "当前不得自动进入下一阶段"}
      </div>
      <div class="columns">
        <div>
          <h3>entry_conditions</h3>
          ${list(data.entry_conditions)}
        </div>
        <div>
          <h3>satisfied_conditions</h3>
          ${list(data.satisfied_conditions)}
        </div>
        <div>
          <h3>unsatisfied_conditions</h3>
          ${list(data.unsatisfied_conditions)}
        </div>
        <div>
          <h3>forbidden_until_passed</h3>
          ${list(data.forbidden_until_passed)}
        </div>
      </div>
      <h3>evidence</h3>
      ${list(data.evidence)}
    `);
  }

  function renderRecentHistory(items) {
    renderInto("recent-history", collection(items, (item) => `
      <details class="item">
        <summary>
          <span>${escapeHtml(item.case_id)}</span>
          <strong>${escapeHtml(item.signal_type)}</strong>
        </summary>
        <dl class="field-list">
          ${field("input_summary", item.input_summary)}
          ${field("hypothesis_key", item.hypothesis_key)}
          ${field("total_score", item.total_score)}
          ${field("audit_score_estimate", item.audit_score_estimate)}
          ${field("touchpoint_summary", item.touchpoint_summary)}
          ${field("revision_summary", item.revision_summary)}
        </dl>
      </details>
    `));
  }

  function renderAuditEntry(data) {
    const url = text(data.history_panel_url);
    renderInto("audit-entry", `
      <dl class="field-list">
        <div class="field">
          <dt>history_panel_url</dt>
          <dd><a href="${escapeHtml(url)}">${escapeHtml(url)}</a></dd>
        </div>
        ${field("history_snapshot_path", data.history_snapshot_path)}
        ${field("war_room_snapshot_path", data.war_room_snapshot_path)}
        ${field("latest_manual_acceptance", data.latest_manual_acceptance)}
        ${field("audit_status", data.audit_status)}
      </dl>
      <h3>audit_blockers</h3>
      ${list(data.audit_blockers)}
    `);
  }

  function renderSourceAudit(metadata, audit) {
    renderInto("source-audit", `
      <div class="metrics">
        ${score("used_sources", Array.isArray(metadata.used_sources) ? metadata.used_sources.length : FALLBACK)}
        ${score("required_sections_present", audit.required_sections_present)}
        ${score("can_support_w2_static_page", audit.can_support_w2_static_page)}
        ${score("can_enter_w2", audit.can_enter_w2)}
      </div>
      <div class="columns">
        <div>
          <h3>missing_sources</h3>
          ${list(metadata.missing_sources)}
        </div>
        <div>
          <h3>known_limitations</h3>
          ${list(metadata.known_limitations)}
        </div>
        <div>
          <h3>warnings</h3>
          ${list(audit.warnings)}
        </div>
        <div>
          <h3>blocking_issues</h3>
          ${list(audit.blocking_issues)}
        </div>
      </div>
    `);
  }

  function unique(items) {
    const seen = new Set();
    return (Array.isArray(items) ? items : []).filter((item) => {
      const key = text(item);
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  }

  function setText(id, input) {
    const node = document.getElementById(id);
    if (node) node.textContent = text(input);
  }

  function renderCurrentContext(snapshot) {
    setText("judgment-generated-at", snapshot.generated_at || "判断生成时间不可用");
    setText("judgment-valid-window", W6D_VALID_WINDOW);
    setText("current-action-label", W6D_CURRENT_ACTION);
  }

  function renderRealBrief(snapshot) {
    const current = snapshot.current_situation || {};
    const brief = snapshot.advisor_brief || {};
    const action = snapshot.today_action || {};
    const decision = snapshot.decision_focus || {};
    const avoidItems = unique([...(current.what_not_to_do || []), ...(action.avoid_list || [])]);
    renderCurrentContext(snapshot);
    setText("real-one-sentence", current.one_sentence_situation);
    setText("real-direct-judgment", brief.direct_judgment);
    setText("real-why-this-matters", brief.why_this_matters);
    setText("real-counter-argument", brief.counter_argument);
    setText("real-consequence", brief.consequence_if_ignored);
    setText("real-only-action", W6D_CURRENT_ACTION);
    setText("real-done-definition", action.done_definition);
    setText("real-time-box", action.time_box);
    setText("real-main-tension", current.main_tension);
    setText("real-decision-question", decision.question);
    setText("real-recommended-option", decision.recommended_option ? `推荐路径：${decision.recommended_option}` : "");
    setText("real-decision-reason", decision.reason ? `理由：${decision.reason}` : "");
    const avoidList = document.getElementById("real-avoid-list");
    if (avoidList) {
      avoidList.innerHTML = avoidItems.length ? avoidItems.map((item) => `<li>${escapeHtml(item)}</li>`).join("") : `<li>${FALLBACK}</li>`;
    }
    const p2 = document.getElementById("real-p2-detail");
    if (p2) {
      p2.innerHTML = `
        <h4>evidence_chain</h4>
        ${collection(snapshot.evidence_chain || [], (item) => `
          <article class="item compact-item">
            ${field("source_event_id", item.source_event_id)}
            ${field("evidence_text", item.evidence_text)}
            ${field("supports", item.supports)}
          </article>
        `)}
        <h4>stage_gate</h4>
        <dl class="field-list">
          ${field("current_gate", snapshot.stage_gate && snapshot.stage_gate.current_gate)}
          ${field("can_enter_next_stage", snapshot.stage_gate && snapshot.stage_gate.can_enter_next_stage)}
        </dl>
        <h4>audit</h4>
        <dl class="field-list">
          ${field("uses_real_events", snapshot.audit && snapshot.audit.uses_real_events)}
          ${field("uses_test_cases", snapshot.audit && snapshot.audit.uses_test_cases)}
          ${field("blocks_external_intel", snapshot.audit && snapshot.audit.blocks_external_intel)}
          ${field("blocks_execution_agent", snapshot.audit && snapshot.audit.blocks_execution_agent)}
        </dl>
      `;
    }
  }

  function setupModuleControls() {
    document.querySelectorAll(".module-panel").forEach((panel) => {
      const button = panel.querySelector(".toggle-module");
      const body = panel.querySelector(".panel-body");
      if (!button || !body) return;
      button.addEventListener("click", () => {
        const collapsed = panel.classList.toggle("is-collapsed");
        body.hidden = collapsed;
        button.setAttribute("aria-expanded", String(!collapsed));
        button.textContent = collapsed ? "展开" : "收起";
      });
    });
  }

  function setupNavigation() {
    document.querySelectorAll(".module-nav a").forEach((link) => {
      link.addEventListener("click", () => {
        document.querySelectorAll(".module-nav a").forEach((item) => item.classList.remove("active"));
        link.classList.add("active");
      });
    });
  }

  function collection(items, renderer) {
    if (!Array.isArray(items) || items.length === 0) {
      return `<p class="empty">${FALLBACK}</p>`;
    }
    return `<div class="item-list">${items.map(renderer).join("")}</div>`;
  }

  function render(snapshot) {
    renderCurrentSituation(snapshot.current_situation || {});
    renderAdvisorBrief(snapshot.advisor_brief || {});
    renderTodaysAction(snapshot.todays_action || {});
    renderSignals(snapshot.high_value_signals || []);
    renderHypotheses(snapshot.personal_model_hypotheses || []);
    renderGates(snapshot.commitments_and_gates || {});
    renderRecentHistory(snapshot.recent_history || []);
    renderAuditEntry(snapshot.audit_entry || {});
    renderSourceAudit(snapshot.source_metadata || {}, snapshot.snapshot_audit || {});
    setupModuleControls();
    setupNavigation();
  }

  Promise.all([
    fetch(REAL_SNAPSHOT_PATH).then((response) => {
      if (!response.ok) throw new Error(`real snapshot HTTP ${response.status}`);
      return response.json();
    }),
    fetch(SNAPSHOT_PATH).then((response) => {
      if (!response.ok) return null;
      return response.json();
    }).catch(() => null)
  ])
    .then(([realSnapshot, historicalSnapshot]) => {
      renderRealBrief(realSnapshot);
      if (historicalSnapshot) {
        render(historicalSnapshot);
        statusEl.textContent = "real_war_room_snapshot_v1.json 已加载；war_room_snapshot_v1.json 次级模块已加载。";
      } else {
        statusEl.textContent = "real_war_room_snapshot_v1.json 已加载；war_room_snapshot_v1.json 未加载，下方历史模块降级显示。";
        statusEl.classList.add("ok");
        document.querySelectorAll(".historical-shell .panel-body").forEach((node) => {
          node.innerHTML = `<p class="empty">war_room_snapshot_v1.json 未加载，历史测试快照与审计区暂不可用。</p>`;
        });
      }
      statusEl.classList.add("ok");
    })
    .catch((error) => {
      statusEl.textContent = "无法读取 real_war_room_snapshot_v1.json。请先运行 scripts/build_real_war_room_snapshot.py 并通过 scripts/validate_real_war_room_snapshot.py。";
      statusEl.classList.add("error");
      const main = document.querySelector("main");
      if (main) {
        main.insertAdjacentHTML("afterbegin", `<section class="panel error-panel"><h2>读取失败</h2><p>${escapeHtml(error.message)}</p></section>`);
      }
    });
})();
