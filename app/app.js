const $ = (s) => document.querySelector(s);
const API = window.location.protocol === "file:" ? "http://127.0.0.1:8000" : "";
let currentJobId = null;
let pollTimer = null;
let convo = [];

function esc(v) { return String(v || "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;"); }

// ── Date ──────────────────────────────────────────────────

function updateDate() {
  const now = new Date();
  const days = ["日","一","二","三","四","五","六"];
  $("#headerDate").textContent = `${now.getFullYear()}年${now.getMonth()+1}月${now.getDate()}日 · 星期${days[now.getDay()]}`;
}
updateDate();

// ── Chat form ─────────────────────────────────────────────

$("#chatForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = $("#chatInput");
  const question = input.value.trim();
  if (!question || $("#sendBtn").disabled) return;
  input.value = "";
  autoResize(input);

  // Remove welcome state
  const welcome = $("#welcomeState");
  if (welcome) welcome.remove();

  appendMessage("user", question);
  await sendToClaudeWorker(question);
});

function autoResize(el) {
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 160) + "px";
}
$("#chatInput").addEventListener("input", () => autoResize($("#chatInput")));
$("#chatInput").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); $("#chatForm").dispatchEvent(new Event("submit")); }
});

// ── Core: send via Local Claude Worker ─────────────────────

async function sendToClaudeWorker(question) {
  if (currentJobId) { clearTimeout(pollTimer); }

  disableInput(true);
  showProcessing("创建任务", 0);
  $("#workerStatusBadge").textContent = "连接中";
  $("#workerStatusBadge").className = "panel-status connected";

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
      throw new Error(`status_${r.status}: ${errText}`);
    }

    const data = await r.json();
    currentJobId = data.job_id;

    // Update UI
    $("#procJobId").textContent = `Job: ${currentJobId}`;
    setStage(0, "done");
    setStage(1, "active");
    $("#procTitle").textContent = "等待本机 Claude Worker...";

    // Update right panel
    $("#panelJobInfo").hidden = false;
    $("#panelJobId").textContent = currentJobId;
    $("#workerStatusBadge").textContent = "处理中";
    $("#workerStatusBadge").className = "panel-status processing";

    // Start polling
    pollJob(currentJobId);

  } catch (err) {
    hideProcessing();
    disableInput(false);
    const msg = err.message || String(err);

    if (msg.includes("worker_api_unavailable")) {
      showWorkerUnavailable();
    } else {
      appendMessage("assistant", `请求失败：${esc(msg)}`, { error: true });
    }
    $("#workerStatusBadge").textContent = "错误";
    $("#workerStatusBadge").className = "panel-status error";
  }
}

// ── Poll job ───────────────────────────────────────────────

async function pollJob(jobId) {
  try {
    const r = await fetch(`${API}/api/local-agent/jobs/${jobId}`);
    if (!r.ok) {
      pollTimer = setTimeout(() => pollJob(jobId), 2000);
      return;
    }

    const data = await r.json();

    if (data.status === "pending") {
      setStage(1, "active");
      pollTimer = setTimeout(() => pollJob(jobId), 2000);

    } else if (data.status === "claimed") {
      setStage(1, "done");
      setStage(2, "active");
      $("#procTitle").textContent = "Claude Code 正在深度推理...";
      pollTimer = setTimeout(() => pollJob(jobId), 3000);

    } else if (data.status === "running") {
      setStage(2, "active");
      $("#procTitle").textContent = "Claude Code 推理中...";
      pollTimer = setTimeout(() => pollJob(jobId), 3000);

    } else if (data.status === "succeeded") {
      setStage(2, "done");
      setStage(3, "done");
      $("#procTitle").textContent = "推理完成";
      hideProcessing();
      disableInput(false);
      showResult(data, true);
      updateContextPanel(data);

    } else if (data.status === "failed") {
      setStage(2, "done");
      setStage(3, "done");
      hideProcessing();
      disableInput(false);
      showResult(data, false);
      $("#workerStatusBadge").textContent = "失败";
      $("#workerStatusBadge").className = "panel-status error";

    } else {
      pollTimer = setTimeout(() => pollJob(jobId), 3000);
    }
  } catch (_) {
    pollTimer = setTimeout(() => pollJob(jobId), 3000);
  }
}

// ── Show result ────────────────────────────────────────────

