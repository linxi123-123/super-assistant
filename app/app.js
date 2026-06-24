const $ = (selector) => document.querySelector(selector);
const API = window.location.protocol === "file:" ? "http://127.0.0.1:8000" : "";

let currentJobId = null;
let pollTimer = null;
let activeAssistantMessage = null;

const statusCopy = {
  ready: "点击说话，或长按输入",
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
    .replace(/^[-•]\s+(.+)$/gm, "<span class=\"chat-list-line\">• $1</span>")
    .replaceAll("\n", "<br>");
}

function isChatActive() {
  return document.querySelector(".mobile-shell")?.classList.contains("chat-active");
}

function ensureChatActive() {
  document.querySelector(".mobile-shell")?.classList.add("chat-active");
}

function scrollChatToEnd() {
  const log = $("#chatLog");
  if (!log) return;
  window.requestAnimationFrame(() => {
    log.scrollTop = log.scrollHeight;
  });
}

function addChatMessage(role, content, { html = false, state = "" } = {}) {
  const log = $("#chatLog");
  if (!log) return null;

  const item = document.createElement("article");
  item.className = `chat-message ${role} ${state}`.trim();

  const meta = document.createElement("div");
  meta.className = "chat-meta";
  meta.textContent = role === "user" ? "你" : "外脑 · 刚刚";

  const body = document.createElement("div");
  body.className = "chat-bubble";
  if (html) body.innerHTML = content;
  else body.textContent = content;

  item.append(meta, body);
  log.appendChild(item);
  scrollChatToEnd();
  return item;
}

function setChatMessage(node, content, { html = false, state = "" } = {}) {
  if (!node) return;
  node.className = `chat-message assistant ${state}`.trim();
  const body = node.querySelector(".chat-bubble");
  if (!body) return;
  if (html) body.innerHTML = content;
  else body.textContent = content;
  scrollChatToEnd();
}

function setCommandText(text, state = "") {
  const command = $("#commandText");
  if (!command) return;
  command.className = `command-text ${state}`.trim();
  command.textContent = String(text || statusCopy.ready).replace(/<br>/g, " ");
  command.title = command.textContent;
}

function setDebug({ jobId = "-", status = "ready", confidence = "-", message = "等待输入" } = {}) {
  const jobNode = $("#debugJobId");
  const statusNode = $("#debugStatus");
  const confidenceNode = $("#debugConfidence");
  const messageNode = $("#debugMessage");
  if (jobNode) jobNode.textContent = jobId || "-";
  if (statusNode) statusNode.textContent = status || "-";
  if (confidenceNode) confidenceNode.textContent = confidence || "-";
  if (messageNode) messageNode.textContent = message || "-";
}

function addQuestionCard(question) {
  ensureChatActive();
  addChatMessage("user", question);
}

function setInputDisabled(disabled) {
  $("#sendBtn").disabled = disabled;
  $("#chatInput").disabled = disabled;
  $("#voiceBtn").disabled = disabled;
  $("#modeBtn").disabled = disabled;
}

function autoResize(textarea) {
  textarea.style.height = "auto";
  textarea.style.height = `${Math.min(textarea.scrollHeight, 128)}px`;
}

function updateProductStatus(status, data = {}) {
  const copy = statusCopy[status] || statusCopy.running;
  const state = status === "failed" ? "failed" : (status === "succeeded" || status === "ready" ? "" : "processing");
  setCommandText(copy, state);
  if (isChatActive() && status !== "ready" && status !== "succeeded") {
    if (!activeAssistantMessage) {
      activeAssistantMessage = addChatMessage("assistant", copy, { state });
    } else {
      setChatMessage(activeAssistantMessage, copy, { state });
    }
  }
  setDebug({
    jobId: data.job_id || currentJobId || "-",
    status,
    confidence: data.result?.confidence || "-",
    message: data.error || data.result?.debug_message || copy.replace(/<br>/g, " "),
  });
}

