const chat = document.getElementById("chat");
const form = document.getElementById("composer");
const input = document.getElementById("query");

function addBubble(text, role, meta = "") {
  const wrap = document.createElement("div");
  wrap.className = `bubble ${role}`;
  wrap.textContent = text;
  if (meta) {
    const metaEl = document.createElement("div");
    metaEl.className = "meta";
    metaEl.textContent = meta;
    wrap.appendChild(metaEl);
  }
  chat.appendChild(wrap);
  chat.scrollTop = chat.scrollHeight;
  return wrap;
}

function addLoadingBubble() {
  const wrap = document.createElement("div");
  wrap.className = "bubble bot";
  const loading = document.createElement("div");
  loading.className = "loading";
  loading.innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span>';
  wrap.appendChild(loading);
  chat.appendChild(wrap);
  chat.scrollTop = chat.scrollHeight;
  return wrap;
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const q = input.value.trim();
  if (!q) return;

  addBubble(q, "user");
  input.value = "";
  input.focus();

  const loadingBubble = addLoadingBubble();
  form.querySelector("button").disabled = true;

  try {
    const res = await fetch("/api/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: q })
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || "Request failed");
    }

    const data = await res.json();
    loadingBubble.remove();
    addBubble(data.answer || "(no answer)", "bot", data.sources ? `Sources: ${data.sources.join(", ")}` : "");
  } catch (err) {
    loadingBubble.remove();
    addBubble(`Error: ${err.message}`, "bot");
  } finally {
    form.querySelector("button").disabled = false;
  }
});
