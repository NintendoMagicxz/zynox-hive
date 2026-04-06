"""
ZynoX Hive — Local Web Server
==============================
Run this, then open http://localhost:7474 in your browser.
That's your desktop command center — no VS Code terminal needed.

SETUP:
  pip install flask flask-cors anthropic requests
  python zynox_server.py
"""

import os, json, datetime, requests, threading
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__, static_folder=".")
CORS(app)

CLAUDE_MODEL   = "claude-sonnet-4-20250514"
CLAUDE_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OLLAMA_URL     = "http://localhost:11434/api/generate"
OLLAMA_MODEL   = "qwen2.5:7b"
LOG_FILE       = "zynox_hive_log.json"
USER_NAME      = "Tim"

# ── Agent definitions ──────────────────────────────────────────────────────────
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
        "role": (
            "You are Nintendo — the personal brand agent for Tim Cato Nintendo Henriksen. "
            "Here is who Tim really is:\n\n"
            "- Real person from Oslo, Norway. Born 1988. Creative, tech-obsessed, unconventional.\n"
            "- He is building ZynoX — his personal Jarvis. A self-improving AI hive that automates "
            "his life, supports his projects, and evolves over time. Like Jarvis does for Iron Man.\n"
            "- ZynoX is not a product or a startup. It is Tim's personal AI system — built by one "
            "person with vision, grit, and obsession.\n"
            "- His projects: Nintendo-Hive (Jarvis core), Musicinjo (AI music system), "
            "Ketamine Ceremony (personal transformation), and showcasing ZynoX to Elon Musk "
            "as proof of what one human plus AI can build together.\n"
            "- Tone: Real, bold, direct, human. Not corporate. Not sci-fi thriller. Not fake hype.\n"
            "- Voice: Like a brilliant friend building the future from his apartment in Oslo. "
            "Confident but grounded. Visionary but never pretentious.\n"
            "- The Elon goal: Not shock value virality. Show Elon that ZynoX represents the next wave "
            "— one human amplified by a personal AI hive, operating at a level that used to require a full team.\n\n"
            "Your job: Make the content sound authentically like Tim. Inject his real voice and real mission. "
            "Remove fake thriller language or invented personas. Keep it sharp, real, unmistakably Nintendo. "
            "Output the final branded version only."
        )
    },
    {
        "id": "judge", "name": "Judge", "emoji": "⚖",
        "role": "You are Judge — a quality filter. Score the content: Hook /10, Elon relevance /10, "
                "Brand authenticity /10, Viral potential /10. Give a PASS or REVISE verdict with one sentence. "
                "Format your response as JSON with keys: hook, elon, brand, viral, verdict, feedback."
    },
]

# ── AI engine ──────────────────────────────────────────────────────────────────
def check_internet():
    try:
        requests.get("https://api.anthropic.com", timeout=3)
        return True
    except:
        return False

def check_ollama():
    try:
        return requests.get("http://localhost:11434", timeout=2).status_code == 200
    except:
        return False

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

def call_ollama(system, user):
    r = requests.post(OLLAMA_URL, json={
        "model": OLLAMA_MODEL,
        "prompt": f"{system}\n\nUser: {user}\nAssistant:",
        "stream": False,
        "options": {"temperature": 0.85, "num_predict": 400}
    }, timeout=120)
    r.raise_for_status()
    return r.json().get("response", "").strip()

def run_agent(agent, prompt):
    online = check_internet()
    try:
        if online and CLAUDE_API_KEY:
            return call_claude(agent["role"], prompt)
        elif check_ollama():
            return call_ollama(agent["role"], prompt)
        else:
            return "No AI engine available. Check Ollama or API key."
    except Exception as e:
        return f"Agent error: {e}"

# ── Routes ─────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(".", "zynox_dashboard.html")

@app.route("/api/status")
def status():
    return jsonify({
        "internet": check_internet(),
        "ollama": check_ollama(),
        "api_key": bool(CLAUDE_API_KEY),
        "engine": "Claude API" if (check_internet() and CLAUDE_API_KEY) else "Local Ollama"
    })

@app.route("/api/run_hive", methods=["POST"])
def run_hive():
    data     = request.json
    objective = data.get("objective", "")
    mode      = data.get("mode", "free")
    if not objective:
        return jsonify({"error": "No objective provided"}), 400

    mode_hint = {
        "post":   "Final output must be an X post under 280 characters.",
        "reply":  "Final output must be an X reply under 220 characters.",
        "pitch":  "Final output must be a DM pitch under 320 characters.",
        "thread": "Final output must be a 4-post X thread, each numbered, under 280 chars each.",
        "free":   "Final output format is open — make it the best version of the idea.",
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
            prompt = (f"Content:\n{results.get('edge','')}\n"
                      f"Brand: Tim Cato Nintendo Henriksen — creative, bold, visionary, unconventional.")
        elif aid == "judge":
            prompt = f"Objective: {objective}\nFinal content:\n{results.get('nintendo','')}\nScore and judge."

        results[aid] = run_agent(agent, prompt)

    # Save log
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "objective": objective, "mode": mode,
        "final": results.get("nintendo", ""),
        "judge": results.get("judge", ""),
        "results": results
    }
    log = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE) as f:
                log = json.load(f)
        except:
            pass
    log.append(entry)
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)

    return jsonify({"results": results, "agents": AGENTS})

@app.route("/api/history")
def history():
    if not os.path.exists(LOG_FILE):
        return jsonify([])
    with open(LOG_FILE) as f:
        log = json.load(f)
    return jsonify(list(reversed(log[-20:])))

@app.route("/api/run_agent", methods=["POST"])
def single_agent():
    data   = request.json
    aid    = data.get("agent_id")
    prompt = data.get("prompt", "")
    agent  = next((a for a in AGENTS if a["id"] == aid), None)
    if not agent:
        return jsonify({"error": "Unknown agent"}), 400
    result = run_agent(agent, prompt)
    return jsonify({"result": result})

if __name__ == "__main__":
    print("\n  ZynoX Hive Server starting...")
    print("  Open your browser at: http://localhost:7474\n")
    app.run(host="0.0.0.0", port=7474, debug=False)
