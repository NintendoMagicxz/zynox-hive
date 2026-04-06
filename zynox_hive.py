"""
ZynoX Agent Hive — Local Multi-Agent System
=============================================
A swarm of specialist AI agents that collaborate to sharpen
any idea into peak ZynoX / Nintendo Henriksen output.

AGENTS IN THE HIVE:
  1. Scout     — researches the topic & finds the angle
  2. Strategist — builds the mission logic
  3. Writer    — drafts the raw content
  4. Edge      — makes it bolder, more ZynoX
  5. Nintendo  — adds Tim's personal brand flavour
  6. Judge     — scores and filters. Only the best passes.

SETUP:
  pip install anthropic requests
  ollama pull qwen2.5:7b   (for offline fallback)
  python zynox_hive.py
"""

import os, json, datetime, requests, time

# ── Config ─────────────────────────────────────────────────────────────────────
CLAUDE_MODEL   = "claude-sonnet-4-20250514"
CLAUDE_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OLLAMA_URL     = "http://localhost:11434/api/generate"
OLLAMA_MODEL   = "qwen2.5:7b"
LOG_FILE       = "zynox_hive_log.json"
USER_NAME      = "Tim"
BRAND          = "ZynoX / Nintendo Henriksen"

# ── Terminal colours ────────────────────────────────────────────────────────────
R="\033[0m"; BOLD="\033[1m"
PU="\033[95m"; CY="\033[96m"; GR="\033[92m"; YE="\033[93m"; RE="\033[91m"; BL="\033[94m"

# ── Agent definitions ──────────────────────────────────────────────────────────
AGENTS = [
    {
        "id": "scout",
        "name": "Scout",
        "color": BL,
        "role": "You are Scout — a research agent. Your job is to analyse a topic and identify "
                "the sharpest angle, the tension, the 'why now', and what Elon Musk would find "
                "genuinely interesting about it. Be concise. Output 3-4 bullet points max."
    },
    {
        "id": "strategist",
        "name": "Strategist",
        "color": CY,
        "role": "You are Strategist — a mission logic agent. Given a topic and Scout's research, "
                "define the single best content strategy: what format (post/reply/thread/pitch), "
                "what emotional hook, and what outcome it drives. 3-4 bullets max."
    },
    {
        "id": "writer",
        "name": "Writer",
        "color": GR,
        "role": "You are Writer — a content creation agent. Given the strategy, write the actual "
                "content piece. Crisp, bold, no filler. Respect character limits when given."
    },
    {
        "id": "edge",
        "name": "Edge",
        "color": YE,
        "role": "You are Edge — a sharpening agent. Take the Writer's draft and make it 30% bolder, "
                "more provocative, more memorable. Cut weak words. Raise the stakes. Keep the same "
                "format and character limit. Output the improved version only."
    },
    {
        "id": "nintendo",
        "name": "Nintendo",
        "color": PU,
        "role": f"You are Nintendo — the brand identity agent for {USER_NAME} (Tim Cato Nintendo Henriksen). "
                f"Your job is to inject Tim's personal voice and brand ({BRAND}) into the content. "
                f"Make it feel authentically Tim — creative, bold, visionary, unconventional. "
                f"Do not change the core message. Output the final branded version only."
    },
    {
        "id": "judge",
        "name": "Judge",
        "color": RE,
        "role": "You are Judge — a quality filter agent. Score the final content on: "
                "(1) Hook strength /10, (2) Elon relevance /10, (3) Brand authenticity /10, "
                "(4) Viral potential /10. Then give an overall PASS or REVISE verdict with one "
                "sentence of feedback. Format: scores as JSON, then verdict on a new line."
    },
]

# ── AI engine ──────────────────────────────────────────────────────────────────

def check_internet():
    try:
        requests.get("https://api.anthropic.com", timeout=3)
        return True
    except Exception:
        return False

def check_ollama():
    try:
        return requests.get("http://localhost:11434", timeout=2).status_code == 200
    except Exception:
        return False

