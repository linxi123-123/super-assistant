const $ = (selector) => document.querySelector(selector);
const API = window.location.protocol === "file:" ? "http://127.0.0.1:8000" : "";

let currentJobId = null;
let pollTimer = null;

const statusCopy = {
  ready: "我已上线，记忆与上下文连接完成。<br>你可以直接把问题交给我，我会帮你整理思路、分析信息或推进下一步。",
  processing: "正在处理你的问题…",
  done: "整理好了，我把结果给你",
  error: "处理遇到了问题，请稍后重试",
};

function esc(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatText(text) {
  return esc(text)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/^[-•]\s+(.+)$/gm, "<span style=\"display:block;margin:4px 0 4px 10px;\">• $1</span>")
    .replaceAll("\n", "<br>");
}

function setAnswer(html, state = "") {
  const answer = $("#answerCopy");
  if (!answer) return;
  answer.className = `answer-copy ${state}`.trim();
  answer.innerHTML = html;
}

function setDebug({ jobId = "-", status = "ready", confidence = "-", message = "等待输入" } = {}) {
  const elJob = $("#debugJobId");
  const elStatus = $("#debugStatus");
  const elConf = $("#debugConfidence");
  const elMsg = $("#debugMessage");
  if (elJob) elJob.textContent = jobId || "-";
  if (elStatus) elStatus.textContent = status;
  if (elConf) elConf.textContent = confidence || "-";
  if (elMsg) elMsg.textContent = message || "-";
}

function addQuestionCard(question) {
  const stack = $("#answerStack");
  if (!stack) return;
  const card = document.createElement("article");
  card.className = "question-card";
  card.textContent = question;
  const answerCard = $("#answerCard");
  if (answerCard) stack.insertBefore(card, answerCard);
  else stack.appendChild(card);
}

function renderAdvisorResponse(data) {
  // data is AdvisorChatResponse: { answer, task_type, actions, external_data, memory, meta, ... }
  const answer = data.answer || data.core_judgment || "已收到回答。";
  let html = formatText(answer);

  const blocks = [];

  // Answer mode from meta
  const answerMode = (data.meta || {}).answer_mode || data.answer_mode;
  if (answerMode) {
    const modeLabels = {
      personal_memory: "基于你的长期记忆",
      public_research: "基于公开资料查询",
      mixed: "结合记忆和公开资料",
      task_execution: "任务规划",
      casual_chat: "外脑对话"
    };
    const label = modeLabels[answerMode] || answerMode;
    blocks.push(`<section class="info-block"><h3>回答来源</h3><p>${esc(label)}</p></section>`);
  }

  // External data / sources
  const sources = data.external_sources || [];
  if (sources.length) {
    blocks.push(`<section class="info-block"><h3>信息来源</h3><ul>${sources.slice(0,5).map(s => {
      const title = s.title || s.source || "来源";
      const url = s.url || "";
      return url ? `<li><a href="${esc(url)}" target="_blank" rel="noopener">${esc(title)}</a></li>` : `<li>${esc(title)}</li>`;
    }).join("")}</ul></section>`);
  }

  // Actions
  const actions = data.actions || [];
  if (actions.length) {
    blocks.push(`<section class="info-block"><h3>下一步建议</h3><ul>${actions.map(a => `<li>${esc(typeof a === 'string' ? a : a.description || a.action || '')}</li>`).join("")}</ul></section>`);
  }

  // Memory
  const memory = data.memory || {};
  if (memory.candidate_memory_count > 0) {
    blocks.push(`<section class="info-block"><h3>记忆</h3><p>已沉淀 ${memory.candidate_memory_count} 条候选记忆</p></section>`);
  }

  if (blocks.length) {
    html += `<div class="structured-blocks">${blocks.join("")}</div>`;
  }

  setAnswer(html);
  setDebug({
    jobId: data.audit_id || "-",
    status: "succeeded",
    confidence: "-",
    message: data.task_type || "advisor_response",
  });

  // Update header meta
  const metaEl = document.querySelector(".answer-meta");
  if (metaEl) {
    const provider = data.provider || "super-assistant";
    metaEl.innerHTML = `<span class="answer-sigil"></span>外脑 · ${esc(provider)} · ${esc(data.task_type || "")}`;
  }
}

function setInputDisabled(disabled) {
  const send = $("#sendBtn");
  const input = $("#chatInput");
  if (send) send.disabled = disabled;
  if (input) input.disabled = disabled;
}

function autoResize(textarea) {
  textarea.style.height = "auto";
  textarea.style.height = `${Math.min(textarea.scrollHeight, 128)}px`;
}

// ── Core: call /api/advisor/chat ────────────────────────────

async function submitQuestion(question) {
  setInputDisabled(true);
  addQuestionCard(question);
  setAnswer("正在处理你的问题…", "processing");

  try {
    const response = await fetch(`${API}/api/advisor/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: question,
        user_id: "default_user",
      }),
    });

    if (!response.ok) {
      throw new Error(`advisor_http_${response.status}`);
    }

    const data = await response.json();
    renderAdvisorResponse(data);
    setInputDisabled(false);

  } catch (error) {
    setInputDisabled(false);
    setAnswer(`处理遇到了问题：${esc(error.message)}`, "failed");
    setDebug({ status: "error", message: error.message });
  }
}

function initSidebar() {
  const rail = $("#sideRail");
  const scrim = $("#sidebarScrim");
  const toggle = $("#menuToggle");

  function setOpen(open) {
    rail.classList.toggle("open", open);
    toggle.setAttribute("aria-expanded", String(open));
    toggle.setAttribute("aria-label", open ? "收起功能栏" : "展开功能栏");
    scrim.hidden = !open;
  }

  toggle.addEventListener("click", () => setOpen(!rail.classList.contains("open")));
  scrim.addEventListener("click", () => setOpen(false));
  document.querySelectorAll(".rail-item").forEach((item) => {
    item.addEventListener("click", () => {
      document.querySelectorAll(".rail-item").forEach((node) => node.classList.remove("active"));
      item.classList.add("active");
      setOpen(false);
    });
  });
}

function initForm() {
  const input = $("#chatInput");
  $("#chatForm").addEventListener("submit", (event) => {
    event.preventDefault();
    const question = input.value.trim();
    if (!question || $("#sendBtn").disabled) return;
    input.value = "";
    autoResize(input);
    submitQuestion(question);
  });

  input.addEventListener("input", () => autoResize(input));
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      $("#chatForm").requestSubmit();
    }
  });
}

initSidebar();
initForm();
setDebug();
