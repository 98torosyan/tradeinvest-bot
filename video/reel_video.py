"""
Assembles a finished vertical (1080x1920) Reel .mp4 from:
  - a hook card
  - a branded chart frame
  - one card per script point
  - an outro/CTA card
  - narration audio (if TTS succeeded)

When edge-tts returns per-word timing ("WordBoundary" events -- see
video/tts.py), each script-line card is sized to exactly how long
that line is actually spoken (real burned-in sync), and the narration
track is time-shifted to start right when the first script-line card
appears (after the hook + chart cards). If timing isn't available or
doesn't line up with the script (unverified in this sandbox -- see
tts.py), this falls back to the original, safe even-split timing with
narration starting at t=0, so a Reel is never broken by it.
"""
import os
from moviepy import ImageClip, concatenate_videoclips, AudioFileClip, CompositeAudioClip

from video import frames, tts, music

FPS = 24
MIN_CARD_SECONDS = 1.2


def build_reel(reel_plan, chart_image_path, out_dir, filename="reel.mp4", chip_pct=None, breaking_headline=None):
    os.makedirs(out_dir, exist_ok=True)

    hook_path = frames.render_hook_card(
        reel_plan["hook"], os.path.join(out_dir, "hook.png"),
        chip_pct=chip_pct, breaking_headline=breaking_headline,
    )
    chart_path = frames.render_chart_frame(
        chart_image_path, os.path.join(out_dir, "chart.png"), caption=reel_plan["on_screen_text"],
    )
    point_paths = [
        frames.render_point_card(pt, os.path.join(out_dir, f"point_{i}.png"), eyebrow=f"{i+1}")
        for i, pt in enumerate(reel_plan["script"])
    ]
    outro_path = frames.render_outro_card(reel_plan["cta"], os.path.join(out_dir, "outro.png"))

    image_sequence = [hook_path, chart_path] + point_paths + [outro_path]

    narration_text = " ".join(reel_plan["script"])
    audio_path, boundaries = tts.generate_narration_with_boundaries(
        narration_text, os.path.join(out_dir, "narration.mp3"),
    )

    audio_len = None
    if audio_path:
        try:
            audio_len = AudioFileClip(audio_path).duration
        except Exception:
            audio_len = None

    line_durations = None
    if audio_len:
        line_durations = _line_windows_from_boundaries(reel_plan["script"], boundaries, audio_len)

    narration_offset = 0.0
    if line_durations is not None:
        # Precise path: hook + chart play silently, narration starts
        # exactly when the first script-line card appears.
        head_each = max(MIN_CARD_SECONDS, min(1.8, audio_len * 0.08))
        durations = [head_each, head_each] + line_durations + [max(2.0, MIN_CARD_SECONDS)]
        narration_offset = 2 * head_each
    else:
        durations = _compute_durations(image_sequence, audio_path, audio_len)

    clips = [ImageClip(p).with_duration(d) for p, d in zip(image_sequence, durations)]
    video = concatenate_videoclips(clips, method="compose")

    if audio_path:
        narration = AudioFileClip(audio_path)
        if narration_offset:
            video = video.with_duration(narration_offset + narration.duration + 0.6)
        else:
            video = video.with_duration(min(video.duration, narration.duration + 0.6))
    else:
        narration = None

    # Background music: synthesized (no download, no licensing risk -- see
    # video/music.py), layered quietly under the narration so a Reel never
    # feels dead-silent between spoken lines; on its own (full volume) when
    # TTS produced no narration at all.
    music_path = os.path.join(out_dir, "music.wav")
    music.generate_background_music(video.duration, music_path,
                                     volume=0.10 if audio_path else 0.35)
    bg = AudioFileClip(music_path)

    if narration is not None:
        narration_positioned = narration.with_start(narration_offset) if narration_offset else narration
        final_audio = CompositeAudioClip([bg, narration_positioned])
    else:
        final_audio = bg
    video = video.with_audio(final_audio)

    out_path = os.path.join(out_dir, filename)
    video.write_videofile(
        out_path, fps=FPS, codec="libx264", audio_codec="aac",
        logger=None,
    )
    return out_path


def _line_windows_from_boundaries(script_lines, boundaries, audio_duration):
    """Maps edge-tts word-boundary events back to each script line by
    consuming that line's word count worth of consecutive boundaries,
    then converts word-onset times into onset-to-onset card durations
    (so pauses between sentences are absorbed into the preceding
    card, and the cards' total exactly matches the narration length).
    Returns None (triggering the safe even-split fallback) if the
    boundary count doesn't roughly match the script's word count --
    edge-tts's Armenian word segmentation was never verified live in
    this sandbox, so a mismatch is treated as "don't trust this"
    rather than silently mis-syncing the captions."""
    if not boundaries:
        return None
    word_counts = [max(len(line.split()), 1) for line in script_lines]
    total_expected = sum(word_counts)
    if total_expected == 0 or abs(len(boundaries) - total_expected) > max(3, int(total_expected * 0.25)):
        return None

    onsets = []
    idx = 0
    for wc in word_counts:
        chunk = boundaries[idx:idx + wc]
        idx += wc
        if not chunk:
            return None
        onsets.append(chunk[0]["start"])

    durations = []
    for i, onset in enumerate(onsets):
        nxt = onsets[i + 1] if i + 1 < len(onsets) else audio_duration
        durations.append(max(nxt - onset, MIN_CARD_SECONDS))
    return durations


def _compute_durations(image_sequence, audio_path, audio_len):
    """Original, safe fallback: spread the narration's total length
    evenly across the "middle" cards (chart + script points), with a
    fixed head/tail for the hook and outro cards. Used whenever
    per-line boundary timing isn't available or can't be trusted."""
    n = len(image_sequence)
    if audio_len:
        head_tail = min(2.2, audio_len * 0.15)
        remaining = max(audio_len - 2 * head_tail, MIN_CARD_SECONDS * (n - 2))
        middle = remaining / max(n - 2, 1)
        return [head_tail] + [middle] * (n - 2) + [head_tail]

    # no audio at all: fixed, generous per-card timing so text is readable
    return [2.4] + [2.6] * (n - 2) + [2.6]
