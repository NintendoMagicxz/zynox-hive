"""
ZynoX Hive — Cloud Server (Railway Edition)
=============================================
Run locally:  python zynox_server.py
Deployed on:  Railway — reads PORT from environment automatically

ENVIRONMENT VARIABLES (set in Railway dashboard, never in code):
  ANTHROPIC_API_KEY   — your Claude API key
  ZYNOX_PASSWORD      — your login password
  ZAPIER_WEBHOOK_URL  — optional
  TELEGRAM_BOT_TOKEN  — optional
  TELEGRAM_CHAT_ID    — optional
"""

import os, json, datetime, requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder=".")
CORS(app)

# ── Config — all from environment, never hardcoded ─────────────────────────────
CLAUDE_MODEL   = "claude-sonnet-4-20250514"
CLAUDE_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ZYNOX_PASSWORD = os.getenv("ZYNOX_PASSWORD", "ZynoX123")
ZAPIER_URL     = os.getenv("ZAPIER_WEBHOOK_URL", "")
TG_TOKEN       = os.getenv("TELEGRAM_BOT_TOKEN", "")
TG_CHAT        = os.getenv("TELEGRAM_CHAT_ID", "")
PORT           = int(os.getenv("PORT", 7474))
LOG_FILE       = "zynox_log.json"

sessions = set()

# ── Agents ─────────────────────────────────────────────────────────────────────
AGENTS = [
    {
        "id": "scout", "name": "Scout", "emoji": "🔍",
        "role": "You are Scout — a research agent. Analyse the topic and identify the sharpest angle, "
                "the tension, the 'why now', and what Elon Musk would find genuinely interesting. "
                "Be concise. Output 3-4 bullet points max."
    },
    {
        "id": "strategist", "name": "Strategist", "emoji": "♟",
        "role": "You are Strategist — a mission logic agent. Given the topic and Scout's research, "
                "define the single best content strategy: format, emotional hook, and outcome. 3-4 bullets max."
    },
    {
        "id": "writer", "name": "Writer", "emoji": "✍",
        "role": "You are Writer — a content creation agent. Given the strategy, write the actual content. "
                "Crisp, bold, no filler. Respect character limits when given."
    },
    {
        "id": "edge", "name": "Edge", "emoji": "⚡",
        "role": "You are Edge — a sharpening agent. Take the draft and make it 30% bolder, more provocative, "
                "more memorable. Cut weak words. Raise the stakes. Keep format and character limit. Output improved version only."
    },
    {
        "id": "nintendo", "name": "Nintendo", "emoji": "🎮",
        "role": "You are Nintendo — the brand identity agent for Tim Cato Nintendo Henriksen. "
                "Inject Tim's personal voice: creative, bold, visionary, unconventional. "
                "Do not change the core message. Output the final branded version only."
    },
    {
        "id": "judge", "name": "Judge", "emoji": "⚖",
        "role": "You are Judge — a quality filter. Score the content: Hook /10, Elon relevance /10, "
                "Brand authenticity /10, Viral potential /10. Give a PASS or REVISE verdict with one sentence. "
                'Format your response as JSON: {"hook":8,"elon":9,"brand":8,"viral":7,"verdict":"PASS","feedback":"..."}'
    },
]

# ── Helpers ────────────────────────────────────────────────────────────────────
def make_token():
    import random
    return str(random.random()) + str(datetime.datetime.now().timestamp())

def call_claude(system, user):
    headers = {
        "x-api-key": CLAUDE_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    r = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json={
        "model": CLAUDE_MODEL, "max_tokens": 600,
        "system": system, "messages": [{"role": "user", "content": user}]
    }, timeout=30)
    r.raise_for_status()
    return r.json()["content"][0]["text"].strip()

def run_agent(agent, prompt):
    try:
        return call_claude(agent["role"], prompt)
    except Exception as e:
        return f"Agent error: {e}"

def log_to_file(entry):
    log = []
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE) as f:
                log = json.load(f)
    except Exception:
        pass
    log.append(entry)
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)

def send_telegram(text):
    if not TG_TOKEN or not TG_CHAT:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            json={"chat_id": TG_CHAT, "text": text, "parse_mode": "Markdown"},
            timeout=10
        )
    except Exception:
        pass