function renderResult(data) {
  // Advisor returns data.answer at top level; local-agent returns data.result.answer
  const answer = data.answer || (data.result || {}).answer || "我已经收到结果，但这次没有拿到可展示的回答。";
  const result = data.result || {};
  const firstLine = answer.split(/\r?\n/).find(Boolean) || statusCopy.succeeded;
  setCommandText(firstLine.length > 42 ? `${firstLine.slice(0, 42)}...` : firstLine);
  if (isChatActive()) {
    if (!activeAssistantMessage) activeAssistantMessage = addChatMessage("assistant", "", { state: "processing" });
    setChatMessage(activeAssistantMessage, formatText(answer), { html: true });
    activeAssistantMessage = null;
  }
  setDebug({
    jobId: data.job_id,
    status: data.status,
    confidence: result.confidence || "-",
    message: result.debug_message || result.summary || statusCopy.succeeded,
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
      },
    }),
  });
  if (!response.ok) throw new Error(`create_job_http_${response.status}`);
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
    setDebug({ jobId, status: "polling", confidence: "-", message: error.message || "轮询暂时失败，继续重试" });
    pollTimer = window.setTimeout(() => pollJob(jobId), 3000);
  }
}

async function submitQuestion(question) {
  window.clearTimeout(pollTimer);
  currentJobId = null;
  activeAssistantMessage = null;
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
    updateProductStatus("failed", { error: error.message || "创建任务失败" });
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
  const form = $("#chatForm");
  const input = $("#chatInput");
  const modeButton = $("#modeBtn");
  const voiceButton = $("#voiceBtn");

  function setTextMode(enabled) {
    form.classList.toggle("text-mode", enabled);
    modeButton.setAttribute("aria-label", enabled ? "切换语音输入" : "切换文字输入");
    if (enabled) {
      window.setTimeout(() => input.focus(), 30);
    } else {
      input.blur();
      input.value = "";
      autoResize(input);
      if (!currentJobId) setCommandText(statusCopy.ready);
    }
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    if (!form.classList.contains("text-mode")) {
      setTextMode(true);
      return;
    }
    const question = input.value.trim();
    if (!question || $("#sendBtn").disabled) return;
    input.value = "";
    autoResize(input);
    submitQuestion(question);
  });

  modeButton.addEventListener("click", () => {
    setTextMode(!form.classList.contains("text-mode"));
  });

  voiceButton.addEventListener("click", () => {
    if (form.classList.contains("text-mode")) {
      setTextMode(false);
      return;
    }
    setCommandText("语音入口已就绪，也可以点右侧按钮输入文字");
  });

  input.addEventListener("input", () => autoResize(input));
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      form.requestSubmit();
    }
  });
}