function showResult(data, success) {
  if (success) {
    const r = data.result || {};
    const answer = r.answer || "Claude 返回了回答但未包含 answer 字段。";

    // If there's a worker unavailable message in the answer, show warning
    if (answer.includes("Worker 暂未响应") || answer.includes("Worker") && answer.includes("未")) {
      appendMessage("assistant", answer, { workerWarning: true });
    } else {
      appendMessage("assistant", answer, {
        summary: r.summary,
        nextActions: r.next_actions,
        memoryUpdates: r.memory_updates,
        confidence: r.confidence,
        warnings: r.warnings,
        jobId: data.job_id
      });
    }

    $("#workerStatusBadge").textContent = "就绪";
    $("#workerStatusBadge").className = "panel-status success";
    setTimeout(() => {
      $("#workerStatusBadge").textContent = "待命中";
      $("#workerStatusBadge").className = "panel-status offline";
    }, 3000);

  } else {
    const errMsg = data.error || "未知错误";
    appendMessage("assistant",
      `❌ 本机 Claude Worker 处理失败（${esc(errMsg)}）。\n\n请确认：\n1. 本机 \`local_claude_worker.py\` 正在运行\n2. 本机 Claude Code 可用`,
      { error: true }
    );

    // Show fallback note
    const fb = document.createElement("div");
    fb.className = "fallback-banner";
    fb.textContent = "已降级到普通模型回答（如需使用 Claude Code 外脑，请检查本机 Worker 状态）";
    $("#conversation").appendChild(fb);
    fb.scrollIntoView({ behavior: "smooth" });
  }

  currentJobId = null;
}

// ── Show worker unavailable ────────────────────────────────

function showWorkerUnavailable() {
  const div = document.createElement("div");
  div.className = "error-banner";
  div.innerHTML = `⚠️ <strong>本机 Claude Worker 暂未响应</strong><br>请确认本机 <code>local_claude_worker.py</code> 正在运行。<br>服务器端 Local Claude Worker 功能可能未启用。`;
  $("#conversation").appendChild(div);
  div.scrollIntoView({ behavior: "smooth" });
  $("#workerStatusBadge").textContent = "未连接";
  $("#workerStatusBadge").className = "panel-status error";
}

// ── Processing UI ──────────────────────────────────────────

function showProcessing(title, stageIdx) {
  const panel = $("#processingPanel");
  panel.hidden = false;
  $("#procTitle").textContent = title;
  // Reset all stages
  for (let i = 0; i <= 3; i++) {
    const el = $(`#stage${["Create","Claim","Run","Done"][i]}`);
    if (el) { el.classList.remove("active", "done"); }
  }
  if (stageIdx >= 0) {
    const el = $(`#stage${["Create","Claim","Run","Done"][stageIdx]}`);
    if (el) el.classList.add("active");
  }
}

function hideProcessing() {
  setTimeout(() => { $("#processingPanel").hidden = true; }, 1000);
}

function setStage(idx, state) {
  const el = $(`#stage${["Create","Claim","Run","Done"][idx]}`);
  if (!el) return;
  el.classList.remove("active", "done");
  if (state === "active") el.classList.add("active");
  if (state === "done") el.classList.add("done");
}

function disableInput(v) {
  $("#sendBtn").disabled = v;
  $("#chatInput").disabled = v;
  $("#statusText").textContent = v ? "处理中 · 等待本机 Claude Code..." : "就绪 · 本机 Claude Code 外脑待命";
}

// ── Append message ─────────────────────────────────────────

