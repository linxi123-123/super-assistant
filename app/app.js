const $ = (s) => document.querySelector(s);
const API = window.location.protocol === "file:" ? "http://127.0.0.1:8000" : "";
let currentJobId = null;
let pollTimer = null;
let convo = [];
let processingEl = null;

function esc(v) { return String(v || "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;"); }

// ── Sidebar ─────────────────────────────────────────────────

$("#menuBtn").addEventListener("click", () => {
  $("#sidebar").classList.toggle("open");
  $("#sidebarOverlay").classList.toggle("open");
});
$("#sidebarOverlay").addEventListener("click", () => {
  $("#sidebar").classList.remove("open");
  $("#sidebarOverlay").classList.remove("open");
});
document.querySelectorAll(".nav-item").forEach(el => {
  el.addEventListener("click", () => {
    document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
    el.classList.add("active");
    $("#sidebar").classList.remove("open");
    $("#sidebarOverlay").classList.remove("open");
  });
});

// ── Chat form ──────────────────────────────────────────────

$("#chatForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = $("#chatInput");
  const question = input.value.trim();
  if (!question || $("#sendBtn").disabled) return;
  input.value = "";
  autoResize(input);

  const welcome = $("#welcome");
  if (welcome) welcome.style.display = "none";

  appendUserMessage(question);
  await sendToClaudeWorker(question);
});

function autoResize(el) {
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 140) + "px";
}
$("#chatInput").addEventListener("input", () => autoResize($("#chatInput")));
$("#chatInput").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); $("#chatForm").dispatchEvent(new Event("submit")); }
});

// ── Core: send via Local Claude Worker ──────────────────────