async function initParticleBrain() {
  const canvas = $("#particleBrain");
  if (!canvas) return;
  let THREE;
  try {
    THREE = await import("./vendor/three.module.min.js");
  } catch (error) {
    canvas.classList.add("webgl-unavailable");
    console.warn("Particle brain skipped because Three.js was not loaded.", error);
    return;
  }
  const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({
      canvas,
      alpha: true,
      antialias: true,
      preserveDrawingBuffer: true,
      powerPreference: "high-performance",
    });
  } catch (_) {
    canvas.classList.add("webgl-unavailable");
    return;
  }
  renderer.setClearColor(0x000000, 0);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
  camera.position.set(0, 0, 4.95);

  const group = new THREE.Group();
  scene.add(group);

  const count = prefersReduced ? 900 : 2600;
  const positions = new Float32Array(count * 3);
  const seeds = new Float32Array(count);
  const sizes = new Float32Array(count);
  const colors = new Float32Array(count * 3);

  function colorFor(i) {
    const p = Math.random();
    if (p < 0.66) return [1.0, 0.22 + Math.random() * 0.28, 0.34 + Math.random() * 0.18];
    if (p < 0.86) return [1.0, 0.86, 0.9];
    return [0.66 + Math.random() * 0.22, 0.28, 1.0];
  }

  for (let i = 0; i < count; i += 1) {
    const u = Math.random();
    const v = Math.random();
    const theta = Math.acos(2 * u - 1);
    const phi = Math.PI * 2 * v;
    const shell = 0.78 + Math.random() * 0.24;
    const x = shell * Math.sin(theta) * Math.cos(phi);
    const y = shell * Math.sin(theta) * Math.sin(phi);
    const z = shell * Math.cos(theta);
    positions[i * 3] = x;
    positions[i * 3 + 1] = y;
    positions[i * 3 + 2] = z;
    seeds[i] = Math.random() * 1000;
    sizes[i] = 3.2 + Math.random() * 5.4 + (Math.random() > 0.94 ? 8.8 : 0);
    const c = colorFor(i);
    colors[i * 3] = c[0];
    colors[i * 3 + 1] = c[1];
    colors[i * 3 + 2] = c[2];
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute("aSeed", new THREE.BufferAttribute(seeds, 1));
  geometry.setAttribute("aSize", new THREE.BufferAttribute(sizes, 1));
  geometry.setAttribute("aColor", new THREE.BufferAttribute(colors, 3));

  const material = new THREE.ShaderMaterial({
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
    uniforms: {
      uTime: { value: 0 },
      uPixelRatio: { value: Math.min(window.devicePixelRatio || 1, 2) },
      uBreathe: { value: 1 },
    },
    vertexShader: `
      attribute float aSeed;
      attribute float aSize;
      attribute vec3 aColor;
      uniform float uTime;
      uniform float uPixelRatio;
      uniform float uBreathe;
      varying vec3 vColor;
      varying float vAlpha;

      mat3 rotY(float a) {
        float s = sin(a);
        float c = cos(a);
        return mat3(c, 0.0, s, 0.0, 1.0, 0.0, -s, 0.0, c);
      }

      void main() {
        vec3 p = position;
        float n1 = sin(uTime * (0.85 + fract(aSeed) * 0.8) + aSeed);
        float n2 = sin(uTime * 1.73 + aSeed * 2.17);
        float localBreath = 1.0 + 0.045 * n1 + 0.022 * n2;
        p *= localBreath * uBreathe;
        p += normalize(position + 0.001) * (0.035 * sin(uTime * 1.25 + aSeed * 3.0));
        p = rotY(0.12 * sin(uTime * 0.6 + aSeed * 0.01)) * p;

        vec4 mvPosition = modelViewMatrix * vec4(p, 1.0);
        gl_Position = projectionMatrix * mvPosition;
        float front = smoothstep(-1.1, 1.0, p.z);
        gl_PointSize = aSize * uPixelRatio * (1.08 + front * 0.58) / max(0.9, -mvPosition.z * 0.58);
        vColor = aColor;
        vAlpha = 0.3 + front * 0.58;
      }
    `,
    fragmentShader: `
      varying vec3 vColor;
      varying float vAlpha;
      void main() {
        vec2 uv = gl_PointCoord - vec2(0.5);
        float d = length(uv);
        float core = smoothstep(0.24, 0.0, d);
        float halo = smoothstep(0.5, 0.0, d) * 0.42;
        float rayX = smoothstep(0.032, 0.0, abs(uv.y)) * smoothstep(0.46, 0.0, abs(uv.x));
        float rayY = smoothstep(0.032, 0.0, abs(uv.x)) * smoothstep(0.46, 0.0, abs(uv.y));
        float sparkle = (rayX + rayY) * smoothstep(0.5, 0.12, d) * 0.2;
        vec3 hot = mix(vColor, vec3(1.0, 0.94, 0.98), core * 0.72);
        float alpha = (core * 1.16 + halo * 0.36 + sparkle) * vAlpha;
        gl_FragColor = vec4(hot, alpha);
      }
    `,
  });

  const points = new THREE.Points(geometry, material);
  group.add(points);

  const linePairs = prefersReduced ? 160 : 520;
  const linePositions = new Float32Array(linePairs * 2 * 3);
  let written = 0;
  let attempts = 0;
  while (written < linePairs && attempts < linePairs * 80) {
    attempts += 1;
    const a = Math.floor(Math.random() * count);
    const b = Math.floor(Math.random() * count);
    if (a === b) continue;
    const ax = positions[a * 3], ay = positions[a * 3 + 1], az = positions[a * 3 + 2];
    const bx = positions[b * 3], by = positions[b * 3 + 1], bz = positions[b * 3 + 2];
    const dx = ax - bx, dy = ay - by, dz = az - bz;
    const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);
    if (dist > 0.1 && dist < 0.24) {
      const o = written * 6;
      linePositions[o] = ax; linePositions[o + 1] = ay; linePositions[o + 2] = az;
      linePositions[o + 3] = bx; linePositions[o + 4] = by; linePositions[o + 5] = bz;
      written += 1;
    }
  }
  const lineGeometry = new THREE.BufferGeometry();
  lineGeometry.setAttribute("position", new THREE.BufferAttribute(linePositions, 3));
  const lineMaterial = new THREE.LineBasicMaterial({
    color: 0xff436a,
    transparent: true,
    opacity: 0.18,
    blending: THREE.AdditiveBlending,
    depthWrite: false,
  });
  const photonLines = new THREE.LineSegments(lineGeometry, lineMaterial);
  group.add(photonLines);

  function resize() {
    const rect = canvas.getBoundingClientRect();
    const width = Math.max(1, Math.floor(rect.width));
    const height = Math.max(1, Math.floor(rect.height));
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
  }

  let raf = 0;
  const clock = new THREE.Clock();
  function animate() {
    const time = clock.getElapsedTime();
    const chatActive = document.querySelector(".mobile-shell")?.classList.contains("chat-active");
    const breathe = 1 + 0.055 * Math.sin(time * 1.15) + 0.018 * Math.sin(time * 2.8);
    const targetFov = chatActive ? 52 : 42;
    const targetZ = chatActive ? 3.82 : 4.95;
    camera.fov += (targetFov - camera.fov) * 0.055;
    camera.position.z += (targetZ - camera.position.z) * 0.055;
    camera.position.x = 0;
    camera.position.y = 0;
    camera.updateProjectionMatrix();
    material.uniforms.uTime.value = time;
    material.uniforms.uBreathe.value = breathe * (chatActive ? 1.08 : 1);
    group.rotation.y = time * (chatActive ? 0.48 : 0.32) + 0.18 * Math.sin(time * 0.53);
    group.rotation.x = (chatActive ? 0.26 : 0.16) * Math.sin(time * 0.37) + (chatActive ? 0.08 : 0);
    group.rotation.z = (chatActive ? 0.12 : 0.06) * Math.sin(time * 0.29);
    group.position.x = 0;
    group.position.y = chatActive ? -0.02 + 0.025 * Math.sin(time * 0.44) : 0;
    group.scale.setScalar((chatActive ? 1.32 : 1.04) * breathe);
    photonLines.material.opacity = (chatActive ? 0.2 : 0.12) + (chatActive ? 0.11 : 0.07) * Math.sin(time * 1.3);
    renderer.render(scene, camera);
    if (!prefersReduced) raf = requestAnimationFrame(animate);
  }

  resize();
  animate();
  window.addEventListener("resize", resize);
  document.addEventListener("visibilitychange", () => {
    if (document.hidden && raf) cancelAnimationFrame(raf);
    if (!document.hidden && !prefersReduced) animate();
  });
}

initSidebar();
initForm();
initParticleBrain();
setDebug();
setCommandText(statusCopy.ready);
