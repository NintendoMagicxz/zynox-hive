"""
ZynoX Agent — Local PC Edition
================================
Your personal Jarvis running 24/7 on your machine.
Works ONLINE (Claude API) and OFFLINE (local Ollama model).

SETUP:
1. Install Ollama: https://ollama.com
2. Run: ollama pull qwen2.5:7b
3. pip install anthropic requests
4. python zynox_agent.py
"""

import os
import sys
import json
import datetime
import requests

# ── Config ────────────────────────────────────────────────────────────────────
AGENT_NAME     = "ZynoX"
USER_NAME      = "Tim"
MISSION        = "Get Elon Musk's attention and land a collaboration"
OLLAMA_URL     = "http://localhost:11434/api/generate"
OLLAMA_MODEL   = "qwen2.5:7b"          # change to any model you have pulled
CLAUDE_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
LOG_FILE       = "zynox_log.json"

# ── Colours for terminal ───────────────────────────────────────────────────────
PURPLE = "\033[95m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

# ── Helpers ────────────────────────────────────────────────────────────────────

def banner():
    print(f"""
{PURPLE}{BOLD}
  ███████╗██╗   ██╗███╗   ██╗ ██████╗ ██╗  ██╗
  ╚══███╔╝╚██╗ ██╔╝████╗  ██║██╔═══██╗╚██╗██╔╝
    ███╔╝  ╚████╔╝ ██╔██╗ ██║██║   ██║ ╚███╔╝
   ███╔╝    ╚██╔╝  ██║╚██╗██║██║   ██║ ██╔██╗
  ███████╗   ██║   ██║ ╚████║╚██████╔╝██╔╝ ██╗
  ╚══════╝   ╚═╝   ╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝
{RESET}
  {CYAN}Jarvis Mode — Local PC Edition{RESET}
  {YELLOW}Mission: {MISSION}{RESET}
  Ready for your command, {USER_NAME}.
""")

def check_internet() -> bool:
    try:
        requests.get("https://api.anthropic.com", timeout=3)
        return True
    except Exception:
        return False

def check_ollama() -> bool:
    try:
        r = requests.get("http://localhost:11434", timeout=2)
        return r.status_code == 200
    except Exception:
        return False

def status_line(online: bool, ollama: bool):
    net   = f"{GREEN}Online{RESET}"    if online  else f"{YELLOW}Offline{RESET}"
    local = f"{GREEN}Running{RESET}"   if ollama  else f"{YELLOW}Not found{RESET}"
    mode  = f"{GREEN}Claude API{RESET}" if online else f"{YELLOW}Local (Ollama){RESET}"
    print(f"  Internet: {net}   Ollama: {local}   Mode: {mode}\n")

