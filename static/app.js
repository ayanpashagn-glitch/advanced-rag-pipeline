"use strict";
const $ = (s) => document.querySelector(s);
let docs = [],
  selected = new Set(),
  conversation = null,
  mode = "ask",
  busy = false;
const messages = $("#messages");
function node(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text !== undefined) e.textContent = text;
  return e;
}
async function api(path, options = {}) {
  const r = await fetch("/api" + path, options);
  const data = await r.json();
  if (!r.ok)
    throw Error(
      typeof data.detail === "string"
        ? data.detail
        : "Invalid request. Check the selected documents and question.",
    );
  return data;
}
function post(path, body) {
  return api(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}
function notice(text, error = false) {
  $("#notice").hidden = !text;
  $("#notice").textContent = text;
  $("#notice").className = error ? "error" : "";
}
function scope() {
  $("#scope").textContent = selected.size
    ? `${selected.size} source${selected.size === 1 ? "" : "s"} selected · ${mode === "compare" ? "select exactly two" : "answers stay within this scope"}`
    : "No sources selected";
}
async function task(label, fn) {
  if (busy) return;
  busy = true;
  $("#activity").textContent = label;
  document
    .querySelectorAll("button,input,textarea")
    .forEach((e) => (e.disabled = true));
  notice("");
  try {
    await fn();
  } catch (e) {
    notice(e.message, true);
  } finally {
    busy = false;
    $("#activity").textContent = "";
    document
      .querySelectorAll("button,input,textarea")
      .forEach((e) => (e.disabled = false));
    scope();
  }
}
async function loadDocs() {
  docs = await api("/documents");
  selected = new Set(
    [...selected].filter((id) => docs.some((d) => d.id === id)),
  );
  $("#doc-count").textContent = `${docs.length} / 12`;
  const box = $("#documents");
  box.replaceChildren();
  if (!docs.length) box.append(node("p", "empty-small", "No documents yet."));
  for (const d of docs) {
    const card = node("div", "document"),
      label = node("label"),
      check = node("input");
    check.type = "checkbox";
    check.checked = selected.has(d.id);
    check.addEventListener("change", () => {
      check.checked ? selected.add(d.id) : selected.delete(d.id);
      scope();
    });
    label.append(check, node("strong", "", d.name));
    card.append(
      label,
      node(
        "small",
        "",
        `${d.pages} pages · ${d.chunks} chunks · ${d.indexed ? "indexed" : "not indexed"}`,
      ),
    );
    const actions = node("div", "doc-actions");
    const view = node("button", "text-button", "View text");
    view.onclick = () =>
      showSource({ document_id: d.id, page: 1, name: d.name, quote: "" });
    const reindex = node("button", "text-button", "Reindex");
    reindex.onclick = () =>
      task("Indexing…", async () => {
        await post(`/documents/${d.id}/reindex`, {});
        await loadDocs();
        notice("Semantic index ready.");
      });
    const del = node("button", "text-button danger", "Delete");
    del.onclick = () => {
      if (
        confirm(
          `Delete ${d.name}? Old chat excerpts remain, but source pages become unavailable.`,
        )
      )
        task("Deleting…", async () => {
          await api("/documents/" + d.id, { method: "DELETE" });
          await loadDocs();
        });
    };
    actions.append(view, reindex, del);
    card.append(actions);
    box.append(card);
  }
  scope();
}
async function loadConversations() {
  const items = await api("/conversations");
  const box = $("#conversations");
  box.replaceChildren();
  for (const c of items) {
    const b = node(
      "button",
      "history-item" + (c.id === conversation ? " active" : ""),
      c.title,
    );
    b.title = c.title;
    b.onclick = () =>
      task("Loading history…", async () => {
        conversation = c.id;
        await renderHistory();
        await loadConversations();
      });
    box.append(b);
  }
}
async function newChat() {
  const c = await post("/conversations", {});
  conversation = c.id;
  messages.replaceChildren(
    node(
      "p",
      "empty-small",
      "New investigation. Select documents and ask a question.",
    ),
  );
  await loadConversations();
}
async function renderHistory() {
  const history = await api("/conversations/" + conversation);
  messages.replaceChildren();
  for (const m of history) {
    if (m.role === "user")
      messages.append(node("div", "message user", m.content));
    else renderAnswer(m.content);
  }
  if (!history.length)
    messages.append(
      node("p", "empty-small", "No questions in this investigation yet."),
    );
}
function renderAnswer(data) {
  messages.querySelector(".welcome")?.remove();
  messages.querySelector(".empty-small")?.remove();
  const card = node("article", "message answer");
  const head = node("div", "answer-head");
  head.append(
    node(
      "strong",
      "",
      data.kind === "summary"
        ? "DOCUMENT BRIEF"
        : data.kind === "comparison"
          ? "DOCUMENT COMPARISON"
          : "ASTRA INTEL",
    ),
    node("span", "", data.provider || "source search"),
  );
  if (data.cached) head.append(node("span", "", "cached result"));
  if (data.retrieval)
    head.append(node("span", "", data.retrieval + " retrieval"));
  card.append(head, node("p", "answer-note", data.message || ""));
  for (const c of data.claims || []) {
    const claim = node("section", "claim");
    claim.append(node("p", "", c.text));
    if (c.quote && c.quote !== c.text)
      claim.append(node("blockquote", "", c.quote));
    const button = node("button", "citation", `${c.name} · page ${c.page} ↗`);
    button.onclick = () => showSource(c);
    claim.append(button);
    card.append(claim);
  }
  if (data.rejected_claims)
    card.append(
      node(
        "p",
        "answer-note",
        `${data.rejected_claims} unsupported or unverifiable claim(s) withheld.`,
      ),
    );
  messages.append(card);
  messages.scrollTop = messages.scrollHeight;
}
async function showSource(c) {
  try {
    const p = await api(`/documents/${c.document_id}/pages/${c.page}`);
    $("#source-title").textContent =
      `${p.name} / page ${p.number}${p.ocr ? " / OCR" : ""}`;
    const target = $("#source-text");
    target.replaceChildren();
    const text = p.text.replace(/\s+/g, " ").trim(),
      quote = (c.quote || "").replace(/\s+/g, " ").trim();
    const i = quote ? text.indexOf(quote) : -1;
    if (i >= 0) {
      target.append(
        document.createTextNode(text.slice(0, i)),
        node("mark", "", text.slice(i, i + quote.length)),
        document.createTextNode(text.slice(i + quote.length)),
      );
    } else target.textContent = p.text;
    $("#source-dialog").showModal();
  } catch (e) {
    notice("Source unavailable: " + e.message, true);
  }
}
$("#close-source").onclick = () => $("#source-dialog").close();
$("#upload-form").onsubmit = (e) => {
  e.preventDefault();
  task("Uploading & indexing…", async () => {
    const files = [...$("#file").files];
    if (!files.length) throw Error("Choose at least one document.");
    let warnings = [];
    for (const file of files) {
      const body = new FormData();
      body.append("file", file);
      body.append("ocr", $("#ocr").checked);
      const result = await api("/documents", { method: "POST", body });
      selected.add(result.id);
      warnings.push(...result.warnings);
      await loadDocs();
    }
    $("#file").value = "";
    notice(
      warnings.length
        ? warnings.join("\n")
        : "Documents uploaded and indexed. You can now summarize or ask a question.",
    );
  });
};
const drop = $("#dropzone");
for (const event of ["dragenter", "dragover"])
  drop.addEventListener(event, (e) => {
    e.preventDefault();
    drop.classList.add("drag");
  });
for (const event of ["dragleave", "drop"])
  drop.addEventListener(event, (e) => {
    e.preventDefault();
    drop.classList.remove("drag");
  });
drop.addEventListener("drop", (e) => {
  if (!busy) $("#file").files = e.dataTransfer.files;
});
document.querySelectorAll("[data-mode]").forEach(
  (b) =>
    (b.onclick = () => {
      mode = b.dataset.mode;
      document
        .querySelectorAll("[data-mode]")
        .forEach((x) => x.classList.toggle("active", x === b));
      $("#send").textContent =
        mode === "search"
          ? "Search ↗"
          : mode === "compare"
            ? "Compare ↗"
            : "Ask ↗";
      $("#question").placeholder =
        mode === "compare"
          ? "Which topic should the two selected documents be compared on?"
          : "Ask a question about your selected documents…";
      scope();
    }),
);
document.querySelectorAll("[data-question]").forEach(
  (b) =>
    (b.onclick = () => {
      $("#question").value = b.dataset.question;
      $("#question").focus();
    }),
);
$("#new-chat").onclick = () => task("Creating conversation…", newChat);
$("#summarize").onclick = () =>
  task("Summarizing every section…", async () => {
    if (!selected.size) throw Error("Upload and select a document first.");
    const answer = await post("/summary", { document_ids: [...selected] });
    renderAnswer(answer);
    notice(
      "Summary generated. Summaries can be regenerated from the cache; Q&A history is saved automatically.",
    );
  });
$("#question-form").onsubmit = (e) => {
  e.preventDefault();
  task(
    mode === "search" ? "Searching…" : "Retrieving & checking evidence…",
    async () => {
      const question = $("#question").value.trim();
      if (!selected.size) throw Error("Upload and select a document first.");
      if (!question) throw Error("Enter a question.");
      if (mode === "compare" && selected.size !== 2)
        throw Error("Select exactly two documents to compare.");
      if (!conversation) await newChat();
      const body = {
        question,
        document_ids: [...selected],
        conversation_id: conversation,
        compare: mode === "compare",
      };
      if (mode === "search") {
        const data = await post("/search", body);
        renderAnswer({
          kind: "search",
          provider: data.mode + " search",
          message:
            "Retrieved passages, not an AI-generated answer. Search scores are ranking signals, not confidence probabilities.",
          claims: data.results.map((c) => ({ ...c, quote: c.text })),
        });
      } else {
        const answer = await post("/ask", body);
        messages.querySelector(".welcome")?.remove();
        messages.querySelector(".empty-small")?.remove();
        messages.append(node("div", "message user", question));
        renderAnswer(answer);
        await loadConversations();
      }
      $("#question").value = "";
    },
  );
};
$("#question").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    $("#question-form").requestSubmit();
  }
});
(async () => {
  try {
    const status = await api("/status");
    $("#model").textContent =
      `${status.provider.toUpperCase()} / ${status.chat_model}`;
    $("#status-note").textContent = status.mode_notice;
    $("#privacy").textContent = status.privacy;
    $("#ocr-state").textContent = status.ocr_available
      ? "available"
      : "needs Tesseract";
    await loadDocs();
    const chats = await api("/conversations");
    if (chats.length) {
      conversation = chats[0].id;
      await renderHistory();
    }
    await loadConversations();
    if (status.provider === "groq" && !status.key_configured)
      notice(
        "GROQ_API_KEY is missing. Add it to .env and restart, or switch to Ollama.",
        true,
      );
  } catch (e) {
    notice(e.message, true);
  }
})();
