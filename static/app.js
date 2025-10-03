const chatEl = document.getElementById("chat");
const formEl = document.getElementById("chat-form");
const inputEl = document.getElementById("query");
const fullEl = document.getElementById("full-context");

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
      body: JSON.stringify({ query: q, full: !!(fullEl && fullEl.checked) }),
    });
    const data = await resp.json();
    const bubble = chatEl.lastChild.querySelector(".bubble");
    // If server returns HTML, render it as HTML; else text
    if (
      data &&
      typeof data.answer === "string" &&
      /<\/?(p|div|table|ul|ol|section|h\d|hr)/i.test(data.answer)
    ) {
      bubble.innerHTML = data.answer;
    } else {
      bubble.textContent = data.answer || JSON.stringify(data);
    }
  } catch (err) {
    chatEl.lastChild.querySelector(".bubble").textContent =
      "Error contacting server.";
  }
});
