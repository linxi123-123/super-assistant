const $ = s => document.querySelector(s);
const API = window.location.protocol === "file:" ? "http://127.0.0.1:8000" : "";
let currentJobId = null;
let pollTimer = null;
let convo = [];

function esc(v) { return String(v||"").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;"); }

// ── Sidebar navigation ──────────────────────────────────────

document.querySelectorAll(".side-item").forEach(el => {
  el.addEventListener("click", () => {
    document.querySelectorAll(".side-item").forEach(n => n.classList.remove("active"));
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

  // Hide brain welcome
  const brain = $("#brainStage");
  if (brain) brain.style.display = "none";

  appendUserMessage(q);
  await sendToClaudeWorker(q);
});

function autoResize(el) { el.style.height = "auto"; el.style.height = Math.min(el.scrollHeight, 140) + "px"; }
$("#chatInput").addEventListener("input", () => autoResize($("#chatInput")));
$("#chatInput").addEventListener("keydown", e => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); $("#chatForm").dispatchEvent(new Event("submit")); }
});

// ── Core: Local Claude Worker ───────────────────────────────

const STAGES = [
  "正在接收你的问题",
  "正在连接长期记忆",
  "正在整理相关上下文",
  "正在调动本机 Claude Code",
  "正在合成答案",
  "整理完成"
];

let procCardEl = null;

