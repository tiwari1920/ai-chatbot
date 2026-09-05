/*
 * AI Chatbot — Frontend logic
 * Created by: Satyam Tiwari (iamsatyampandit@gmail.com)
 *
 * Plain HTML/CSS/JS, no build step. Talks to the FastAPI backend under /api.
 */

const API_BASE = "/api";

const els = {
  messages: document.getElementById("messages"),
  emptyState: document.getElementById("emptyState"),
  form: document.getElementById("composerForm"),
  input: document.getElementById("messageInput"),
  sendBtn: document.getElementById("sendBtn"),
  historyList: document.getElementById("historyList"),
  historyEmpty: document.getElementById("historyEmpty"),
  newChatBtn: document.getElementById("newChatBtn"),
  chatTitle: document.getElementById("chatTitle"),
  statusDot: document.getElementById("statusDot"),
  statusText: document.getElementById("statusText"),
  modelName: document.getElementById("modelName"),
};

const state = {
  sessionId: getOrCreateSessionId(),
  conversationId: null,
};

function getOrCreateSessionId() {
  let id = localStorage.getItem("chat_session_id");
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem("chat_session_id", id);
  }
  return id;
}

/* ---------- Rendering ---------- */

function clearMessages() {
  els.messages.innerHTML = "";
}

function showEmptyState(show) {
  if (show) {
    els.messages.innerHTML = "";
    els.messages.appendChild(els.emptyState);
  }
}

function appendMessage(role, content, { pending = false } = {}) {
  if (els.messages.contains(els.emptyState)) {
    els.emptyState.remove();
  }
  const wrap = document.createElement("div");
  wrap.className = `msg ${role}${pending ? " typing" : ""}`;

  const roleLabel = document.createElement("div");
  roleLabel.className = "role";
  roleLabel.textContent = role === "user" ? "You" : "Assistant";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = content;

  wrap.appendChild(roleLabel);
  wrap.appendChild(bubble);
  els.messages.appendChild(wrap);
  els.messages.scrollTop = els.messages.scrollHeight;
  return wrap;
}

/* ---------- API calls ---------- */

async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    const about = await (await fetch(`${API_BASE}/about`)).json();
    if (res.ok) {
      els.statusDot.classList.add("online");
      els.statusText.textContent = "Connected";
      els.modelName.textContent = about.version ? `v${about.version}` : "ready";
    } else {
      throw new Error("bad status");
    }
  } catch {
    els.statusDot.classList.add("offline");
    els.statusText.textContent = "Backend unreachable";
  }
}

async function sendMessage(text) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message: text,
      session_id: state.sessionId,
      conversation_id: state.conversationId,
    }),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

async function loadHistory() {
  try {
    const res = await fetch(`${API_BASE}/conversations?session_id=${state.sessionId}`);
    if (!res.ok) return;
    const conversations = await res.json();
    renderHistory(conversations);
  } catch {
    /* silent — history is a nice-to-have */
  }
}

async function openConversation(id) {
  const res = await fetch(`${API_BASE}/conversations/${id}?session_id=${state.sessionId}`);
  if (!res.ok) return;
  const data = await res.json();
  state.conversationId = data.id;
  els.chatTitle.textContent = data.title;
  clearMessages();
  data.messages.forEach((m) => appendMessage(m.role, m.content));
  markActiveHistoryItem(id);
}

/* ---------- History sidebar ---------- */

function renderHistory(conversations) {
  els.historyList.innerHTML = "";
  if (!conversations.length) {
    els.historyList.appendChild(els.historyEmpty);
    return;
  }
  conversations.forEach((c) => {
    const item = document.createElement("div");
    item.className = "history-item";
    item.dataset.id = c.id;
    item.textContent = c.title || "Untitled conversation";
    item.addEventListener("click", () => openConversation(c.id));
    els.historyList.appendChild(item);
  });
  markActiveHistoryItem(state.conversationId);
}

function markActiveHistoryItem(id) {
  document.querySelectorAll(".history-item").forEach((el) => {
    el.classList.toggle("active", el.dataset.id === id);
  });
}

/* ---------- Composer ---------- */

els.input.addEventListener("input", () => {
  els.input.style.height = "auto";
  els.input.style.height = Math.min(els.input.scrollHeight, 160) + "px";
});

els.input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    els.form.requestSubmit();
  }
});

els.form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = els.input.value.trim();
  if (!text) return;

  els.input.value = "";
  els.input.style.height = "auto";
  els.sendBtn.disabled = true;

  appendMessage("user", text);
  const pending = appendMessage("assistant", "Thinking…", { pending: true });

  try {
    const data = await sendMessage(text);
    state.conversationId = data.conversation_id;
    pending.classList.remove("typing");
    pending.querySelector(".bubble").textContent = data.reply;
    els.chatTitle.textContent = text.slice(0, 60);
    loadHistory();
  } catch (err) {
    pending.classList.remove("typing");
    pending.classList.add("error");
    pending.querySelector(".bubble").textContent = `Something went wrong: ${err.message}`;
  } finally {
    els.sendBtn.disabled = false;
    els.input.focus();
  }
});

els.newChatBtn.addEventListener("click", () => {
  state.conversationId = null;
  els.chatTitle.textContent = "New conversation";
  showEmptyState(true);
  markActiveHistoryItem(null);
  els.input.focus();
});

/* ---------- Boot ---------- */

checkHealth();
loadHistory();
els.input.focus();