def call_claude(system: str, user: str) -> str:
    headers = {
        "x-api-key": CLAUDE_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    payload = {
        "model": CLAUDE_MODEL,
        "max_tokens": 600,
        "system": system,
        "messages": [{"role": "user", "content": user}]
    }
    r = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data["content"][0]["text"].strip()

def call_ollama(system: str, user: str) -> str:
    prompt = f"{system}\n\nUser: {user}\nAssistant:"
    r = requests.post(OLLAMA_URL, json={
        "model": OLLAMA_MODEL, "prompt": prompt,
        "stream": False, "options": {"temperature": 0.85, "num_predict": 400}
    }, timeout=120)
    r.raise_for_status()
    return r.json().get("response", "").strip()

def run_agent(agent: dict, user_message: str, online: bool) -> str:
    try:
        if online and CLAUDE_API_KEY:
            return call_claude(agent["role"], user_message)
        elif check_ollama():
            return call_ollama(agent["role"], user_message)
        else:
            return "[No AI available — start Ollama or add API key]"
    except Exception as e:
        return f"[Agent error: {e}]"

# ── Hive orchestrator ──────────────────────────────────────────────────────────

def run_hive(objective: str, mode: str, online: bool) -> dict:
    """
    Runs all agents in sequence, passing each output to the next.
    Returns a dict with every agent's output.
    """
    results = {}
    context = f"Objective: {objective}\nMode: {mode}"

    mode_instruction = {
        "post":   "Final output must be an X post under 280 characters.",
        "reply":  "Final output must be an X reply under 220 characters.",
        "pitch":  "Final output must be a DM pitch under 320 characters.",
        "thread": "Final output must be a 4-post X thread, each post numbered and under 280 chars.",
        "free":   "Final output format is open — make it the best version of the idea.",
    }.get(mode, "Final output format is open.")

    for i, agent in enumerate(AGENTS):
        color = agent["color"]
        name  = agent["name"]

        print(f"  {color}{BOLD}[{name}]{R} thinking", end="", flush=True)

        # Build the prompt for this agent
        if agent["id"] == "scout":
            prompt = f"Topic: {objective}\nFormat hint: {mode_instruction}\nAnalyse this and give your research."
        elif agent["id"] == "strategist":
            prompt = f"Topic: {objective}\nScout's research:\n{results.get('scout','')}\nBuild the strategy."
        elif agent["id"] == "writer":
            prompt = (f"Topic: {objective}\nStrategy:\n{results.get('strategist','')}\n"
                      f"{mode_instruction}\nWrite the content.")
        elif agent["id"] == "edge":
            prompt = f"Draft to sharpen:\n{results.get('writer','')}\n{mode_instruction}\nMake it bolder."
        elif agent["id"] == "nintendo":
            prompt = (f"Content to brand:\n{results.get('edge','')}\n"
                      f"Brand context: Tim Cato Nintendo Henriksen — creative/media visionary, "
                      f"bold, unconventional. Inject his voice.")
        elif agent["id"] == "judge":
            prompt = (f"Original objective: {objective}\n"
                      f"Final content:\n{results.get('nintendo','')}\nScore and judge this.")

        # Animate dots while waiting
        output = run_agent(agent, prompt, online)
        print(f"\r  {color}{BOLD}[{name}]{R} done          ")
        results[agent["id"]] = output
        time.sleep(0.2)

    return results

# ── Display ────────────────────────────────────────────────────────────────────

def display_hive_results(results: dict, objective: str, mode: str):
    agent_map = {a["id"]: a for a in AGENTS}
    print(f"\n{PU}{'═'*56}{R}")
    print(f"  {BOLD}HIVE COMPLETE — {mode.upper()} | {objective[:40]}{R}")
    print(f"{PU}{'═'*56}{R}\n")

    stages = ["scout", "strategist", "writer", "edge", "nintendo"]
    labels = {
        "scout":      "Research & angle",
        "strategist": "Strategy",
        "writer":     "First draft",
        "edge":       "Sharpened",
        "nintendo":   "Nintendo-branded (FINAL)",
    }
    for key in stages:
        color = agent_map[key]["color"]
        print(f"  {color}{BOLD}{labels[key]}{R}")
        print(f"  {results.get(key, '')}\n")

    print(f"{RE}{'─'*56}{R}")
    print(f"  {BOLD}[Judge] Quality verdict{R}")
    print(f"  {results.get('judge', '')}")
    print(f"{RE}{'─'*56}{R}\n")

def log_hive(objective: str, mode: str, results: dict):
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "objective": objective,
        "mode": mode,
        "final": results.get("nintendo", ""),
        "judge": results.get("judge", ""),
    }
    log = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE) as f:
                log = json.load(f)
        except Exception:
            pass
    log.append(entry)
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)

