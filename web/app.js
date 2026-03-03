// ====== CONFIG ======
const API_URL = localStorage.getItem("RAG_API_URL") || "/api/query";

// ====== STATE ======
const LS_KEY = "rag_ui_state_v1";
let state = loadState();

// ====== DOM ======
const chatListEl = document.getElementById("chatList");
const messagesEl = document.getElementById("messages");
const welcomeEl = document.getElementById("welcome");
const formEl = document.getElementById("composerForm");
const inputEl = document.getElementById("promptInput");
const newChatBtn = document.getElementById("newChatBtn");
const usernameBtn = document.getElementById("usernameBtn");
const profileNameEl = document.getElementById("profileName");

// ====== INIT ======
syncUsernameUI();
ensureActiveChat();
renderAll();

// ====== EVENTS ======
newChatBtn.addEventListener("click", () => {
  const chat = createChat();
  state.chats.unshift(chat);
  state.activeChatId = chat.id;
  saveState();
  renderAll();
});

usernameBtn.addEventListener("click", () => {
  const next = prompt("Set your username:", state.username || "Username");
  if (next === null) return;
  state.username = (next || "Username").trim() || "Username";
  saveState();
  syncUsernameUI();
});

formEl.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = inputEl.value.trim();
  if (!text) return;

  const chat = getActiveChat();
  if (!chat) return;

  // add user message
  chat.messages.push({ role: "user", text, ts: Date.now() });
  if (!chat.title || chat.title === "New Chat") {
    chat.title = text.slice(0, 28) + (text.length > 28 ? "…" : "");
  }
  inputEl.value = "";
  saveState();
  renderAll();
  scrollMessagesToBottom();

  // add a temporary bot bubble
  const pendingId = crypto.randomUUID();
  chat.messages.push({ role: "assistant", text: "…", ts: Date.now(), pending: true, id: pendingId });
  saveState();
  renderAll();
  scrollMessagesToBottom();

  try {
    const res = await askRag({ query: text });

    // replace pending bubble
    const idx = chat.messages.findIndex(m => m.id === pendingId);
    if (idx !== -1) {
      chat.messages[idx] = {
        role: "assistant",
        text: res.answer ?? String(res),
        ts: Date.now(),
        sources: res.sources || null
      };
    }
    saveState();
    renderAll();
    scrollMessagesToBottom();
  } catch (err) {
    const idx = chat.messages.findIndex(m => m.id === pendingId);
    if (idx !== -1) {
      chat.messages[idx] = {
        role: "assistant",
        text: `Error calling API.\n${String(err?.message || err)}`,
        ts: Date.now()
      };
    }
    saveState();
    renderAll();
    scrollMessagesToBottom();
  }
});

// ====== RENDER ======
function renderAll() {
  renderChatList();
  renderMessages();
  renderWelcome();
}

function renderChatList() {
  const activeId = state.activeChatId;
  chatListEl.innerHTML = "";

  state.chats.forEach((chat) => {
    const item = document.createElement("div");
    item.className = "chatItem" + (chat.id === activeId ? " chatItem--active" : "");
    item.innerHTML = `
      <div class="chatItem__title">${escapeHtml(chat.title || "New Chat")}</div>
      <div class="chatItem__sub">${chat.messages.length} msgs</div>
    `;
    item.addEventListener("click", () => {
      state.activeChatId = chat.id;
      saveState();
      renderAll();
      scrollMessagesToBottom();
    });
    chatListEl.appendChild(item);
  });

  if (state.chats.length === 0) {
    const empty = document.createElement("div");
    empty.style.opacity = "0.8";
    empty.style.padding = "10px";
    empty.textContent = "No chats yet. Click “+ New”.";
    chatListEl.appendChild(empty);
  }
}

function renderMessages() {
  const chat = getActiveChat();
  messagesEl.innerHTML = "";

  if (!chat) return;

  chat.messages.forEach((m) => {
    const bubble = document.createElement("div");
    bubble.className = "bubble " + (m.role === "user" ? "bubble--user" : "bubble--bot");

    let text = m.text ?? "";
    if (m.pending) text = "Thinking…";

    bubble.textContent = text;

    // Optional: show sources if your API returns them
    if (m.sources && Array.isArray(m.sources) && m.sources.length) {
      const src = document.createElement("div");
      src.style.marginTop = "10px";
      src.style.fontSize = "12px";
      src.style.opacity = "0.85";
      src.textContent = "Sources: " + m.sources.map(s => s.title || s).join(" · ");
      bubble.appendChild(src);
    }

    messagesEl.appendChild(bubble);
  });
}

function renderWelcome() {
  const chat = getActiveChat();
  const hasMessages = chat && chat.messages && chat.messages.length > 0;
  welcomeEl.style.display = hasMessages ? "none" : "block";
}

function scrollMessagesToBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function syncUsernameUI() {
  const name = state.username || "Username";
  usernameBtn.textContent = name;
  profileNameEl.textContent = name;
}

// ====== API ======
async function askRag(payload) {
  const r = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return await r.json();
}

// ====== HELPERS ======
function createChat() {
  return {
    id: crypto.randomUUID(),
    title: "New Chat",
    messages: [],
    createdAt: Date.now()
  };
}

function ensureActiveChat() {
  if (!state.chats.length) {
    const chat = createChat();
    state.chats = [chat];
    state.activeChatId = chat.id;
    saveState();
    return;
  }
  if (!state.activeChatId || !state.chats.some(c => c.id === state.activeChatId)) {
    state.activeChatId = state.chats[0].id;
    saveState();
  }
}

function getActiveChat() {
  return state.chats.find(c => c.id === state.activeChatId) || null;
}

function loadState() {
  try {
    const raw = localStorage.getItem(LS_KEY);
    if (!raw) return { username: "Username", chats: [], activeChatId: null };
    const parsed = JSON.parse(raw);
    return {
      username: parsed.username || "Username",
      chats: Array.isArray(parsed.chats) ? parsed.chats : [],
      activeChatId: parsed.activeChatId || null,
    };
  } catch {
    return { username: "Username", chats: [], activeChatId: null };
  }
}

function saveState() {
  localStorage.setItem(LS_KEY, JSON.stringify(state));
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  }[c]));
}
