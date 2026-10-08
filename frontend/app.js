const $ = (s) => document.querySelector(s);

let currentSearchId = null;
let totalSites = 0;
let found = 0, notFound = 0, errors = 0, received = 0;
let selectedCategories = new Set();
let evtSource = null;

// ---------- inicialização ----------
async function loadSites() {
  const res = await fetch("/api/sites");
  const data = await res.json();
  const wrap = $("#categories");
  data.categories.forEach(cat => {
    const el = document.createElement("span");
    el.textContent = cat;
    el.onclick = () => {
      el.classList.toggle("active");
      el.classList.contains("active") ? selectedCategories.add(cat) : selectedCategories.delete(cat);
    };
    wrap.appendChild(el);
  });
}

async function loadHistory() {
  const res = await fetch("/api/history");
  const { history } = await res.json();
  const ul = $("#history-list");
  ul.innerHTML = "";
  history.slice(0, 20).forEach(h => {
    const li = document.createElement("li");
    li.textContent = `${h.username} (${h.found}/${h.total})`;
    li.onclick = () => renderAll(h);
    ul.appendChild(li);
  });
}

// ---------- busca ----------
$("#search-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const username = $("#username").value.trim();
  if (!/^[A-Za-z0-9._\-]{2,40}$/.test(username)) {
    alert("Username inválido. Use letras, números, ponto, hífen ou underscore (2-40 caracteres).");
    return;
  }

  if (evtSource) evtSource.close();
  resetUI();

  const body = {
    username,
    categories: selectedCategories.size ? [...selectedCategories] : null,
    include_nsfw: $("#nsfw").checked,
    deep_mode: false,
  };

  $("#btn-search").disabled = true;
  $("#progress-wrap").classList.remove("hidden");
  $("#actions").classList.remove("hidden");
  $("#results").innerHTML = "";

  // SSE
  evtSource = new EventSourcePolyfill("/api/search/stream", body);
  evtSource.onmessage = (e) => handleEvent(JSON.parse(e.data));
  evtSource.onerror = () => {
    $("#btn-search").disabled = false;
  };
});

// Fallback SSE com POST (EventSource nativo só aceita GET)
class EventSourcePolyfill {
  constructor(url, body) {
    this.url = url;
    this.body = body;
    this._abort = new AbortController();
    this.onmessage = () => {};
    this.onerror = () => {};
    this._start();
  }
  _start() {
    fetch(this.url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(this.body),
      signal: this._abort.signal,
    }).then(async (res) => {
      if (!res.ok || !res.body) { this.onerror(); return; }
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        const parts = buf.split("\n\n");
        buf = parts.pop();
        for (const block of parts) this._parse(block);
      }
    }).catch(() => this.onerror());
  }
  _parse(block) {
    const lines = block.split("\n");
    let event = "message";
    let data = "";
    for (const line of lines) {
      if (line.startsWith("event:")) event = line.slice(6).trim();
      else if (line.startsWith("data:")) data += line.slice(5).trim();
    }
    if (!data) return;
    try {
      const payload = JSON.parse(data);
      if (event === "message") this.onmessage({ data });
      else this.onmessage({ data });
      // also handle "meta" and "done" via same onmessage
      if (payload.type === "meta" || event === "meta") {
        // tratado no handleEvent
      }
    } catch (_) {}
  }
  close() { this._abort.abort(); }
}

// Intercepta eventos meta/result/done
let originalOnMessage = null;
function attachHandler() {
  if (!evtSource) return;
  const raw = evtSource.onmessage;
  evtSource.onmessage = (e) => {
    const parsed = JSON.parse(e.data);
    // Detecta tipo de payload
    if (parsed.variations && parsed.dorks) {
      handleMeta(parsed);
    } else if (parsed.type === "result") {
      handleResult(parsed.data);
    } else if (parsed.type === "done") {
      handleDone(parsed.data);
    } else if (parsed.type === "error") {
      alert("Erro: " + parsed.data);
      $("#btn-search").disabled = false;
    }
  };
}

function handleEvent(parsed) {
  if (parsed.variations) return handleMeta(parsed);
  if (parsed.type === "result") return handleResult(parsed.data);
  if (parsed.type === "done") return handleDone(parsed.data);
  if (parsed.type === "error") { alert("Erro: " + parsed.data); $("#btn-search").disabled = false; }
}

// aplica o handler após criar o EventSource
const _origForm = $("#search-form");
const _origSubmit = _origForm.onsubmit;

