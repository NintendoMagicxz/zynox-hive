"""
╔══════════════════════════════════════════════════════════════════════╗
║                         M U S I C I N J O                           ║
║              ZynBoX · AI Song Data Agent · ZynoX System             ║
║         "I remember everything so the music never forgets."         ║
╚══════════════════════════════════════════════════════════════════════╝

Musicinjo is the memory and intelligence core of ZynBoX.
He collects, stores, tags, and retrieves all creative data —
lyrics, Suno prompts, Hive System notes, moods, song DNA —
so every future song is built on a living archive of past genius.

Author : ZynoX / ZynBoX Creative System
Agent  : Musicinjo v1.0
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional


# ── Config ────────────────────────────────────────────────────────────
MUSICINJO_DIR = Path.home() / ".musicinjo"
SONGS_DB      = MUSICINJO_DIR / "songs.json"
PROMPTS_DB    = MUSICINJO_DIR / "prompts.json"
HIVE_DB       = MUSICINJO_DIR / "hive_notes.json"
MOODS_DB      = MUSICINJO_DIR / "moods.json"
LOG_FILE      = MUSICINJO_DIR / "musicinjo.log"

BANNER = """
╔══════════════════════════════════════════════════════════╗
║  🎵  M U S I C I N J O  — ZynBoX Song Memory Agent     ║
║      I remember everything so the music never forgets.  ║
╚══════════════════════════════════════════════════════════╝
"""


# ── Utilities ─────────────────────────────────────────────────────────

def _ensure_dirs():
    MUSICINJO_DIR.mkdir(parents=True, exist_ok=True)
    for db in [SONGS_DB, PROMPTS_DB, HIVE_DB, MOODS_DB]:
        if not db.exists():
            db.write_text("[]", encoding="utf-8")


def _load(path: Path) -> list:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def _save(path: Path, data: list):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {msg}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry)
    print(f"  ♪ {msg}")


def _new_id() -> str:
    return str(uuid.uuid4())[:8].upper()


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _separator(char="─", width=58):
    print(char * width)


# ── Core Agent: Musicinjo ─────────────────────────────────────────────

class Musicinjo:
    """
    Musicinjo — ZynBoX AI Song Data Agent.

    Responsibilities:
      · Save and retrieve song DNA (title, lyrics, genre, mood, BPM)
      · Store Suno prompts with version history
      · Log Hive System refinement notes per song
      · Tag and search songs by mood, genre, vibe, or keyword
      · Export song packages for Suno generation sessions
    """

    def __init__(self):
        _ensure_dirs()
        print(BANNER)
        _log("Musicinjo is awake. Ready to remember your music.")

    # ── Song Management ───────────────────────────────────────────────

    def save_song(
        self,
        title: str,
        lyrics: str,
        genre: str,
        mood: str,
        bpm: Optional[int] = None,
        vibe_tags: Optional[list] = None,
        influences: Optional[list] = None,
        theme: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> dict:
        """
        Save a new song to the Musicinjo archive.

        Args:
            title       : Song title
            lyrics      : Full lyrics text
            genre       : Primary genre (e.g. "Dub Pop", "Techno")
            mood        : Emotional mood (e.g. "euphoric", "dreamy")
            bpm         : Target BPM
            vibe_tags   : List of vibe keywords (e.g. ["Oslo", "fjord", "magic"])
            influences  : List of artist influences (e.g. ["Bob Marley"])
            theme       : Lyrical theme / concept
            notes       : Any extra creative notes
        """
        songs = _load(SONGS_DB)
        song_id = _new_id()

        song = {
            "id": song_id,
            "title": title,
            "genre": genre,
            "mood": mood,
            "bpm": bpm,
            "vibe_tags": vibe_tags or [],
            "influences": influences or [],
            "theme": theme or "",
            "lyrics": lyrics,
            "notes": notes or "",
            "created_at": _now(),
            "updated_at": _now(),
            "version": 1,
            "suno_prompt_ids": [],
            "hive_note_ids": [],
        }

        songs.append(song)
        _save(SONGS_DB, songs)
        _log(f"Song saved → [{song_id}] '{title}' | {genre} | {mood}")
        return song

    def update_song(self, song_id: str, **kwargs) -> Optional[dict]:
        """Update fields on an existing song by ID."""
        songs = _load(SONGS_DB)
        for song in songs:
            if song["id"] == song_id:
                for key, value in kwargs.items():
                    if key in song:
                        song[key] = value
                song["updated_at"] = _now()
                song["version"] += 1
                _save(SONGS_DB, songs)
                _log(f"Song updated → [{song_id}] '{song['title']}' v{song['version']}")
                return song
        _log(f"Song not found: {song_id}")
        return None

    def get_song(self, song_id: str) -> Optional[dict]:
        """Retrieve a song by its ID."""
        for song in _load(SONGS_DB):
            if song["id"] == song_id:
                return song
        return None

    def list_songs(self, limit: int = 20) -> list:
        """List all stored songs, newest first."""
        songs = _load(SONGS_DB)
        return sorted(songs, key=lambda s: s["created_at"], reverse=True)[:limit]

    def search_songs(self, keyword: str) -> list:
        """
        Search songs by keyword across title, genre, mood,
        vibe_tags, influences, theme, and lyrics.
        """
        keyword = keyword.lower()
        results = []
        for song in _load(SONGS_DB):
            searchable = " ".join([
                song.get("title", ""),
                song.get("genre", ""),
                song.get("mood", ""),
                song.get("theme", ""),
                song.get("lyrics", ""),
                " ".join(song.get("vibe_tags", [])),
                " ".join(song.get("influences", [])),
            ]).lower()
            if keyword in searchable:
                results.append(song)
        _log(f"Search '{keyword}' → {len(results)} result(s)")
        return results

    # ── Suno Prompt Management ────────────────────────────────────────

    def save_suno_prompt(
        self,
        song_id: str,
        prompt_text: str,
        version_label: str = "",
        energy_level: str = "medium",
    ) -> Optional[dict]:
        """
        Save a Suno style prompt and link it to a song.

        Args:
            song_id       : The song this prompt belongs to
            prompt_text   : Full Suno style prompt string
            version_label : Human label (e.g. "v1 original", "v2 more dub")
            energy_level  : low / medium / high / euphoric
        """
        prompts = _load(PROMPTS_DB)
        songs   = _load(SONGS_DB)

        prompt_id = _new_id()
        prompt = {
            "id": prompt_id,
            "song_id": song_id,
            "prompt_text": prompt_text,
            "version_label": version_label or f"v{len(prompts)+1}",
            "energy_level": energy_level,
            "created_at": _now(),
        }
        prompts.append(prompt)
        _save(PROMPTS_DB, prompts)

        # Link to song
        for song in songs:
            if song["id"] == song_id:
                song["suno_prompt_ids"].append(prompt_id)
                song["updated_at"] = _now()
                break
        _save(SONGS_DB, songs)

        _log(f"Suno prompt saved → [{prompt_id}] for song [{song_id}] | {energy_level} energy")
        return prompt

    def get_prompts_for_song(self, song_id: str) -> list:
        """Get all Suno prompts linked to a song."""
        return [p for p in _load(PROMPTS_DB) if p["song_id"] == song_id]

    # ── Hive System Notes ─────────────────────────────────────────────

    def save_hive_note(
        self,
        song_id: str,
        category: str,
        note: str,
        priority: str = "medium",
    ) -> Optional[dict]:
        """
        Save a Hive System refinement note for a song.

        Args:
            song_id   : Target song ID
            category  : e.g. "bass", "guitar", "drop", "feel", "vocals"
            note      : The actual refinement instruction
            priority  : low / medium / high / critical
        """
        hive_notes = _load(HIVE_DB)
        songs      = _load(SONGS_DB)

        note_id = _new_id()
        hive_note = {
            "id": note_id,
            "song_id": song_id,
            "category": category,
            "note": note,
            "priority": priority,
            "created_at": _now(),
            "resolved": False,
        }
        hive_notes.append(hive_note)
        _save(HIVE_DB, hive_notes)

        # Link to song
        for song in songs:
            if song["id"] == song_id:
                song["hive_note_ids"].append(note_id)
                song["updated_at"] = _now()
                break
        _save(SONGS_DB, songs)

        _log(f"Hive note saved → [{note_id}] [{category}] priority:{priority} for song [{song_id}]")
        return hive_note

    def resolve_hive_note(self, note_id: str) -> bool:
        """Mark a Hive System note as resolved."""
        notes = _load(HIVE_DB)
        for note in notes:
            if note["id"] == note_id:
                note["resolved"] = True
                _save(HIVE_DB, notes)
                _log(f"Hive note resolved → [{note_id}]")
                return True
        return False

    def get_hive_notes_for_song(self, song_id: str, unresolved_only: bool = False) -> list:
        """Get Hive System notes for a song."""
        notes = [n for n in _load(HIVE_DB) if n["song_id"] == song_id]
        if unresolved_only:
            notes = [n for n in notes if not n["resolved"]]
        return notes

    # ── Mood Intelligence ─────────────────────────────────────────────

    def save_mood_profile(
        self,
        name: str,
        keywords: list,
        suno_tags: list,
        color: str = "",
        description: str = "",
    ) -> dict:
        """
        Save a reusable mood profile for future song generation.

        A mood profile is a named bundle of creative energy that can
        be applied across many songs — Musicinjo remembers them all.
        """
        moods = _load(MOODS_DB)
        mood_id = _new_id()
        mood = {
            "id": mood_id,
            "name": name,
            "keywords": keywords,
            "suno_tags": suno_tags,
            "color": color,
            "description": description,
            "created_at": _now(),
        }
        moods.append(mood)
        _save(MOODS_DB, moods)
        _log(f"Mood profile saved → [{mood_id}] '{name}'")
        return mood

    def list_moods(self) -> list:
        return _load(MOODS_DB)

    def find_mood(self, name: str) -> Optional[dict]:
        """Find a mood profile by name (case-insensitive)."""
        for mood in _load(MOODS_DB):
            if mood["name"].lower() == name.lower():
                return mood
        return None

    # ── Export: Song Package ──────────────────────────────────────────

    def export_song_package(self, song_id: str, output_path: Optional[str] = None) -> str:
        """
        Export a complete song package as a JSON file.

        Includes: song data, all Suno prompts, all Hive notes.
        Perfect for sharing a full creative brief.
        """
        song = self.get_song(song_id)
        if not song:
            _log(f"Export failed — song not found: {song_id}")
            return ""

        package = {
            "musicinjo_export": True,
            "exported_at": _now(),
            "song": song,
            "suno_prompts": self.get_prompts_for_song(song_id),
            "hive_notes": self.get_hive_notes_for_song(song_id),
        }

        out = output_path or str(MUSICINJO_DIR / f"export_{song_id}_{_now()[:10]}.json")
        Path(out).write_text(json.dumps(package, indent=2, ensure_ascii=False), encoding="utf-8")
        _log(f"Song package exported → {out}")
        return out

    # ── Display Helpers ───────────────────────────────────────────────

    def display_song(self, song: dict):
        """Pretty-print a song record to the terminal."""
        _separator("═")
        print(f"  🎵  {song['title']}  [{song['id']}]  v{song['version']}")
        _separator()
        print(f"  Genre      : {song['genre']}")
        print(f"  Mood       : {song['mood']}")
        print(f"  BPM        : {song.get('bpm') or '—'}")
        print(f"  Theme      : {song.get('theme') or '—'}")
        print(f"  Influences : {', '.join(song['influences']) or '—'}")
        print(f"  Vibe tags  : {', '.join(song['vibe_tags']) or '—'}")
        print(f"  Created    : {song['created_at']}")
        print(f"  Updated    : {song['updated_at']}")
        _separator()
        print("  LYRICS:")
        print()
        for line in song["lyrics"].splitlines():
            print(f"    {line}")
        if song.get("notes"):
            print()
            print(f"  Notes: {song['notes']}")
        _separator("═")

    def display_all_songs(self):
        """Print a summary table of all stored songs."""
        songs = self.list_songs()
        if not songs:
            print("  ♪ No songs in the archive yet. Time to create!")
            return
        _separator("═")
        print(f"  🎵  Musicinjo Archive — {len(songs)} song(s)")
        _separator()
        print(f"  {'ID':<10} {'Title':<28} {'Genre':<18} {'Mood':<14} {'BPM'}")
        _separator()
        for s in songs:
            bpm = str(s.get("bpm") or "—")
            print(f"  {s['id']:<10} {s['title'][:27]:<28} {s['genre'][:17]:<18} {s['mood'][:13]:<14} {bpm}")
        _separator("═")

    def display_hive_notes(self, song_id: str):
        """Display Hive System notes for a song."""
        notes = self.get_hive_notes_for_song(song_id)
        song  = self.get_song(song_id)
        name  = song["title"] if song else song_id
        _separator("═")
        print(f"  🐝  Hive Notes for '{name}' — {len(notes)} note(s)")
        _separator()
        priority_icons = {"low": "○", "medium": "◑", "high": "●", "critical": "🔴"}
        for n in notes:
            icon    = priority_icons.get(n["priority"], "○")
            resolved = "✓" if n["resolved"] else " "
            print(f"  [{resolved}] {icon} [{n['category'].upper():<10}] {n['note']}")
        _separator("═")


# ── Demo: First Run ───────────────────────────────────────────────────

def demo():
    """
    Musicinjo demo — seeds the archive with the Oslo Magic song
    from the ZynBoX session, including Suno prompts and Hive notes.
    """
    agent = Musicinjo()

    print("\n  Seeding archive with Oslo Magic...\n")

    # Save the Oslo Magic song
    oslo = agent.save_song(
        title="Oslo Magic",
        lyrics=(
            "Walkin' through Aker Brygge in the morning light\n"
            "Fjord on my left, the city feelin' right\n"
            "Trams roll slow like a riddim in my soul\n"
            "Oslo got a magic, yeah it's takin' me whole\n\n"
            "Oslo, Oslo — magic in the air\n"
            "Floatin' through the city like I got no care\n"
            "Dub & bass & neon on the street\n"
            "Feel the Viking riddim, feel the northern beat\n\n"
            "Grünerløkka glowin' under twilight skies\n"
            "Every corner turning into paradise\n"
            "The bass drops low, the four-four kicks in\n"
            "Oslo pulling me deeper, let the journey begin"
        ),
        genre="Dub Pop / Techno House",
        mood="euphoric, dreamy, magical",
        bpm=90,
        vibe_tags=["Oslo", "fjord", "Nordic", "magic", "city travel", "dub", "house drop"],
        influences=["Bob Marley", "Massive Attack", "Dennis Bovell"],
        theme="Traveling through the magical city of Oslo",
        notes="Bridge is instrumental — pure dub echo + house kick build. Key: major.",
    )

    song_id = oslo["id"]

    # Save Suno prompt
    agent.save_suno_prompt(
        song_id=song_id,
        prompt_text=(
            "dub reggae, Bob Marley influence, pop crossover, melodic techno, "
            "deep house pulse, reverb-heavy bass, off-beat skank guitar, dreamy delay effects, "
            "hypnotic groove, uplifting vocals, urban magic, Nordic mysticism, city adventure, "
            "90 BPM, major key, lush reverb tails, four-on-the-floor kick, "
            "reggae guitar chops, synthesizer pads, euphoric drop"
        ),
        version_label="v1 original",
        energy_level="euphoric",
    )

    # Save Hive System notes
    agent.save_hive_note(song_id, "bass",   "Dub bass must sit below 80Hz — heavy, slow, rubbery. Request 'dub sub bass, delay tail on every note' if Suno runs thin.", priority="high")
    agent.save_hive_note(song_id, "guitar", "Reggae skank must hit on the offbeat (2 & 4). Add 'offbeat skank guitar, upstroke chop' if Suno pushes it downbeat.", priority="high")
    agent.save_hive_note(song_id, "drop",   "House drop should hit after the bridge. Use Suno tag [big drop] [four-on-the-floor] right after the bridge section.", priority="medium")
    agent.save_hive_note(song_id, "feel",   "If Nordic mysticism is lost — add 'icy synth pads, fjord atmosphere, cold air reverb' on next Suno generation pass.", priority="medium")

    # Save mood profile
    agent.save_mood_profile(
        name="Oslo Magical",
        keywords=["city travel", "euphoric", "dreamy", "Nordic", "fjord", "magic"],
        suno_tags=["Nordic mysticism", "icy synth pads", "urban magic", "fjord atmosphere", "dreamy delay"],
        color="#00CED1",
        description="The feeling of wandering Oslo's streets in a state of pure wonder.",
    )

    print()
    agent.display_song(oslo)
    print()
    agent.display_hive_notes(song_id)
    print()
    agent.display_all_songs()

    # Export
    export_path = agent.export_song_package(song_id)
    print(f"\n  ♪ Full package exported → {export_path}")
    print("\n  Musicinjo is ready. The archive lives. The music never forgets. 🎵\n")


# ── Entry Point ───────────────────────────────────────────────────────

if __name__ == "__main__":
    demo()
