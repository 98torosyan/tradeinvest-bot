"""
Generates a soft, original ambient/corporate-style background pad for
Reels, entirely synthesized with numpy (no downloaded audio file, so
there is zero copyright/licensing risk and no network dependency).
It is layered *under* the narration at low volume in reel_video.py --
and used on its own when TTS narration isn't available, so a Reel is
never fully silent.
"""
import wave
import numpy as np

SAMPLE_RATE = 44100

# A calm 4-chord progression (Am - F - C - G), each chord as its
# component frequencies in Hz -- a common, pleasant "premium/fintech"
# background progression.
PROGRESSION = [
    [220.00, 261.63, 329.63],   # Am
    [174.61, 220.00, 261.63],   # F
    [261.63, 329.63,392.00],   # C
    [196.00, 246.94,293.66],   # G
]
CHORD_SECONDS = 4.0
CROSSFADE_SECONDS = 0.6


def _chord_wave(freqs, t):
    wave_sum = np.zeros_like(t)
    for i, f in enumerate(freqs):
        # slightly detune/soften harmonics so it doesn't sound like a pure test tone
        wave_sum += np.sin(2 * np.pi * f * t) / (i + 1.4)
    return wave_sum / len(freqs)


def generate_background_music(duration_seconds, out_path, volume=0.18):
    duration_seconds = max(duration_seconds, 1.0)
    n_samples = int(SAMPLE_RATE * duration_seconds)
    t_full = np.arange(n_samples) / SAMPLE_RATE

    signal = np.zeros(n_samples)
    n_chords = len(PROGRESSION)
    chord_idx = 0
    pos = 0.0
    while pos < duration_seconds:
        chord = PROGRESSION[chord_idx % n_chords]
        seg_len = min(CHORD_SECONDS, duration_seconds - pos)
        start = int(pos * SAMPLE_RATE)
        end = int((pos + seg_len) * SAMPLE_RATE)
        t_seg = t_full[start:end]
        seg = _chord_wave(chord, t_seg)

        # crossfade into the previous chord so transitions are smooth, not clicky
        fade_len = int(CROSSFADE_SECONDS * SAMPLE_RATE)
        if start > 0 and fade_len > 0:
            ramp = np.linspace(0, 1, min(fade_len, len(seg)))
            seg[: len(ramp)] *= ramp

        signal[start:end] += seg
        pos += CHORD_SECONDS
        chord_idx += 1

    # overall soft envelope: fade in/out so the track never starts/stops abruptly
    fade_samples = int(min(1.5, duration_seconds / 4) * SAMPLE_RATE)
    if fade_samples > 0:
        envelope = np.ones(n_samples)
        envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
        envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
        signal *= envelope

    peak = np.max(np.abs(signal)) or 1.0
    signal = (signal / peak) * volume
    pcm = np.int16(signal * 32767)

    with wave.open(out_path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm.tobytes())

    return out_path
