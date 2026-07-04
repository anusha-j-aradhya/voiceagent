/*
app.js
------
Owns the conversation state (same "resend full history" pattern as the CLI
projects), handles voice input via the Web Speech API's SpeechRecognition,
voice output via speechSynthesis, and renders tool_events as visible chips
so you can watch the agent's reasoning steps.

Voice APIs used here (SpeechRecognition, speechSynthesis) are built into
Chrome and Edge. Firefox/Safari support is partial or absent — use Chrome
or Edge for the full experience.
*/

const chatEl = document.getElementById("chat");
const emptyState = document.getElementById("emptyState");
const micButton = document.getElementById("micButton");
const micWrap = document.querySelector(".mic-wrap");
const statusLabel = document.getElementById("statusLabel");
const textForm = document.getElementById("textForm");
const textInput = document.getElementById("textInput");

let messages = []; // conversation history: [{role, content}]

function setStatus(state) {
  // state: "idle" | "listening" | "thinking" | "speaking"
  statusLabel.textContent = state;
  statusLabel.className = "status-label " + state;
  micWrap.className = "mic-wrap " + state;
  micButton.className = "mic-button " + state;
}

function addBubble(role, text) {
  emptyState.style.display = "none";
  const div = document.createElement("div");
  div.className = "bubble " + role;
  div.textContent = text;
  chatEl.appendChild(div);
  chatEl.scrollTop = chatEl.scrollHeight;
}

function addToolChip(event) {
  const div = document.createElement("div");
  div.className = "tool-chip";
  const argsStr = Object.values(event.args || {}).join(", ");
  div.innerHTML = `<span class="tool-name">${event.name}(${argsStr})</span>` +
                  `<span class="tool-result">→ ${event.result}</span>`;
  chatEl.appendChild(div);
  chatEl.scrollTop = chatEl.scrollHeight;
}

async function sendMessage(text) {
  if (!text.trim()) return;

  addBubble("user", text);
  messages.push({ role: "user", content: text });
  setStatus("thinking");

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages }),
    });

    if (!res.ok) throw new Error("Server error: " + res.status);

    const data = await res.json();

    for (const event of data.tool_events || []) {
      addToolChip(event);
    }

    addBubble("agent", data.reply);
    messages.push({ role: "assistant", content: data.reply });

    speak(data.reply);
  } catch (err) {
    addBubble("agent", "Something went wrong talking to the server: " + err.message);
    setStatus("idle");
  }
}

function speak(text) {
  if (!("speechSynthesis" in window)) {
    setStatus("idle");
    return;
  }
  setStatus("speaking");
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1.02;
  utterance.onend = () => setStatus("idle");
  utterance.onerror = () => setStatus("idle");
  window.speechSynthesis.cancel(); // stop any prior speech first
  window.speechSynthesis.speak(utterance);
}

/* ---------- Voice input ---------- */

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognizer = null;

if (SpeechRecognition) {
  recognizer = new SpeechRecognition();
  recognizer.continuous = false;
  recognizer.interimResults = false;
  recognizer.lang = "en-US";

  recognizer.onresult = (e) => {
    const transcript = e.results[0][0].transcript;
    sendMessage(transcript);
  };

  recognizer.onerror = (e) => {
    console.error("Speech recognition error:", e.error);
    setStatus("idle");
  };

  recognizer.onend = () => {
    if (statusLabel.textContent === "listening") setStatus("idle");
  };
} else {
  statusLabel.textContent = "voice not supported — use Chrome/Edge";
}

micButton.addEventListener("click", () => {
  if (!recognizer) return;

  // Interrupt agent speech if the user wants to talk again
  window.speechSynthesis.cancel();

  if (statusLabel.textContent === "listening") {
    recognizer.stop();
    setStatus("idle");
    return;
  }

  setStatus("listening");
  recognizer.start();
});

/* ---------- Text fallback ---------- */

textForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = textInput.value;
  textInput.value = "";
  sendMessage(text);
});

setStatus("idle");
