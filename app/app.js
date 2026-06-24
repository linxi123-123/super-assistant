const $ = (selector) => document.querySelector(selector);
const API = window.location.protocol === "file:" ? "http://127.0.0.1:8000" : "";

let currentJobId = null;
let pollTimer = null;

const statusCopy = {
  ready: "我已上线，记忆与上下文连接完成。<br>你可以直接把问题交给我，我会帮你整理思路、分析信息或推进下一步。",
  pending: "正在连接你的本机外脑",
  claimed: "我接到这个问题了，正在调动记忆",
  running: "正在整理上下文并合成答案",
  succeeded: "整理好了，我把结果给你",
  failed: "本机外脑暂时没接上，请确认 local_claude_worker.py 正在运行",
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
  answer.className = `answer-copy ${state}`.trim();
  answer.innerHTML = html;
}

function setDebug({ jobId = "-", status = "ready", confidence = "-", message = "等待输入" } = {}) {
  $("#debugJobId").textContent = jobId || "-";
  $("#debugStatus").textContent = status || "-";
  $("#debugConfidence").textContent = confidence || "-";
  $("#debugMessage").textContent = message || "-";
}

function addQuestionCard(question) {
  const card = document.createElement("article");
  card.className = "question-card";
  card.textContent = question;
  $("#answerStack").insertBefore(card, $("#answerCard"));
}

function renderResult(data) {
  const result = data.result || {};
  const answer = result.answer || "我已经收到结果，但这次没有拿到可展示的回答。";
  let html = formatText(answer);

  const blocks = [];

  // Answer mode indicator
  if (result.answer_mode) {
    const modeLabels = { personal_memory: "基于你的长期记忆", public_research: "基于公开资料查询", mixed: "结合记忆和公开资料", task_execution: "任务规划" };
    const label = modeLabels[result.answer_mode] || result.answer_mode;
    blocks.push(`<section class="info-block"><h3>回答来源</h3><p>${esc(label)}</p></section>`);
  }

  if (result.summary) {
    blocks.push(`<section class="info-block"><h3>处理摘要</h3><p>${esc(result.summary)}</p></section>`);
  }

  // Sources
  if (Array.isArray(result.sources) && result.sources.length) {
    blocks.push(`<section class="info-block"><h3>信息来源</h3><ul>${result.sources.map(s => `<li>${s.url ? `<a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title || s.source)}</a>` : esc(s.title || s.source)}</li>`).join("")}</ul></section>`);
  }
  if (Array.isArray(result.next_actions) && result.next_actions.length) {
    blocks.push(`<section class="info-block"><h3>下一步建议</h3><ul>${result.next_actions.map((item) => `<li>${esc(item)}</li>`).join("")}</ul></section>`);
  }
  if (Array.isArray(result.memory_updates) && result.memory_updates.length) {
    blocks.push(`<section class="info-block"><h3>建议更新记忆</h3>${result.memory_updates.map((item) => `<p>${esc(item.content || item.reason || item.target || "")}</p>`).join("")}</section>`);
  }
  if (blocks.length) {
    html += `<div class="structured-blocks">${blocks.join("")}</div>`;
  }

  setAnswer(html);
  setDebug({
    jobId: data.job_id,
    status: data.status,
    confidence: result.confidence || "-",
    message: result.debug_message || result.summary || statusCopy.succeeded,
  });
}

function setInputDisabled(disabled) {
  $("#sendBtn").disabled = disabled;
  $("#chatInput").disabled = disabled;
}

function autoResize(textarea) {
  textarea.style.height = "auto";
  textarea.style.height = `${Math.min(textarea.scrollHeight, 128)}px`;
}

function updateProductStatus(status, data = {}) {
  const copy = statusCopy[status] || statusCopy.running;
  const state = status === "failed" ? "failed" : (status === "succeeded" || status === "ready" ? "" : "processing");
  setAnswer(copy, state);
  setDebug({
    jobId: data.job_id || currentJobId || "-",
    status,
    confidence: data.result?.confidence || "-",
    message: data.error || data.result?.debug_message || copy.replace(/<br>/g, " "),
  });
}

async function createJob(question) {
  const response = await fetch(`${API}/api/local-agent/jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: "default_user",
      task_type: "deep_reasoning",
      question,
      context: {
        source: "main_chat_ui",
        mode: "local_claude_worker_default",
        use_llm_wiki: true,
        allow_public_research: true,
        answer_policy: "memory_plus_public_research",
        public_research_required_for_current_knowledge: true,
      },
    }),
  });

  if (!response.ok) {
    throw new Error(`create_job_http_${response.status}`);
  }
  return response.json();
}

async function pollJob(jobId) {
  try {
    const response = await fetch(`${API}/api/local-agent/jobs/${encodeURIComponent(jobId)}`);
    if (!response.ok) {
      pollTimer = window.setTimeout(() => pollJob(jobId), 2200);
      return;
    }

    const data = await response.json();
    const status = data.status || "running";
    updateProductStatus(status, data);

    if (status === "pending") {
      pollTimer = window.setTimeout(() => pollJob(jobId), 1800);
      return;
    }
    if (status === "claimed" || status === "running") {
      pollTimer = window.setTimeout(() => pollJob(jobId), 2600);
      return;
    }
    if (status === "succeeded") {
      renderResult(data);
      currentJobId = null;
      setInputDisabled(false);
      return;
    }
    if (status === "failed") {
      updateProductStatus("failed", data);
      currentJobId = null;
      setInputDisabled(false);
      return;
    }

    pollTimer = window.setTimeout(() => pollJob(jobId), 2600);
  } catch (error) {
    setDebug({
      jobId,
      status: "polling",
      confidence: "-",
      message: error.message || "轮询暂时失败，继续重试",
    });
    pollTimer = window.setTimeout(() => pollJob(jobId), 3000);
  }
}

async function submitQuestion(question) {
  window.clearTimeout(pollTimer);
  currentJobId = null;
  setInputDisabled(true);
  addQuestionCard(question);
  updateProductStatus("pending");

  try {
    const data = await createJob(question);
    currentJobId = data.job_id;
    updateProductStatus(data.status || "pending", data);
    pollJob(currentJobId);
  } catch (error) {
    currentJobId = null;
    setInputDisabled(false);
    updateProductStatus("failed", {
      error: error.message || "创建任务失败",
    });
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
