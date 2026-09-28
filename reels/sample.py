"""Renders a preview of the new B-roll lesson style (with voice) and a few
voice samples to docs/samples/ -- nothing is published to Instagram."""
import json
import os
import subprocess
import sys

from . import broll, gemini, palettes, render

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "samples")
VOICES = ["Charon", "Orus", "Kore", "Sulafat"]
LINE = "Բարև, սա TradeInvest-ն է։ Այսօր կսովորենք, թե ինչպես է ձևավորվում գինը։"


def main():
    os.makedirs(OUT, exist_ok=True)
    notes = []
    spec = json.load(open(os.path.join(os.path.dirname(__file__), "lesson_broll_sample.json"), encoding="utf-8"))
    tracks = render.music_tracks("lesson")
    music = next((t for t in tracks if "delayed" in t), tracks[0] if tracks else None)
    voice = os.environ.get("SAMPLE_VOICE", "Charon")
    for with_voice in (True, False):
        name = "lesson2_broll_voice.mp4" if with_voice else "lesson2_broll_novoice.mp4"
        total, used = broll.render_broll(spec, palettes.LESSON[0], os.path.join(OUT, name), music=music,
                                         voice=voice if with_voice else None, notes=notes)
        notes.append(f"{name}: {total:.1f}s, pexels clips {used}")
        notes += [n for n in __import__("reels.pexels", fromlist=["NOTES"]).NOTES]
    for v in VOICES:
        try:
            wav = gemini.tts(LINE, v, os.path.join(OUT, f"voice_{v}.wav"))
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-b:a", "128k",
                            os.path.join(OUT, f"voice_{v}.mp3")], check=True)
            os.remove(wav); notes.append(f"voice {v}: ok")
        except Exception as exc:  # noqa: BLE001
            notes.append(f"voice {v}: FAILED {str(exc)[:200]}")
    with open(os.path.join(OUT, "notes.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(notes))
    print("\n".join(notes))


if __name__ == "__main__":
    sys.exit(main())
