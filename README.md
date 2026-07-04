# Voice Agent

A full voice-conversation AI agent with a real UI: talk to it, watch it
decide to call tools, and hear it talk back — all running locally, powered
by your free Groq API key.

## What this demonstrates

Everything from the earlier CLI projects, now with a real interface:

| Concept | Where |
|---|---|
| Multi-turn conversation | `app.js` — `messages` array resent every request, same pattern as the CLI |
| Tool use / agent loop | `app.py` — the `while choice.finish_reason == "tool_calls"` loop |
| RAG | `tools.py`'s `search_facts()`, backed by `knowledge_base.py` |
| Voice input | Browser's `SpeechRecognition` API (`app.js`) — converts your speech to text |
| Voice output | Browser's `speechSynthesis` API (`app.js`) — reads the agent's reply aloud |
| Visible agent reasoning | Tool calls render as live teal chips in the chat, so you see *when and why* the agent decided to use a tool |

## Setup

```powershell
cd voice_agent
python -m pip install -r requirements.txt
$env:GROQ_API_KEY="gsk_your_key_here"
python app.py
```

Then open **http://localhost:5000** in **Chrome or Edge** (voice APIs need
one of these — Firefox/Safari support is limited or missing).

## How to use it

1. Click the mic button, say something like:
   *"What's 847 times 23?"*
2. Watch it: transcribes your speech → sends to the agent → agent decides to
   call the `calculator` tool → you see a teal chip showing the tool call and
   its result → the agent's reply appears and is read aloud.
3. Try: *"What's the difference between Sonnet and Opus?"* — this triggers
   the `search_facts` tool (RAG over the local knowledge base).
4. Try: *"What time is it?"* — triggers `get_current_time`.
5. No mic? Type in the text box at the bottom instead — same agent, same
   tool use, just skips voice input. The reply is still spoken aloud.

## Why a chip appears for tool calls

The agent doesn't secretly run code — it can only ask your backend
(`app.py`) to run a specific tool with specific arguments. That request →
run → respond loop is the same one you saw in the CLI version; this UI just
makes it visible instead of scrolling past in a terminal. That visibility is
the whole point of this project — you're watching an LLM agent's decisions,
not just its final answer.

## Known limitations

- Conversation history lives only in the browser tab's memory — refreshing
  the page clears it (same as restarting the CLI script).
- Voice input requires Chrome or Edge; the text box always works as a fallback.
- If your mic permission is blocked, Chrome will prompt you the first time
  you click the mic button — allow it.
- The agent is instructed to keep replies short/conversational since they're
  read aloud — if you want longer, more detailed answers, use the text box
  and ask it to "explain in detail."

## Natural next steps

- Add a "stop speaking" button (currently speech is interrupted only by
  starting a new voice input)
- Persist conversation history to a file or database
- Add more tools (a real web search, weather, etc.)
- Swap `speechSynthesis` (robotic default voice) for a nicer TTS API if you
  want more natural-sounding speech