async function sendToClaudeWorker(question) {
  if (currentJobId) { clearTimeout(pollTimer); }
  disableInput(true);

  // Show processing bubble
  processingEl = appendProcessingBubble();

  try {
    const r = await fetch(`${API}/api/local-agent/jobs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: "default_user",
        task_type: "deep_reasoning",
        question: question,
        context: { source: "main_chat_ui", mode: "local_claude_worker_default", use_llm_wiki: true }
      })
    });

    if (!r.ok) {
      const errText = await r.text().catch(() => "");
      if (r.status === 404 || r.status === 405) {
        throw new Error("worker_api_unavailable");
      }
      throw new Error(`status_${r.status}`);
    }

    const data = await r.json();
    currentJobId = data.job_id;
    updateProcessingText("Claude Code 正在思考…");
    pollJob(currentJobId);

  } catch (err) {
    removeProcessingBubble();
    disableInput(false);
    const msg = err.message || String(err);

    if (msg.includes("worker_api_unavailable")) {
      appendErrorMessage("本机 Claude Worker 暂未响应<br><small>请确认本机 <code>local_claude_worker.py</code> 正在运行</small>");
    } else {
      appendErrorMessage(`请求失败：${esc(msg)}`);
    }
  }
}

// ── Poll ────────────────────────────────────────────────────

async function pollJob(jobId) {
  try {
    const r = await fetch(`${API}/api/local-agent/jobs/${jobId}`);
    if (!r.ok) { pollTimer = setTimeout(() => pollJob(jobId), 2000); return; }
    const data = await r.json();

    if (data.status === "pending") {
      updateProcessingText("等待本机连接…");
      pollTimer = setTimeout(() => pollJob(jobId), 2000);
    } else if (data.status === "claimed") {
      updateProcessingText("Claude Code 正在深度推理…");
      pollTimer = setTimeout(() => pollJob(jobId), 3000);
    } else if (data.status === "running") {
      updateProcessingText("推理中…");
      pollTimer = setTimeout(() => pollJob(jobId), 3000);
    } else if (data.status === "succeeded") {
      removeProcessingBubble();
      disableInput(false);
      appendAIResult(data);
      currentJobId = null;
    } else if (data.status === "failed") {
      removeProcessingBubble();
      disableInput(false);
      appendErrorMessage("Claude Worker 处理失败<br><small>" + esc(data.error || "未知错误") + "</small>");
      currentJobId = null;
    } else {
      pollTimer = setTimeout(() => pollJob(jobId), 3000);
    }
  } catch (_) {
    pollTimer = setTimeout(() => pollJob(jobId), 3000);
  }
}

// ── UI: Messages ────────────────────────────────────────────

function appendUserMessage(text) {
  convo.push({ role: "user", content: text, ts: Date.now() });
  const div = document.createElement("div");
  div.className = "msg msg-user";
  div.innerHTML = `
    <div class="msg-avatar">U</div>
    <div class="msg-content">
      <div class="msg-bubble">${esc(text).replaceAll("\n","<br>")}</div>
    </div>`;
  $("#messages").appendChild(div);
  div.scrollIntoView({ behavior: "smooth" });
}

function appendProcessingBubble() {
  const div = document.createElement("div");
  div.className = "msg msg-ai msg-processing";
  div.id = "processingMsg";
  div.innerHTML = `
    <div class="msg-avatar">谋</div>
    <div class="msg-content">
      <div class="msg-bubble">
        <div class="proc-dots"><span></span><span></span><span></span></div>
        <span class="proc-text" id="procText">正在创建任务…</span>
      </div>
    </div>`;
  $("#messages").appendChild(div);
  div.scrollIntoView({ behavior: "smooth" });
  return div;
}

function updateProcessingText(text) {
  const el = $("#procText");
  if (el) el.textContent = text;
}

function removeProcessingBubble() {
  const el = $("#processingMsg");
  if (el) el.remove();
  processingEl = null;
}

function appendAIResult(data) {
  const r = data.result || {};
  const answer = r.answer || "（未获取到回答）";
  convo.push({ role: "ai", content: answer, meta: r, ts: Date.now() });

  const div = document.createElement("div");
  div.className = "msg msg-ai";

  let bodyHTML = `
    <div class="msg-avatar">谋</div>
    <div class="msg-content">
      <div class="msg-bubble">${formatText(answer)}</div>`;

  // Structured info cards
  if (r.summary || r.next_actions || r.memory_updates || r.confidence) {
    bodyHTML += `<div class="info-cards">`;

    if (r.confidence) {
      bodyHTML += `<div class="info-card"><h4>置信度</h4><span class="conf-badge conf-${esc(r.confidence)}">${esc(r.confidence)}</span></div>`;
    }
    if (r.summary) {
      bodyHTML += `<div class="info-card"><h4>推理摘要</h4><p>${esc(r.summary)}</p></div>`;
    }
    if (r.next_actions && r.next_actions.length) {
      bodyHTML += `<div class="info-card"><h4>下一步建议</h4><ul>${r.next_actions.map(a => `<li>${esc(a)}</li>`).join("")}</ul></div>`;
    }
    if (r.memory_updates && r.memory_updates.length) {
      bodyHTML += `<div class="info-card"><h4>建议更新记忆</h4>`;
      r.memory_updates.forEach(m => {
        bodyHTML += `<p style="margin-bottom:6px"><strong>📁 ${esc(m.target)}</strong><br>${esc(m.content)}<br><small style="color:var(--muted)">${esc(m.reason)}</small></p>`;
      });
      bodyHTML += `</div>`;
    }
    bodyHTML += `</div>`;
  }

  // Debug toggle (collapsed)
  bodyHTML += `
    <div class="debug-toggle" onclick="this.nextElementSibling.classList.toggle('open')">技术详情 ▾</div>
    <div class="debug-info">
      Job: ${esc(data.job_id)} · Claude Code 外脑
    </div>`;

  bodyHTML += `</div>`;
  div.innerHTML = bodyHTML;
  $("#messages").appendChild(div);
  div.scrollIntoView({ behavior: "smooth" });
}

function appendErrorMessage(html) {
  const div = document.createElement("div");
  div.className = "msg msg-ai";
  div.innerHTML = `
    <div class="msg-avatar">!</div>
    <div class="msg-content">
      <div class="msg-bubble error-msg">${html}</div>
    </div>`;
  $("#messages").appendChild(div);
  div.scrollIntoView({ behavior: "smooth" });
}

function formatText(text) {
  return esc(text)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/^[-•] (.+)$/gm, "<span style='display:block;padding-left:6px;margin:2px 0'>· $1</span>")
    .replaceAll("\n", "<br>");
}

function disableInput(v) {
  $("#sendBtn").disabled = v;
  $("#chatInput").disabled = v;
  $("#headerStatus").textContent = v ? "处理中" : "就绪";
  $("#headerStatus").style.color = v ? "var(--amber)" : "var(--green)";
  $("#headerStatus").style.background = v ? "var(--amber-light)" : "var(--green-light)";
}

// ── Bootstrap ───────────────────────────────────────────────

fetch(`${API}/api/health`)
  .then(r => r.json())
  .then(d => { $("#headerStatus").textContent = "就绪"; })
  .catch(() => { $("#headerStatus").textContent = "离线"; $("#headerStatus").style.color = "var(--red)"; $("#headerStatus").style.background = "var(--red-light)"; });
