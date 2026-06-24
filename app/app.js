const $ = (s) => document.querySelector(s);
const API = window.location.protocol === "file:" ? "http://127.0.0.1:8000" : "";

function esc(v) { return String(v || "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;"); }

let convo = [];
let myUserId = localStorage.getItem("super_assistant_uid") || "";
let myTitle = localStorage.getItem("super_assistant_title") || "";
let myName = localStorage.getItem("super_assistant_name") || "";

function uid() { return "u_" + Date.now().toString(36) + "_" + Math.random().toString(36).slice(2, 8); }

function getUserId() { return myUserId || "default_user"; }
function getUserTitle() { return myTitle || ""; }
function getGreeting() { return myTitle ? `${myTitle}` : ""; }

// ── Identity ─────────────────────────────────────────────

async function initIdentity() {
  const prevName = localStorage.getItem("super_assistant_name") || "";

  showNamePrompt(prevName, (name) => {
    const isNewName = (name !== prevName);
    myUserId = name;
    myName = name;
    localStorage.setItem("super_assistant_uid", name);
    localStorage.setItem("super_assistant_name", name);
    $("#greetingName").textContent = name;

    if (isNewName) {
      $("#conversation").innerHTML = "";
      convo = [];
    }

    loadBriefing();

    // Check if this user has history
    checkAndGreet(name, isNewName);
  });
}

function showNamePrompt(prefill, onDone) {
  const shell = $(".app-shell");
  if (!shell) return;
  const isReturning = !!prefill;
  const ov = document.createElement("div");
  ov.id = "_prompt";
  ov.innerHTML = `<div style="position:fixed;inset:0;background:rgba(255,255,255,0.94);display:flex;align-items:center;justify-content:center;z-index:1000"><div style="background:#fff;padding:36px;border-radius:18px;border:1px solid #e5e5e6;text-align:center;max-width:380px;box-shadow:0 8px 40px rgba(0,0,0,0.06)"><div style="width:48px;height:48px;border-radius:12px;background:linear-gradient(135deg,#6366f1,#8b5cf6);margin:0 auto 16px;display:flex;align-items:center;justify-content:center;color:#fff;font-size:1.3rem;font-weight:700">谋</div><h2 style="font-size:1.15rem;font-weight:600;margin-bottom:4px;color:#1a1a2e">${isReturning ? '欢迎回来' : '超级助理'}</h2><p style="color:#6b7280;margin-bottom:18px;font-size:0.86rem;line-height:1.6">${isReturning ? '上次是「' + esc(prefill) + '」吗？<br>换人请修改名字，同一个人直接进入' : '输入你的名字开始使用<br><span style="font-size:0.75rem;color:#9ca3af">同一名字在手机和电脑上登录，记忆自动同步</span>'}</p><form id="_pf"><input id="_pn" required placeholder="你的名字" value="${esc(prefill)}" style="width:100%;padding:12px 16px;border-radius:10px;border:1px solid #e5e5e6;font-size:1rem;margin-bottom:12px;text-align:center" autofocus /><button type="submit" style="width:100%;padding:12px;border-radius:10px;background:#6366f1;color:#fff;font-size:0.95rem;font-weight:500">进入</button></form></div></div>`;
  shell.appendChild(ov);
  $("#_pf").addEventListener("submit", (e) => {
    e.preventDefault();
    const name = $("#_pn").value.trim();
    if (!name) return;
    ov.remove();
    onDone(name);
  });
}

async function checkAndGreet(name, isNewName) {
  try {
    const r = await fetch(`${API}/api/daily-briefing?user_id=${getUserId()}`);
    if (!r.ok) { showNewUserOnboarding(name); return; }
    const d = await r.json();
    const y = d.yesterday || {};
    const convCount = y.conversation_count || 0;

    if (convCount === 0) {
      // Never chatted - show feature intro + ask identity
      showNewUserOnboarding(name);
    } else {
      // Has history - contextual greeting
      const topics = (y.key_topics || []).join("、") || "各种话题";
      const t = d.today || {};
      const goals = (t.active_goals || []).slice(0, 1);
      let msg = "欢迎回来，" + esc(name) + "。";
      if (goals.length) msg += "<br><br>你的目标「" + esc(goals[0]) + "」还在推进中。";
      msg += "<br><br>上次我们聊了" + topics + "。今天有什么需要我帮忙的？";
      appendMessage("assistant", msg);
    }
  } catch (_) {
    showNewUserOnboarding(name);
  }
}

