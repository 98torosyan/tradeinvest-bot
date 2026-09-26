"""Minimal Gemini REST client (free tier key from aistudio.google.com).
Retries on rate limits / server errors and falls back to other free models."""
import json
import os
import time

import requests

URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def _models():
    first = os.environ.get("GEMINI_MODEL", "").strip()
    base = ["gemini-flash-latest", "gemini-2.5-flash", "gemini-flash-lite-latest"]
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
