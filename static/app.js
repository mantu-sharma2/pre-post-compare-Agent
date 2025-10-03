const chatEl = document.getElementById("chat");
const formEl = document.getElementById("chat-form");
const inputEl = document.getElementById("query");

function appendMessage(role, text) {
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  div.appendChild(bubble);
  chatEl.appendChild(div);
  chatEl.scrollTop = chatEl.scrollHeight;
}

function escapeHtml(s) {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function formatAnswer(raw) {
  if (!raw || typeof raw !== "string") return escapeHtml(String(raw));
  // If server already returns HTML, pass through
  if (/<\/?(p|div|table|ul|ol|section|h\d|hr|br|strong|em)/i.test(raw)) {
    return raw;
  }
  const lines = raw
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter(Boolean);
  // Detect strict 3-line comparison (ensure truly three lines)
  if (
    lines.length >= 3 &&
    /^structure:\s*/i.test(lines[0]) &&
    /^values:\s*/i.test(lines[1]) &&
    /^differences:\s*/i.test(lines[2])
  ) {
    const structureVal = escapeHtml((lines[0].split(":")[1] || "").trim());
    const valuesVal = escapeHtml((lines[1].split(":")[1] || "").trim());
    const diffsLine = lines[2];
    const afterLabel = diffsLine.replace(/^differences:\s*/i, "").trim();
    let diffsHtml = '<div class="kv">-</div>';
    if (afterLabel && afterLabel !== "-") {
      // Robustly split items like "1. x; 2. y; 3. z" while preserving content
      let items = afterLabel
        .split(/\s*;\s*/)
        .map((s) => s.replace(/^\d+\.?\s*/, "").trim())
        .filter(Boolean);
      if (items.length > 3) items = items.slice(0, 3);
      if (items.length) {
        const lis = items.map((it) => `<li>${escapeHtml(it)}</li>`).join("");
        diffsHtml = `<ol class=\"diff-list\">${lis}</ol>`;
      }
    }
    return (
      '<div class="structured">' +
      `<div class=\"kv\"><strong>Structure:</strong> ${structureVal}</div>` +
      `<div class=\"kv\"><strong>Values:</strong> ${valuesVal}</div>` +
      `<div class=\"kv\"><strong>Differences:</strong></div>` +
      diffsHtml +
      "</div>"
    );
  }
  // Generic formatter: bold keys before ':' and place each on its own line
  const html = lines
    .map((l) => {
      const m = l.match(/^([^:]+):\s*(.*)$/);
      if (m) {
        return `<div class=\"kv\"><strong>${escapeHtml(
          m[1]
        )}:</strong> ${escapeHtml(m[2])}</div>`;
      }
      return `<div class=\"line\">${escapeHtml(l)}</div>`;
    })
    .join("");
  return `<div class=\"structured\">${html}</div>`;
}

formEl.addEventListener("submit", async (e) => {
  e.preventDefault();
  const q = inputEl.value.trim();
  if (!q) return;
  appendMessage("user", q);
  inputEl.value = "";
  appendMessage("bot", "Thinking...");
  try {
    const resp = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: q, full: true }),
    });
    const data = await resp.json();
    const bubble = chatEl.lastChild.querySelector(".bubble");
    bubble.innerHTML = formatAnswer(data.answer || JSON.stringify(data));
  } catch (err) {
    chatEl.lastChild.querySelector(".bubble").textContent =
      "Error contacting server.";
  }
});