function showNewUserOnboarding(name) {
  setTimeout(() => {
    appendMessage("assistant", "嗨，" + esc(name) + "！我是你的超级助理。<br><br>我能帮你：<br>☀ 查天气和空气质量<br>📈 看市场行情<br>🤖 获取AI行业资讯<br>🎯 做项目战略推演<br>🧠 长期记忆，越用越懂你<br><br>先跟我说说，你是做什么的？平时在忙些什么？");
  }, 500);
}

// ── Title preference ─────────────────────────────────────

function promptTitle() {
  appendMessage("assistant", "你希望我怎么称呼你？直接告诉我就行，我会记住。");
}

// ── Daily Briefing ───────────────────────────────────────

async function loadBriefing() {
  try {
    const r = await fetch(`${API}/api/daily-briefing?user_id=${getUserId()}`);
    if (!r.ok) throw new Error("offline");
    const d = await r.json();
    renderBriefing(d);
  } catch (_) {
    $("#dailyBriefing").innerHTML = `<div class="briefing-card offline"><h3>后端未连接</h3><p>启动后端后自动加载。</p></div>`;
  }
}

function renderBriefing(d) {
  $("#greeting").textContent = d.greeting || "上午好";
  if (myName) $("#greetingName").textContent = getGreeting() ? `${myName} · ${getGreeting()}` : myName;
  $("#dateLine").textContent = `${d.date} · ${d.weekday}`;

  const y = d.yesterday || {};
  $("#yesterdayCard").innerHTML = y.conversation_count
    ? `<p>昨天共 <strong>${y.conversation_count}</strong> 轮对话</p><p>主要话题：${(y.key_topics||[]).join("、")||"综合"}</p><p>沉淀记忆：<strong>${y.memory_deposited||0}</strong> 条</p><p class="dim">${esc(y.key_conclusion||"")}</p>`
    : `<p>昨天暂无对话记录。</p><p class="dim">开始使用后这里会显示昨天的复盘。</p>`;

  const t = d.today || {};
  const mh = t.memory_health || {};
  let todayHtml = "";
  if ((t.active_goals||[]).length) todayHtml += `<p>目标：${esc(t.active_goals[0])}</p>`;
  if (t.radar_rules_active) todayHtml += `<p>活跃雷达：<strong>${t.radar_rules_active}</strong> 条</p>`;
  if (t.pending_reminders) todayHtml += `<p>待处理提醒：<strong>${t.pending_reminders}</strong> 条</p>`;
  todayHtml += `<p>记忆：active ${mh.active||0} · candidate ${mh.candidate||0}</p>`;
  if (!todayHtml) todayHtml = `<p>新的一天。开始对话吧。</p>`;
  $("#todayCard").innerHTML = todayHtml;

  const tm = d.tomorrow || {};
  const sf = tm.suggested_focus || [];
  $("#tomorrowCard").innerHTML = sf.length ? sf.map(s => `<p>· ${esc(s)}</p>`).join("") : `<p>基于今天的对话，明天会有更具体的建议。</p>`;
}

// ── Chat ─────────────────────────────────────────────────

$("#chatForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = $("#chatInput");
  const msg = input.value.trim();
  if (!msg) return;
  input.value = "";
  autoResize(input);

  // Special commands
  if (msg === "/称呼" || msg === "/title") { promptTitle(); return; }

  appendMessage("user", msg);
  await sendToAdvisor(msg);
});

