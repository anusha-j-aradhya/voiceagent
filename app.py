"""
app.py
------
Flask backend for the Voice Agent. Exposes one endpoint:

    POST /api/chat
        body: {"messages": [{"role": "user"/"assistant", "content": "..."}]}
        returns: {"reply": "...", "tool_events": [{"name", "args", "result"}]}

The frontend (static/app.js) owns the conversation history and resends it
every request — same pattern as the CLI projects, just over HTTP now.

Setup:
    pip install -r requirements.txt
    $env:GROQ_API_KEY="gsk_your_key_here"
    python app.py
    -> open http://localhost:5000 in Chrome or Edge (needed for voice)
"""

import os
import json
from flask import Flask, request, jsonify, render_template
from groq import Groq

from tools import TOOLS, run_tool

MODEL = "llama-3.3-70b-versatile"

app = Flask(__name__)

api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    raise RuntimeError(
        "Set GROQ_API_KEY before starting the server. "
        "Get a free key at https://console.groq.com/keys"
    )
client = Groq(api_key=api_key)

SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are a helpful, friendly voice assistant. Keep answers concise and "
        "conversational since they will be read aloud (avoid long lists or "
        "markdown formatting). Use your tools when they'd genuinely help "
        "answer the question."
    ),
}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json()
    messages = data.get("messages", [])
    full_messages = [SYSTEM_PROMPT] + messages

    tool_events = []

    response = client.chat.completions.create(
        model=MODEL,
        messages=full_messages,
        tools=TOOLS,
        max_tokens=400,
    )
    choice = response.choices[0]

    # Tool-call loop: same pattern as the CLI agent, just tracked for the UI
    while choice.finish_reason == "tool_calls":
        assistant_msg = choice.message
        full_messages.append(
            {
                "role": "assistant",
                "content": assistant_msg.content,
                "tool_calls": [tc.model_dump() for tc in assistant_msg.tool_calls],
            }
        )

        for tool_call in assistant_msg.tool_calls:
            args = json.loads(tool_call.function.arguments or "{}")
            result = run_tool(tool_call.function.name, args)

            tool_events.append(
                {"name": tool_call.function.name, "args": args, "result": result}
            )

            full_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                }
            )

        response = client.chat.completions.create(
            model=MODEL,
            messages=full_messages,
            tools=TOOLS,
            max_tokens=400,
        )
        choice = response.choices[0]

    reply = choice.message.content or ""
    return jsonify({"reply": reply, "tool_events": tool_events})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
