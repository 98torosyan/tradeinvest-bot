"""
Generates narration audio for a Reel script using Microsoft Edge's
free neural voices (via the unofficial `edge-tts` package -- no API
key needed). Armenian neural voices exist ("hy-AM-AnahitNeural" /
"hy-AM-HaykNeural"); this could not be verified from inside this
sandbox because its network egress is restricted to package
registries only (see the README's "known limitations" section), so
it is wrapped in a broad fallback: if TTS fails for any reason
(voice unavailable, network hiccup, rate limit), the pipeline simply
produces the Reel without a voice-over instead of crashing --
still a fully usable, text-driven Reel.

Also captures edge-tts's per-word "WordBoundary" timing events, so
video/reel_video.py can size each on-screen script-line card to
exactly how long that line is actually being spoken (real burned-in
sync), instead of splitting the narration's total length evenly
across cards. This boundary capture is likewise unverified live (same
sandbox restriction) -- video/reel_video.py falls back to the old
even-split timing if boundaries are missing, empty, or don't roughly
match the script's word count, so a Reel is never broken by it.
"""
import asyncio
import os

PRIMARY_VOICE = "hy-AM-AnahitNeural"
FALLBACK_VOICE = "hy-AM-HaykNeural"


async def _synthesize(text, out_path, voice, capture_boundaries):
    import edge_tts
    communicate = edge_tts.Communicate(text, voice)
    if not capture_boundaries:
        await communicate.save(out_path)
        return []

    boundaries = []
    with open(out_path, "wb") as fh:
        async for chunk in communicate.stream():
            if chunk.get("type") == "audio":
                fh.write(chunk["data"])
            elif chunk.get("type") == "WordBoundary":
                # offset/duration arrive in 100-nanosecond units.
                boundaries.append({
                    "text": chunk.get("text", ""),
                    "start": chunk["offset"] / 10_000_000,
                    "end": (chunk["offset"] + chunk["duration"]) / 10_000_000,
                })
    return boundaries


def generate_narration(text, out_path):
    """Returns out_path on success, or None if narration could not be produced."""
    path, _ = generate_narration_with_boundaries(text, out_path)
    return path


def generate_narration_with_boundaries(text, out_path):
    """Returns (out_path, boundaries) on success -- boundaries is a list
    of {"text", "start", "end"} (seconds, relative to the audio's own
    start), or [] if the voice/edge-tts version didn't provide them.
    Returns (None, None) if narration could not be produced at all."""
    if not text.strip():
        return None, None
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    for voice in (PRIMARY_VOICE, FALLBACK_VOICE):
        try:
            boundaries = asyncio.run(_synthesize(text, out_path, voice, capture_boundaries=True))
            if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
                return out_path, boundaries
        except Exception as exc:
            print(f"[tts] voice {voice} failed: {exc}")
    print("[tts] no narration voice succeeded; Reel will be produced silently")
    return None, None