async function sendToAdvisor(content) {
  setTyping(true);
  try {
    // Pass recent conversation history so LLM knows context
    const recentHistory = convo.slice(-6).map(c => ({ role: c.role, content: c.content.slice(0, 300) }));
    const r = await fetch(`${API}/api/advisor/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: content, user_id: getUserId(), conversation_history: recentHistory }),
    });
    if (!r.ok) throw new Error(`status_${r.status}`);
    const p = await r.json();
    let text = p.answer || p.core_judgment || "";
    // Clean up warning artifacts that occasionally leak through
    text = text.replace(/本地审查提示[：:][^\n]*(\n|$)/g, "").replace(/该回答已降级为谨慎建议[，,][^\n]*/g, "").trim();
    appendMessage("assistant", text, p);
  } catch (err) {
    appendMessage("assistant", `请求失败：${err.message}。请确认后端已启动：uv run python -m uvicorn server.main:app --host 0.0.0.0 --port 8000`, { error: true });
  }
  setTyping(false);
}

function appendMessage(role, text, meta = {}) {
  convo.push({ role, content: text, meta, ts: new Date().toISOString() });

  const div = document.createElement("div");
  div.className = `msg msg-${role}`;

  // Avatar
  const avatar = document.createElement("div");
  avatar.className = "msg-avatar";
  if (role === "user") {
    avatar.innerHTML = `<svg viewBox="0 0 40 40" fill="none"><circle cx="20" cy="14" r="7" fill="#9ca3af"/><ellipse cx="20" cy="34" rx="12" ry="10" fill="#d1d5db"/></svg>`;
  } else {
    avatar.innerHTML = `<svg viewBox="0 0 40 40" fill="none"><circle cx="20" cy="20" r="16" fill="#6366f1" opacity=".12"/><circle cx="20" cy="20" r="10" fill="#6366f1" opacity=".35"/><circle cx="20" cy="20" r="5" fill="#6366f1"/><circle cx="26" cy="14" r="3" fill="#fff" opacity=".7"/></svg>`;
  }

  // Bubble
  const bubble = document.createElement("div");
  bubble.className = "msg-bubble";

  // Honorific prefix for assistant
  let greeting = "";
  if (role === "assistant" && myTitle && !meta.error) {
    greeting = `<span style="color:var(--cyan);font-weight:500;font-size:0.82rem">${esc(myTitle)}</span>\n`;
  }

  // Format: convert markdown-like bold and bullet points
  let formatted = esc(text)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/^[-•] (.+)$/gm, "<span style='display:block;padding-left:8px;margin:2px 0'>· $1</span>");

  bubble.innerHTML = `<p>${greeting}${formatted.replaceAll("\n", "<br>")}</p>`;

  // Meta
  if (meta && role === "assistant" && !meta.error) {
    const downgraded = meta.was_downgraded;
    const sc = meta.source_count || 0;
    const mode = (meta.meta || {}).advisor_mode || "";
    const flags = ((meta.meta || {}).rationality_flags || []).join(" · ");
    if (mode || flags || sc) {
      const metaDiv = document.createElement("div");
      metaDiv.className = "msg-meta";
      if (mode) metaDiv.innerHTML += `<span>${esc(mode)}</span>`;
      if (flags) metaDiv.innerHTML += `<span>${esc(flags)}</span>`;
      if (sc) metaDiv.innerHTML += `<span>来源 ${sc}</span>`;
      if (downgraded) metaDiv.innerHTML += `<span class="warn">降级</span>`;
      bubble.appendChild(metaDiv);
    }
  }

  div.appendChild(avatar);
  div.appendChild(bubble);
  $("#conversation").appendChild(div);
  div.scrollIntoView({ behavior: "smooth" });
}

function setTyping(on) { const el = $("#typingIndicator"); if (el) el.hidden = !on; }

// ── Quick commands ───────────────────────────────────────

document.addEventListener("click", (e) => {
  const qb = e.target.closest(".quick-btn");
  if (qb) {
    const prompt = qb.dataset.prompt;
    if (prompt) {
      appendMessage("user", prompt);
      sendToAdvisor(prompt);
    }
  }
  const tb = e.target.closest("#titleBtn");
  if (tb) promptTitle();
});

// ── Textarea ─────────────────────────────────────────────

function autoResize(el) {
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 160) + "px";
}
$("#chatInput").addEventListener("input", () => autoResize($("#chatInput")));
$("#chatInput").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    $("#chatForm").dispatchEvent(new Event("submit"));
  }
});

// ── Switch user ──────────────────────────────────────────

$("#greetingName").addEventListener("click", () => {
  myUserId = "";
  myName = "";
  myTitle = "";
  localStorage.removeItem("super_assistant_uid");
  localStorage.removeItem("super_assistant_uid");
  localStorage.removeItem("super_assistant_name");
  localStorage.removeItem("super_assistant_title");
  $("#conversation").innerHTML = "";
  convo = [];
  initIdentity();
});

// ── Voice input ──────────────────────────────────────────

let isListening = false;
let recognition = null;

$("#voiceBtn").addEventListener("click", () => {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    alert("你的浏览器不支持语音输入，请用 Chrome 或 Edge");
    return;
  }
  if (isListening) {
    recognition && recognition.stop();
    return;
  }
  recognition = new SpeechRecognition();
  recognition.lang = "zh-CN";
  recognition.interimResults = false;
  recognition.continuous = false;
  isListening = true;
  $("#voiceBtn").textContent = "🔴";
  recognition.onresult = (event) => {
    const text = event.results[0][0].transcript;
    $("#chatInput").value = text;
    autoResize($("#chatInput"));
    $("#chatForm").dispatchEvent(new Event("submit"));
    isListening = false;
    $("#voiceBtn").textContent = "🎤";
  };
  recognition.onerror = () => {
    isListening = false;
    $("#voiceBtn").textContent = "🎤";
  };
  recognition.onend = () => {
    isListening = false;
    $("#voiceBtn").textContent = "🎤";
  };
  recognition.start();
});

// ── Bootstrap ────────────────────────────────────────────

initIdentity();
loadBriefing();
setInterval(loadBriefing, 5 * 60 * 1000);
