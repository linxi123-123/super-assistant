const $ = s => document.querySelector(s);
const API = window.location.protocol === "file:" ? "http://127.0.0.1:8000" : "";
let currentJobId = null;
let pollTimer = null;

function esc(v) { return String(v||"").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;"); }

// ── Sidebar toggle ──────────────────────────────────────────

$("#menuToggle")?.addEventListener("click", () => {
  const rail = $("#sideRail");
  const scrim = $("#sidebarScrim");
  const expanded = rail.classList.toggle("open");
  $("#menuToggle").setAttribute("aria-expanded", expanded);
  if (scrim) scrim.hidden = !expanded;
});
$("#sidebarScrim")?.addEventListener("click", () => {
  $("#sideRail").classList.remove("open");
  $("#sidebarScrim").hidden = true;
  $("#menuToggle").setAttribute("aria-expanded", "false");
});
document.querySelectorAll(".rail-item").forEach(el => {
  el.addEventListener("click", () => {
    document.querySelectorAll(".rail-item").forEach(n => n.classList.remove("active"));
    el.classList.add("active");
  });
});

// ── Chat form ───────────────────────────────────────────────

$("#chatForm").addEventListener("submit", async e => {
  e.preventDefault();
  const input = $("#chatInput");
  const q = input.value.trim();
  if (!q || $("#sendBtn").disabled) return;
  input.value = "";
  autoResize(input);
  hideHero();
  showAsking(q);
  await sendToClaudeWorker(q);
});

function autoResize(el) { el.style.height = "auto"; el.style.height = Math.min(el.scrollHeight, 140) + "px"; }
$("#chatInput").addEventListener("input", () => autoResize($("#chatInput")));
$("#chatInput").addEventListener("keydown", e => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); $("#chatForm").dispatchEvent(new Event("submit")); }
});

function hideHero() {
  const hero = document.querySelector(".brain-hero");
  if (hero) hero.style.display = "none";
  const identity = document.querySelector(".identity-area p");
  if (identity) identity.textContent = "正在处理…";
}

// ── Show asking state in answer card ────────────────────────

function showAsking(q) {
  const card = $("#answerCard");
  if (!card) return;
  card.style.display = "";
  $("#answerCopy").innerHTML = `<em>"${esc(q)}"</em>`;
  document.querySelector(".answer-sigil")?.parentElement && (document.querySelector(".answer-meta").innerHTML = `<span class="answer-sigil"></span>外脑 · 收到问题`);
  updateDebug("creating", "-", "正在判断问题类型…");
}

// ── Core: Local Claude Worker ───────────────────────────────