def send_zapier(data):
    if not ZAPIER_URL:
        return
    try:
        requests.post(ZAPIER_URL, json=data, timeout=10)
    except Exception:
        pass

# ── Routes ─────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(".", "zynox_dashboard.html")

@app.route("/api/status")
def status():
    return jsonify({
        "online": True,
        "api_key": bool(CLAUDE_API_KEY),
        "telegram": bool(TG_TOKEN and TG_CHAT),
        "zapier": bool(ZAPIER_URL),
        "engine": "Claude API" if CLAUDE_API_KEY else "No API key set",
        "version": "2.1-cloud"
    })

@app.route("/api/login", methods=["POST"])
def login():
    data = request.json or {}
    if data.get("password") == ZYNOX_PASSWORD:
        token = make_token()
        sessions.add(token)
        return jsonify({"ok": True, "token": token})
    return jsonify({"ok": False, "error": "Wrong password"}), 401

@app.route("/api/run_hive", methods=["POST"])
def run_hive():
    token = request.headers.get("x-session-token", "")
    if token not in sessions:
        return jsonify({"error": "Not authenticated"}), 401

    data      = request.json or {}
    objective = data.get("objective", "")
    mode      = data.get("mode", "free")
    if not objective:
        return jsonify({"error": "No objective provided"}), 400

    mode_hint = {
        "post":   "Final output must be an X post under 280 characters.",
        "reply":  "Final output must be an X reply under 220 characters.",
        "pitch":  "Final output must be a DM pitch under 320 characters.",
        "thread": "Final output must be a 4-post X thread, each numbered, under 280 chars each.",
        "free":   "Final output format is open.",
    }.get(mode, "")

    results = {}
    for agent in AGENTS:
        aid = agent["id"]
        if aid == "scout":
            prompt = f"Topic: {objective}\nFormat: {mode_hint}\nAnalyse and give your research."
        elif aid == "strategist":
            prompt = f"Topic: {objective}\nScout:\n{results.get('scout','')}\nBuild the strategy."
        elif aid == "writer":
            prompt = f"Topic: {objective}\nStrategy:\n{results.get('strategist','')}\n{mode_hint}\nWrite it."
        elif aid == "edge":
            prompt = f"Draft:\n{results.get('writer','')}\n{mode_hint}\nMake it bolder."
        elif aid == "nintendo":
            prompt = f"Content:\n{results.get('edge','')}\nBrand: Tim Cato Nintendo Henriksen — creative, bold, visionary, unconventional."
        elif aid == "judge":
            prompt = f"Objective: {objective}\nFinal content:\n{results.get('nintendo','')}\nScore and judge. JSON only."
        results[aid] = run_agent(agent, prompt)

    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "objective": objective, "mode": mode,
        "final": results.get("nintendo", ""),
        "judge": results.get("judge", ""),
        "results": results
    }
    log_to_file(entry)
    send_telegram(f"*ZynoX Hive complete*\n\n*Objective:* {objective}\n\n{results.get('nintendo','')}")
    send_zapier({"timestamp": entry["timestamp"], "objective": objective, "mode": mode, "final": results.get("nintendo","")})

    return jsonify({"results": results, "agents": AGENTS})

@app.route("/api/history")
def history():
    try:
        with open(LOG_FILE) as f:
            log = json.load(f)
        return jsonify(list(reversed(log[-20:])))
    except Exception:
        return jsonify([])

@app.route("/api/run_agent", methods=["POST"])
def single_agent():
    token = request.headers.get("x-session-token", "")
    if token not in sessions:
        return jsonify({"error": "Not authenticated"}), 401
    data   = request.json or {}
    aid    = data.get("agent_id")
    prompt = data.get("prompt", "")
    agent  = next((a for a in AGENTS if a["id"] == aid), None)
    if not agent:
        return jsonify({"error": "Unknown agent"}), 400
    return jsonify({"result": run_agent(agent, prompt)})

# ── Boot ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"\n  ZynoX Hive Cloud Server")
    print(f"  API Key: {'OK' if CLAUDE_API_KEY else 'MISSING'}")
    print(f"  Telegram: {'OK' if TG_TOKEN else 'not set'}")
    print(f"  Zapier: {'OK' if ZAPIER_URL else 'not set'}")
    print(f"  Port: {PORT}\n")
    app.run(host="0.0.0.0", port=PORT, debug=False)