def show_history():
    if not os.path.exists(LOG_FILE):
        print("  No hive runs logged yet.\n")
        return
    with open(LOG_FILE) as f:
        log = json.load(f)
    for e in reversed(log[-5:]):
        ts = e["timestamp"][:16].replace("T", " ")
        print(f"  {CY}[{ts}]{R}  {e['mode'].upper()} — {e['objective'][:50]}")
        print(f"  {e['final'][:120]}")
        print(f"  {YE}{e['judge'][:80]}{R}\n")

def export_final(results: dict, objective: str):
    fname = f"zynox_output_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(fname, "w") as f:
        f.write(f"ZynoX Hive Output\n{'='*40}\n")
        f.write(f"Objective: {objective}\n\n")
        f.write(f"FINAL (Nintendo-branded):\n{results.get('nintendo','')}\n\n")
        f.write(f"Judge verdict:\n{results.get('judge','')}\n")
    print(f"  {GR}Saved to {fname}{R}\n")

# ── Banner ─────────────────────────────────────────────────────────────────────

def banner():
    print(f"""
{PU}{BOLD}
  ╔══════════════════════════════════════════╗
  ║       ZynoX  A G E N T  H I V E         ║
  ║   Mass agents — one refined output       ║
  ╚══════════════════════════════════════════╝
{R}
  Agents: {BL}Scout{R} → {CY}Strategist{R} → {GR}Writer{R} → {YE}Edge{R} → {PU}Nintendo{R} → {RE}Judge{R}
""")

# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    banner()
    online = check_internet()
    ollama = check_ollama()
    net_s  = f"{GR}Online{R}" if online else f"{YE}Offline{R}"
    loc_s  = f"{GR}Ready{R}"  if ollama else f"{YE}Not running{R}"
    mode_s = f"{GR}Claude API{R}" if (online and CLAUDE_API_KEY) else f"{YE}Local Ollama{R}"
    print(f"  Internet: {net_s}   Ollama: {loc_s}   Engine: {mode_s}\n")

    while True:
        print(f"{PU}{'─'*50}{R}")
        print(f"  {BOLD}ZynoX Hive — Command{R}\n")
        print(f"  1 — Run full hive on a new objective")
        print(f"  2 — View recent hive outputs")
        print(f"  3 — Check system status")
        print(f"  0 — Shut down hive")
        print()

        cmd = input("  > ").strip()

        if cmd == "0":
            print(f"\n  {CY}ZynoX Hive offline. Good work, {USER_NAME}.{R}\n")
            break

        elif cmd == "2":
            show_history()

        elif cmd == "3":
            online = check_internet()
            ollama = check_ollama()
            print(f"  Internet: {'Online' if online else 'Offline'}  |  Ollama: {'Ready' if ollama else 'Not running'}\n")

        elif cmd == "1":
            print(f"\n  What's the objective, {USER_NAME}?")
            print(f"  {CY}(e.g. 'I want to pitch SpaceX a documentary' or 'Go viral on AI and creativity'){R}")
            objective = input("  > ").strip()
            if not objective:
                print("  No objective. Try again.\n")
                continue

            print(f"\n  Output mode: [1] X post  [2] Reply  [3] Pitch  [4] Thread  [5] Free form")
            mode_map = {"1":"post","2":"reply","3":"pitch","4":"thread","5":"free"}
            mc = input("  > ").strip()
            mode = mode_map.get(mc, "free")

            print(f"\n  {PU}{BOLD}Deploying hive...{R}\n")
            results = run_hive(objective, mode, online)
            display_hive_results(results, objective, mode)
            log_hive(objective, mode, results)

            action = input("  [e] Export to file   [enter] Continue\n  > ").strip().lower()
            if action == "e":
                export_final(results, objective)

        else:
            print("  Unknown command.\n")

if __name__ == "__main__":
    main()
