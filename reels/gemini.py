"""Minimal Gemini REST client (free tier key from aistudio.google.com).
Retries on rate limits / server errors and falls back to other free models."""
import json
import os
import time

import requests

URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def _models():
    first = os.environ.get("GEMINI_MODEL", "").strip()
    base = ["gemini-flash-latest", "gemini-flash-lite-latest"]
    return ([first] if first else []) + [m for m in base if m != first]


def _extract_json(text):
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(text)
    except ValueError:
        a, b = text.find("{"), text.rfind("}")
        if a >= 0 and b > a:
            return json.loads(text[a:b + 1])
        raise


def generate_json(prompt, temperature=0.4):
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature, "responseMimeType": "application/json"}}
    errors = []
    for model in _models():
        for attempt in range(3):
            try:
                r = requests.post(URL.format(model=model), headers={"x-goog-api-key": key}, json=body, timeout=120)
            except requests.RequestException as exc:
                errors.append(f"{model}: {exc}"); time.sleep(5); continue
            if r.status_code in (429, 500, 502, 503, 504):
                errors.append(f"{model}: HTTP {r.status_code}"); time.sleep(10 * (attempt + 1)); continue
            if r.status_code != 200:
                errors.append(f"{model}: HTTP {r.status_code} {r.text[:200]}"); break  # try next model
            try:
                cand = r.json()["candidates"][0]
                text = "".join(p.get("text", "") for p in cand["content"]["parts"])
                return _extract_json(text)
            except (KeyError, IndexError, ValueError) as exc:
                errors.append(f"{model}: bad response ({exc})"); time.sleep(3)
    raise RuntimeError("Gemini failed: " + " | ".join(errors[-4:]))


# ---------------- text-to-speech ----------------
TTS_MODELS = [m for m in [os.environ.get("GEMINI_TTS_MODEL"), "gemini-3.8-flash-lite-tts", "gemini-3.8-flash-tts",
                          "gemini-3.1-flash-tts-preview", "gemini-2.5-flash-preview-tts"] if m]
TTS_STYLE = ("Read the following Armenian text aloud in natural Eastern Armenian, like a calm, confident, friendly "
             "educator on a finance channel. Clear pronunciation, natural pace, no exaggeration:\n")


def tts(text, voice="Charon", out_wav=None):
    """Returns path to a 24 kHz mono WAV, or raises."""
    import base64, time, wave as _wave
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    body = {"contents": [{"role": "user", "parts": [{"text": TTS_STYLE + text}]}],
            "generationConfig": {"responseModalities": ["AUDIO"],
                                 "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}}}}
    last = ""
    for model in TTS_MODELS:
        for attempt in range(4):
            r = requests.post(URL.format(model=model), headers={"x-goog-api-key": key}, json=body, timeout=180)
            if r.status_code == 429:
                time.sleep(12 * (attempt + 1)); continue
            break
        if r.status_code != 200:
            last = f"TTS {model} HTTP {r.status_code}: {r.text[:200]}"
            print("[tts]", last)
            continue
        try:
            part = next(p for p in r.json()["candidates"][0]["content"]["parts"] if "inlineData" in p)
        except (KeyError, IndexError, StopIteration):
            last = f"TTS {model}: no audio in response"; continue
        pcm = base64.b64decode(part["inlineData"]["data"])
        rate = 24000
        mime = part["inlineData"].get("mimeType", "")
        if "rate=" in mime:
            try:
                rate = int(mime.split("rate=")[1].split(";")[0])
            except ValueError:
                pass
        out_wav = out_wav or os.path.join(os.getcwd(), "tts.wav")
        with _wave.open(out_wav, "w") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate); w.writeframes(pcm)
        print(f"[tts] {model} voice={voice} ok ({len(pcm) / 2 / rate:.1f}s)")
        return out_wav
    raise RuntimeError(last or "TTS failed")


# ---------------- vision check for stock footage ----------------
def frame_flags(image_path):
    """Asks Gemini whether a still frame shows readable text, a brand logo or an
    identifiable human face. Returns a dict, or None if the check could not run."""
    import base64
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        return None
    img = base64.b64encode(open(image_path, "rb").read()).decode()
    prompt = ('Look at this video frame. Answer ONLY JSON: {"text": bool, "logo": bool, "face": bool} where '
              'text = clearly readable words or numbers, logo = a recognisable brand logo or trademark, '
              'face = a human face that could identify a person.')
    body = {"contents": [{"role": "user", "parts": [{"inline_data": {"mime_type": "image/jpeg", "data": img}},
                                                   {"text": prompt}]}],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json"}}
    for model in ["gemini-flash-lite-latest"]:          # cheap model, one try: quota is kept for news and comments
        try:
            r = requests.post(URL.format(model=model), headers={"x-goog-api-key": key}, json=body, timeout=60)
            if r.status_code != 200:
                continue
            txt = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            d = json.loads(txt.strip().removeprefix("```json").removesuffix("```").strip())
            return {k: bool(d.get(k)) for k in ("text", "logo", "face")}
        except Exception:  # noqa: BLE001
            continue
    return None