# ── AI Calls ───────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = f"""You are {AGENT_NAME} — an elite AI agent working for {USER_NAME}, a creative/media professional.
Mission: {MISSION}.
You think like Jarvis: fast, precise, no fluff. You understand Elon's world (xAI, Tesla, SpaceX, X platform).
Keep outputs sharp and under the character limits requested."""

def call_claude(prompt: str) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=800,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )
    return msg.content[0].text.strip()

def call_ollama(prompt: str) -> str:
    full_prompt = f"{SYSTEM_PROMPT}\n\nUser: {prompt}\nAssistant:"
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": full_prompt,
        "stream": False,
        "options": {"temperature": 0.85, "num_predict": 400}
    }
    r = requests.post(OLLAMA_URL, json=payload, timeout=120)
    r.raise_for_status()
    return r.json().get("response", "").strip()

def generate(prompt: str, online: bool) -> str:
    try:
        if online and CLAUDE_API_KEY:
            return call_claude(prompt)
        elif check_ollama():
            print(f"  {YELLOW}[Offline mode — using local Ollama]{RESET}")
            return call_ollama(prompt)
        else:
            return "[ERROR] No AI available. Start Ollama: run 'ollama serve' in a terminal.]"
    except Exception as e:
        return f"[ERROR] {e}"

# ── Logging ────────────────────────────────────────────────────────────────────

def log_entry(mode: str, topic: str, output: str):
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "mode": mode,
        "topic": topic,
        "output": output
    }
    log = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE) as f:
            try:
                log = json.load(f)
            except Exception:
                log = []
    log.append(entry)
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)

def show_log():
    if not os.path.exists(LOG_FILE):
        print("  No history yet.")
        return
    with open(LOG_FILE) as f:
        log = json.load(f)
    last = log[-5:]
    for e in reversed(last):
        ts = e["timestamp"][:16].replace("T", " ")
        print(f"  {CYAN}[{ts}]{RESET} {e['mode'].upper()} — {e['topic'][:60]}")
        print(f"  {e['output'][:120]}...\n")

# ── Prompts per mode ───────────────────────────────────────────────────────────

MODE_PROMPTS = {
    "1": ("X post",
          lambda t: f"Write a single X post (under 280 chars) for {USER_NAME} about: '{t}'. "
                    f"Bold, thought-provoking, relevant to Elon's mission. No hashtags. Output post only."),
    "2": ("Reply to Elon",
          lambda t: f"Write a reply (under 220 chars) to an Elon Musk post about: '{t}'. "
                    f"Add genuine insight. Confident, never sycophantic. Output reply only."),
    "3": ("Collab pitch",
          lambda t: f"Write a DM pitch (under 320 chars) to Elon's team about: '{t}'. "
                    f"Lead with value to his mission. End with a clear next step. Output pitch only."),
    "4": ("Thread",
          lambda t: f"Write a 4-post X thread for {USER_NAME} about: '{t}'. "
                    f"Number them 1/ 2/ 3/ 4/. Each under 280 chars. Bold opener, build tension, "
                    f"end with a call to think. Output thread only."),
    "5": ("Morning brief",
          lambda t: f"Give {USER_NAME} a sharp 3-bullet morning brief on what's happening in Elon's world "
                    f"related to: '{t}'. Each bullet: one sentence, one angle for content. Output bullets only."),
}

# ── Main Loop ──────────────────────────────────────────────────────────────────

def main():
    banner()
    online = check_internet()
    status_line(online, check_ollama())

    while True:
        print(f"{PURPLE}{'─'*50}{RESET}")
        print(f"  {BOLD}What's the mission, {USER_NAME}?{RESET}\n")
        print("  1 — Write an X post")
        print("  2 — Write a reply to Elon")
        print("  3 — Write a collab pitch")
        print("  4 — Write a thread")
        print("  5 — Morning brief")
        print("  6 — Show recent history")
        print("  7 — Check connection status")
        print("  0 — Exit")
        print()

        choice = input("  > ").strip()

        if choice == "0":
            print(f"\n  {CYAN}ZynoX standing down. See you tomorrow, {USER_NAME}.{RESET}\n")
            break

        elif choice == "6":
            show_log()
            continue

        elif choice == "7":
            online = check_internet()
            status_line(online, check_ollama())
            continue

        elif choice in MODE_PROMPTS:
            label, prompt_fn = MODE_PROMPTS[choice]
            topic = input(f"\n  Topic / angle for {label}:\n  > ").strip()
            if not topic:
                print("  No topic given. Try again.")
                continue

            print(f"\n  {CYAN}ZynoX working on it...{RESET}\n")
            result = generate(prompt_fn(topic), online)

            print(f"{GREEN}{'─'*50}{RESET}")
            print(f"  {BOLD}{label.upper()}{RESET}")
            print(f"{GREEN}{'─'*50}{RESET}")
            print(f"\n{result}\n")
            print(f"{GREEN}{'─'*50}{RESET}")
            print(f"  Characters: {len(result)}")

            log_entry(label, topic, result)

            action = input("\n  [c] Copy to clipboard   [enter] Continue\n  > ").strip().lower()
            if action == "c":
                try:
                    import subprocess
                    subprocess.run(["clip"], input=result.encode(), check=True)
                    print(f"  {GREEN}Copied to clipboard.{RESET}")
                except Exception:
                    print("  (Auto-copy not available — select and copy manually.)")

        else:
            print("  Unknown command. Pick 0–7.")

if __name__ == "__main__":
    main()