async function sendToClaudeWorker(q) {
  if (currentJobId) { clearTimeout(pollTimer); }
  disableInput(true);
  updateAnswer("正在理解你的问题…", "");

  try {
    const r = await fetch(`${API}/api/local-agent/jobs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: "default_user",
        task_type: "deep_reasoning",
        question: q,
        context: {
          source: "main_chat_ui",
          mode: "local_claude_worker_default",
          use_llm_wiki: true,
          allow_public_research: true,
          answer_policy: "memory_plus_public_research",
          public_research_required_for_current_knowledge: true
        }
      })
    });

    if (!r.ok) {
      const errText = await r.text().catch(() => "");
      if (r.status === 404 || r.status === 405) throw new Error("worker_api_unavailable");
      throw new Error(`status_${r.status}`);
    }

    const data = await r.json();
    currentJobId = data.job_id;
    updateDebug("pending", "-", "任务已创建，等待本机 Worker…");
    setProcessingStage("connecting");
    pollJob(currentJobId);

  } catch (err) {
    disableInput(false);
    const msg = err.message || "";
    if (msg.includes("worker_api_unavailable")) {
      showError("本机外脑暂时没接上<br><small>请确认本机 <code>local_claude_worker.py</code> 正在运行</small>");
    } else {
      showError("请求失败：" + esc(msg));
    }
    updateDebug("error", "-", msg);
  }
}

// ── Processing stages (product copy) ────────────────────────

function setProcessingStage(stage) {
  const stages = {
    connecting: "正在连接你的本机外脑…",
    understanding: "正在判断问题类型…",
    memory_lookup: "正在查找你的长期记忆…",
    public_research: "正在查找公开资料…",
    claude_thinking: "Claude Code 正在综合推理…",
    synthesizing: "正在整理结果…"
  };
  const text = stages[stage] || stage;
  document.querySelector(".answer-meta") && (document.querySelector(".answer-meta").innerHTML = `<span class="answer-sigil"></span>外脑 · ${text}`);
  $("#answerCopy").innerHTML = text;
}

// ── Polling ─────────────────────────────────────────────────

async function pollJob(jobId) {
  try {
    const r = await fetch(`${API}/api/local-agent/jobs/${jobId}`);
    if (!r.ok) { pollTimer = setTimeout(() => pollJob(jobId), 2000); return; }
    const data = await r.json();

    if (data.status === "pending") {
      setProcessingStage("connecting");
      updateDebug("pending", "-", "等待 Worker");
      pollTimer = setTimeout(() => pollJob(jobId), 2000);

    } else if (data.status === "claimed") {
      setProcessingStage("claude_thinking");
      updateDebug("claimed", "-", "Claude Code 推理中");
      pollTimer = setTimeout(() => pollJob(jobId), 3000);

    } else if (data.status === "running") {
      setProcessingStage("claude_thinking");
      pollTimer = setTimeout(() => pollJob(jobId), 3000);

    } else if (data.status === "succeeded") {
      setProcessingStage("synthesizing");
      disableInput(false);
      showAIResult(data);
      currentJobId = null;

    } else if (data.status === "failed") {
      disableInput(false);
      showError("本机外脑暂时没接上<br><small>请确认本机 <code>local_claude_worker.py</code> 正在运行</small>");
      updateDebug("failed", "-", data.error || "处理失败");
      currentJobId = null;

    } else {
      pollTimer = setTimeout(() => pollJob(jobId), 3000);
    }
  } catch (_) {
    pollTimer = setTimeout(() => pollJob(jobId), 3000);
  }
}

// ── Show AI result ──────────────────────────────────────────

function showAIResult(data) {
  const r = data.result || {};
  const mode = r.answer_mode || "unknown";
  const answer = r.answer || "（未获取到回答）";

  // Product status meta
  const modeLabels = {
    personal_memory: "基于你的长期记忆",
    public_research: "基于公开资料查询",
    mixed: "结合你的记忆和公开资料",
    task_execution: "任务规划"
  };
  const statusLabel = modeLabels[mode] || "外脑回答";

  document.querySelector(".answer-meta") && (document.querySelector(".answer-meta").innerHTML = `<span class="answer-sigil"></span>外脑 · ${statusLabel}`);

  // Build answer HTML
  let html = answer;

  // Sources
  if (r.sources && r.sources.length) {
    html += `<br><br><small style="color:var(--muted)">信息来源：`;
    r.sources.forEach((s, i) => {
      if (s.url) {
        html += `${i>0?' · ':''}<a href="${esc(s.url)}" target="_blank" style="color:var(--accent2)">${esc(s.title||s.source)}</a>`;
      } else {
        html += `${i>0?' · ':''}${esc(s.title||s.source)}`;
      }
    });
    html += `</small>`;
  }

  // Confidence
  if (r.confidence) {
    html += `<br><small style="color:var(--muted)">置信度：${esc(r.confidence)}${r.confidence_reason ? ' — '+esc(r.confidence_reason) : ''}</small>`;
  }

  // Next actions
  if (r.next_actions && r.next_actions.length) {
    html += `<br><br><strong>下一步建议：</strong>`;
    r.next_actions.forEach(a => { html += `<br>· ${esc(a)}`; });
  }

  // Memory updates
  if (r.memory_updates && r.memory_updates.length) {
    html += `<br><br><strong>建议更新记忆：</strong>`;
    r.memory_updates.forEach(m => {
      html += `<br>📁 ${esc(m.target)}：${esc(m.content)} <small style="color:var(--muted)">(${esc(m.reason)})</small>`;
    });
  }

  $("#answerCopy").innerHTML = fmt(html);

  // Debug
  updateDebug("succeeded", r.confidence || "-", r.answer_mode || "unknown");
}

// ── Helpers ─────────────────────────────────────────────────

function updateAnswer(text, debugMsg) {
  $("#answerCopy").innerHTML = text;
  if (debugMsg) updateDebug("processing", "-", debugMsg);
}

function showError(html) {
  $("#answerCopy").innerHTML = `<span style="color:var(--red)">${html}</span>`;
  document.querySelector(".answer-meta") && (document.querySelector(".answer-meta").innerHTML = `<span class="answer-sigil"></span>外脑 · 暂时无法响应`);
}

function updateDebug(status, confidence, message) {
  const elJob = $("#debugJobId");
  const elStatus = $("#debugStatus");
  const elConf = $("#debugConfidence");
  const elMsg = $("#debugMessage");
  if (elJob) elJob.textContent = currentJobId || "-";
  if (elStatus) elStatus.textContent = status;
  if (elConf) elConf.textContent = confidence;
  if (elMsg) elMsg.textContent = message;
}

function fmt(text) {
  return esc(text)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/^[-•] (.+)$/gm, "<span style='display:block;padding-left:6px'>· $1</span>")
    .replaceAll("\n", "<br>");
}

function disableInput(v) {
  if ($("#sendBtn")) $("#sendBtn").disabled = v;
  if ($("#chatInput")) $("#chatInput").disabled = v;
}

// ── Bootstrap ───────────────────────────────────────────────

fetch(`${API}/api/health`)
  .then(r => r.json())
  .then(() => { updateDebug("ready", "-", "外脑在线，等待输入"); })
  .catch(() => { updateDebug("offline", "-", "服务器未连接"); });