function appendMessage(role, text, meta = {}) {
  convo.push({ role, content: text, meta, ts: new Date().toISOString() });
  const div = document.createElement("div");
  div.className = `msg msg-${role}`;

  // Avatar
  const av = document.createElement("div");
  av.className = "msg-avatar";
  av.textContent = role === "user" ? "U" : "谋";

  // Body
  const body = document.createElement("div");
  body.className = "msg-body";

  // Bubble
  const bubble = document.createElement("div");
  bubble.className = "msg-bubble";

  let formatted = esc(text)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/^[-•] (.+)$/gm, "<span style='display:block;padding-left:6px;margin:2px 0'>· $1</span>")
    .replaceAll("\n", "<br>");

  bubble.innerHTML = `<p>${formatted}</p>`;
  body.appendChild(bubble);

  // Error meta
  if (meta.error) {
    const m = document.createElement("div");
    m.className = "msg-meta";
    m.innerHTML = `<span style="color:var(--red)">处理异常</span>`;
    body.appendChild(m);
  }

  // Worker warning meta
  if (meta.workerWarning) {
    const m = document.createElement("div");
    m.className = "msg-meta";
    m.innerHTML = `<span style="color:var(--amber)">⚠ Worker 提示</span>`;
    body.appendChild(m);
  }

  // Structured result cards
  if (meta.confidence) {
    const card = document.createElement("div");
    card.className = "result-card";
    card.innerHTML = `
      <h4>🎯 置信度</h4>
      <span class="confidence-badge conf-${meta.confidence}">${esc(meta.confidence)}</span>`;
    body.appendChild(card);
  }

  if (meta.summary) {
    const card = document.createElement("div");
    card.className = "result-card";
    card.innerHTML = `<h4>📋 推理摘要</h4><p>${esc(meta.summary)}</p>`;
    body.appendChild(card);
  }

  if (meta.nextActions && meta.nextActions.length) {
    const card = document.createElement("div");
    card.className = "result-card";
    card.innerHTML = `<h4>➡️ 下一步建议</h4><ul>${meta.nextActions.map(a => `<li>${esc(a)}</li>`).join("")}</ul>`;
    body.appendChild(card);
  }

  if (meta.memoryUpdates && meta.memoryUpdates.length) {
    const card = document.createElement("div");
    card.className = "result-card";
    card.innerHTML = `<h4>🧠 建议记忆更新</h4>`;
    meta.memoryUpdates.forEach(m => {
      const item = document.createElement("div");
      item.className = "memory-item";
      item.innerHTML = `
        <div class="mem-target">📁 ${esc(m.target)}</div>
        <div class="mem-content">${esc(m.content)}</div>
        <div class="mem-reason">原因：${esc(m.reason)}</div>`;
      card.appendChild(item);
    });
    body.appendChild(card);
  }

  if (meta.warnings && meta.warnings.length) {
    const card = document.createElement("div");
    card.className = "result-card";
    card.innerHTML = `<h4>⚠️ 注意事项</h4><ul>${meta.warnings.map(w => `<li>${esc(w)}</li>`).join("")}</ul>`;
    body.appendChild(card);
  }

  if (meta.jobId) {
    const m = document.createElement("div");
    m.className = "msg-meta";
    m.innerHTML = `<span>Job: ${esc(meta.jobId)}</span><span>Claude Code 外脑</span>`;
    body.appendChild(m);
  }

  div.appendChild(av);
  div.appendChild(body);
  $("#conversation").appendChild(div);
  div.scrollIntoView({ behavior: "smooth" });
}

// ── Right panel update ─────────────────────────────────────

function updateContextPanel(data) {
  const r = data.result || {};

  if (r.confidence) {
    $("#panelConfidence").hidden = false;
    $("#panelConfidenceValue").textContent = r.confidence;
    $("#panelConfidenceValue").className = "confidence-value " +
      (r.confidence === "high" ? "conf-high" : r.confidence === "medium" ? "conf-medium" : "conf-low");
  }

  if (r.next_actions && r.next_actions.length) {
    $("#panelNextActions").hidden = false;
    $("#panelNextActionsList").innerHTML = r.next_actions.map(a => `<li>${esc(a)}</li>`).join("");
  }

  if (r.memory_updates && r.memory_updates.length) {
    $("#panelMemoryUpdates").hidden = false;
    $("#panelMemoryUpdatesContent").innerHTML = r.memory_updates.map(m => `
      <div class="memory-item">
        <div class="mem-target">📁 ${esc(m.target)}</div>
        <div class="mem-content">${esc(m.content)}</div>
        <div class="mem-reason">原因：${esc(m.reason)}</div>
      </div>`).join("");
  }

  if (r.warnings && r.warnings.length) {
    $("#panelWarnings").hidden = false;
    $("#panelWarningsList").innerHTML = r.warnings.map(w => `<li>${esc(w)}</li>`).join("");
  }
}

// ── Recent tasks sidebar ───────────────────────────────────

function addRecentTask(jobId, question) {
  const el = $("#recentTasks");
  if (el.querySelector(".dim-text")) el.innerHTML = "";
  const item = document.createElement("div");
  item.style.cssText = "padding:6px 0;font-size:0.78rem;border-bottom:1px solid var(--line);cursor:pointer";
  item.innerHTML = `<span style="color:var(--accent2)">${esc(jobId)}</span><br><span style="color:var(--text2)">${esc(question.slice(0, 30))}...</span>`;
  item.onclick = () => {
    fetch(`${API}/api/local-agent/jobs/${jobId}`).then(r => r.json()).then(d => {
      updateContextPanel(d);
      $("#panelJobInfo").hidden = false;
      $("#panelJobId").textContent = jobId;
    }).catch(()=>{});
  };
  el.prepend(item);
  if (el.children.length > 10) el.lastChild.remove();
}

// ── Bootstrap ──────────────────────────────────────────────

// Check server connectivity
fetch(`${API}/api/health`)
  .then(r => r.json())
  .then(d => {
    $("#statusText").textContent = `就绪 · 本机 Claude Code 外脑待命 · ${d.mode}`;
    $("#greeting").textContent = "Claude Code 外脑已就绪";
  })
  .catch(() => {
    $("#statusText").textContent = "服务器未连接 · 请启动后端服务";
  });