// ---------- handlers ----------
function handleMeta(meta) {
  currentSearchId = meta.search_id;
  totalSites = meta.total_sites;
  $("#c-max").textContent = totalSites;
  $("#extras").classList.remove("hidden");

  const v = $("#variations"); v.innerHTML = "";
  Object.values(meta.variations).forEach(val => {
    const s = document.createElement("span");
    s.textContent = val;
    s.onclick = () => { $("#username").value = val; };
    v.appendChild(s);
  });

  const d = $("#dorks"); d.innerHTML = "";
  meta.dorks.forEach(dork => {
    const s = document.createElement("span");
    s.textContent = dork;
    s.onclick = () => navigator.clipboard.writeText(dork);
    d.appendChild(s);
  });

  const e = $("#engines"); e.innerHTML = "";
  Object.entries(meta.search_engines).forEach(([name, url]) => {
    const a = document.createElement("a");
    a.href = url; a.target = "_blank"; a.textContent = name + " ";
    a.style.marginRight = "8px";
    e.appendChild(a);
  });

  $("#gravatar").href = meta.gravatar;
}

function handleResult(r) {
  received++;
  if (r.status === "encontrado") found++;
  else if (r.status === "não encontrado") notFound++;
  else if (r.status === "erro") errors++;

  $("#c-found").textContent = found;
  $("#c-nf").textContent = notFound;
  $("#c-err").textContent = errors;
  $("#c-total").textContent = received;
  $("#progress-fill").style.width = (received / Math.max(totalSites, 1) * 100) + "%";

  appendCard(r);
}

function handleDone(summary) {
  $("#btn-search").disabled = false;
  $("#progress-fill").style.width = "100%";
  loadHistory();
}

// ---------- render ----------
const categoryNames = {
  rede_social: "🌐 Redes Sociais",
  dev: "💻 Desenvolvimento",
  gaming: "🎮 Gaming",
  streaming: "🎵 Streaming",
  profissional: "💼 Profissional",
  apoio: "☕ Apoio/Crowdfunding",
  links: "🔗 Links",
  forum: "💬 Fóruns",
  nsfw: "🔞 Adulto",
};

function appendCard(r) {
  const container = $("#results");
  const catTitle = `cat-${r.category}`;
  let section = document.getElementById(catTitle);
  if (!section) {
    section = document.createElement("div");
    section.id = catTitle;
    section.className = "category-title";
    section.textContent = categoryNames[r.category] || r.category;
    container.appendChild(section);
  }
  const card = document.createElement("div");
  card.className = "card";
  const statusClass = r.status.replace(/\s+/g, ".");
  card.innerHTML = `
    <div class="head">
      <div class="name">${r.icon || "🌐"} ${r.site}</div>
      <div class="status ${statusClass}">${r.status}</div>
    </div>
    <div class="meta">
      <span>Confiança: ${r.confidence}%</span>
      <span>${r.elapsed_ms || 0} ms</span>
    </div>
    ${r.status === "encontrado" ? `<a href="${r.url}" target="_blank">${r.url}</a>` : ""}
    <div class="meta"><span>${r.detail || ""}</span></div>
  `;
  section.after(card);
}

function renderAll(summary) {
  resetUI();
  $("#actions").classList.remove("hidden");
  totalSites = summary.total;
  $("#c-max").textContent = summary.total;
  summary.results.forEach(r => handleResult(r));
  $("#progress-fill").style.width = "100%";
}

function resetUI() {
  found = notFound = errors = received = 0;
  $("#c-found").textContent = 0;
  $("#c-nf").textContent = 0;
  $("#c-err").textContent = 0;
  $("#c-total").textContent = 0;
  $("#c-max").textContent = 0;
  $("#progress-fill").style.width = "0";
  $("#results").innerHTML = "";
  $("#extras").classList.add("hidden");
  $("#progress-wrap").classList.add("hidden");
}

// ---------- ações ----------
$("#actions").addEventListener("click", async (e) => {
  const fmt = e.target.dataset.fmt;
  if (fmt && currentSearchId) {
    window.open(`/api/export/${currentSearchId}?format=${fmt}`, "_blank");
  }
});

$("#btn-copy").onclick = () => {
  const text = [...document.querySelectorAll(".card")].map(c =>
    c.querySelector(".name").textContent.trim() + " | " +
    c.querySelector(".status").textContent.trim() + " | " +
    (c.querySelector("a")?.href || "")
  ).join("\n");
  navigator.clipboard.writeText(text);
  $("#btn-copy").textContent = "✅ Copiado!";
  setTimeout(() => $("#btn-copy").textContent = "📋 Copiar", 1500);
};

$("#btn-new").onclick = () => {
  if (evtSource) evtSource.close();
  resetUI();
  $("#username").value = "";
  $("#username").focus();
  $("#actions").classList.add("hidden");
};

// reattach handler após criar EventSource
const _origEventSource = window.EventSourcePolyfill;
const originalStart = EventSourcePolyfill.prototype._start;
EventSourcePolyfill.prototype._start = function () {
  const oldOnMessage = this.onmessage;
  this.onmessage = oldOnMessage;
  originalStart.call(this);
};
// aplica handler pós-criação
const applyHandler = setInterval(() => {
  if (evtSource) {
    const cur = evtSource.onmessage;
    if (!cur._patched) {
      evtSource.onmessage = (e) => handleEvent(JSON.parse(e.data));
      evtSource.onmessage._patched = true;
      clearInterval(applyHandler);
    }
  }
}, 100);

loadSites();
loadHistory();