async function sendToClaudeWorker(q) {
  if (currentJobId) { clearTimeout(pollTimer); }
  disableInput(true);

  // Show processing card
  procCardEl = appendProcessingCard();
  setStage(0, "current");

  try {
    const r = await fetch(`${API}/api/local-agent/jobs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: "default_user",
        task_type: "deep_reasoning",
        question: q,
        context: { source: "main_chat_ui", mode: "local_claude_worker_default", use_llm_wiki: true }
      })
    });

    if (!r.ok) {
      const errText = await r.text().catch(() => "");
      if (r.status === 404 || r.status === 405) throw new Error("worker_api_unavailable");
      throw new Error(`status_${r.status}`);
    }

    const data = await r.json();
    currentJobId = data.job_id;

    setStage(0, "done");
    setStage(1, "current");
    setStage(2, "current");
    updateStatus("处理中", "active");
    $("#currentTaskCard").hidden = false;
    $("#currentTaskText").textContent = "分析中…";

    pollJob(currentJobId);

  } catch (err) {
    removeProcessingCard();
    disableInput(false);
    const msg = err.message || "";

    if (msg.includes("worker_api_unavailable")) {
      appendError("本机外脑暂时没接上，我不会乱答。<br><small>请确认本机 <code>local_claude_worker.py</code> 正在运行。</small>");
    } else {
      appendError("请求失败：" + esc(msg));
    }
    updateStatus("待命", "dim");
    $("#currentTaskCard").hidden = true;
  }
}

// ── Polling ─────────────────────────────────────────────────

async function pollJob(jobId) {
  try {
    const r = await fetch(`${API}/api/local-agent/jobs/${jobId}`);
    if (!r.ok) { pollTimer = setTimeout(() => pollJob(jobId), 2000); return; }
    const data = await r.json();

    if (data.status === "pending") {
      setStage(1, "current");
      pollTimer = setTimeout(() => pollJob(jobId), 2000);
    } else if (data.status === "claimed") {
      setStage(1, "done");
      setStage(2, "done");
      setStage(3, "current");
      setStage(4, "current");
      $("#currentTaskText").textContent = "Claude 推理中";
      pollTimer = setTimeout(() => pollJob(jobId), 3000);
    } else if (data.status === "running") {
      setStage(4, "current");
      pollTimer = setTimeout(() => pollJob(jobId), 3000);
    } else if (data.status === "succeeded") {
      setStage(3, "done");
      setStage(4, "done");
      setStage(5, "done");
      removeProcessingCard();
      disableInput(false);
      showAIResult(data);
      updateStatus("在线", "online");
      $("#currentTaskCard").hidden = true;
      showDebug(data);
      currentJobId = null;
    } else if (data.status === "failed") {
      removeProcessingCard();
      disableInput(false);
      appendError("本机外脑暂时没接上，我不会乱答。<br><small>请确认本机 <code>local_claude_worker.py</code> 正在运行。</small>");
      updateStatus("待命", "dim");
      $("#currentTaskCard").hidden = true;
      currentJobId = null;
    } else {
      pollTimer = setTimeout(() => pollJob(jobId), 3000);
    }
  } catch (_) {
    pollTimer = setTimeout(() => pollJob(jobId), 3000);
  }
}

// ── Processing UI ───────────────────────────────────────────

function appendProcessingCard() {
  const div = document.createElement("div");
  div.className = "msg msg-ai";
  div.id = "procMsg";
  let html = `<div class="msg-avatar">谋</div><div class="msg-body"><div class="proc-card"><div class="proc-stages">`;
  STAGES.forEach((s, i) => {
    html += `<div class="proc-stage" id="stg${i}"><span class="dot"></span>${s}</div>`;
  });
  html += `</div></div></div></div>`;
  div.innerHTML = html;
  $("#convArea").appendChild(div);
  div.scrollIntoView({ behavior: "smooth" });
  return div;
}

function setStage(idx, state) {
  const el = $(`#stg${idx}`);
  if (!el) return;
  el.classList.remove("active", "done", "current");
  if (state === "current") el.classList.add("active", "current");
  if (state === "done") el.classList.add("done");
}

function removeProcessingCard() {
  setTimeout(() => {
    const el = $("#procMsg");
    if (el) el.remove();
  }, 600);
}

// ── AI result ───────────────────────────────────────────────

function showAIResult(data) {
  const r = data.result || {};
  const answer = r.answer || "（未获取到回答）";
  convo.push({ role: "ai", content: answer, meta: r, ts: Date.now() });

  const div = document.createElement("div");
  div.className = "msg msg-ai";
  let html = `<div class="msg-avatar">谋</div><div class="msg-body">`;

  // Opening line
  html += `<div class="ai-opening">我接到了，结果整理好了。</div>`;

  // Main answer block
  html += `<div class="ai-answer-block">${fmt(answer)}</div>`;

  // Structured cards
  html += `<div class="info-cards">`;

  if (r.confidence) {
    html += `<div class="info-card"><h4>置信度</h4><span class="conf-badge conf-${esc(r.confidence)}">${esc(r.confidence)}</span></div>`;
  }
  if (r.summary) {
    html += `<div class="info-card"><h4>处理摘要</h4><p>${esc(r.summary)}</p></div>`;
  }
  if (r.next_actions && r.next_actions.length) {
    html += `<div class="info-card"><h4>下一步建议</h4><ul>${r.next_actions.map(a => `<li>${esc(a)}</li>`).join("")}</ul></div>`;
  }
  if (r.memory_updates && r.memory_updates.length) {
    html += `<div class="info-card"><h4>建议更新记忆</h4>`;
    r.memory_updates.forEach(m => {
      html += `<p style="margin-bottom:8px"><strong>📁 ${esc(m.target)}</strong><br>${esc(m.content)}<br><small style="color:var(--muted)">${esc(m.reason)}</small></p>`;
    });
    html += `</div>`;
  }

  html += `</div></div></div>`;
  div.innerHTML = html;
  $("#convArea").appendChild(div);
  div.scrollIntoView({ behavior: "smooth" });
}

// ── Helpers ─────────────────────────────────────────────────

function appendUserMessage(text) {
  convo.push({ role: "user", content: text, ts: Date.now() });
  const div = document.createElement("div");
  div.className = "msg msg-user";
  div.innerHTML = `<div class="msg-avatar">U</div><div class="msg-body"><div class="msg-bubble">${esc(text)}</div></div>`;
  $("#convArea").appendChild(div);
  div.scrollIntoView({ behavior: "smooth" });
}

function appendError(html) {
  const div = document.createElement("div");
  div.className = "msg msg-ai";
  div.innerHTML = `<div class="msg-avatar">!</div><div class="msg-body"><div class="error-msg">${html}</div></div>`;
  $("#convArea").appendChild(div);
  div.scrollIntoView({ behavior: "smooth" });
}

function fmt(text) {
  return esc(text)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/^[-•] (.+)$/gm, "<span style='display:block;padding-left:6px;margin:2px 0'>· $1</span>")
    .replaceAll("\n", "<br>");
}

function disableInput(v) {
  $("#sendBtn").disabled = v;
  $("#chatInput").disabled = v;
}

function updateStatus(text, cls) {
  const el = $("#brainStatus");
  if (el) { el.textContent = text; el.className = "status-val " + cls; }
}

function showDebug(data) {
  const r = data.result || {};
  const debug = {
    job_id: data.job_id,
    status: data.status,
    confidence: r.confidence || "—"
  };
  $("#debugToggle").hidden = false;
  $("#debugInfo").innerHTML = `<code>Job:</code> ${esc(debug.job_id)} · ${esc(debug.status)} · confidence: ${esc(debug.confidence)}`;
}

// ── Bootstrap ───────────────────────────────────────────────

fetch(`${API}/api/health`)
  .then(r => r.json())
  .then(() => { updateStatus("在线", "online"); })
  .catch(() => {
    updateStatus("离线", "dim");
    $("#memoryStatus").textContent = "未连接";
    $("#memoryStatus").className = "status-val dim";
  });
