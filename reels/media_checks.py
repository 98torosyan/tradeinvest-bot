"""Local, quota-free checks and helpers for stock footage:
scene-cut detection (PySceneDetect), smart crop (smartcrop), text (RapidOCR) and face (OpenCV) detection,
and per-module colour LUTs."""
import functools
import os
import subprocess
import tempfile

import numpy as np


# ---------- clean segments without internal cuts ----------
def cuts(path):
    try:
        from scenedetect import detect, ContentDetector
        return [s[0].get_seconds() for s in detect(path, ContentDetector(threshold=27.0))[1:]]
    except Exception as exc:  # noqa: BLE001
        print("[scenes]", exc); return []


def clean_start(path, need, duration):
    """Earliest start (>=0.3 s) so that [start, start+need] contains no scene cut."""
    bounds = [0.0] + cuts(path) + [duration]
    best = None
    for a, b in zip(bounds, bounds[1:]):
        if b - a >= need + 0.3:
            best = a + 0.3 if a > 0 else min(0.8, max(0.0, b - need - 0.1)); break
    return best if best is not None else min(0.8, max(0.0, duration - need - 0.1))


# ---------- smart crop for landscape clips ----------
def smart_x(frame_path):
    """Horizontal centre (0..1) of the most interesting 9:16 window in a frame."""
    try:
        from PIL import Image
        import smartcrop
        im = Image.open(frame_path).convert("RGB")
        w, h = im.size
        if w <= h * 0.6:                 # already portrait
            return 0.5
        small = im.resize((max(1, w // 4), max(1, h // 4)))
        cw = int(small.size[1] * 9 / 16)
        r = smartcrop.SmartCrop().crop(small, cw, small.size[1])["top_crop"]
        return min(1.0, max(0.0, (r["x"] + r["width"] / 2) / small.size[0]))
    except Exception as exc:  # noqa: BLE001
        print("[smartcrop]", exc); return 0.5


# ---------- local content flags ----------
@functools.lru_cache(maxsize=1)
def _ocr():
    try:
        from rapidocr_onnxruntime import RapidOCR
        return RapidOCR()
    except Exception as exc:  # noqa: BLE001
        print("[ocr] unavailable:", exc); return None


def local_flags(frame_path):
    """{'text': bool, 'face': bool} from local models, or None if they are unavailable."""
    try:
        import cv2
    except ImportError:
        return None
    img = cv2.imread(frame_path)
    if img is None:
        return None
    h, w = img.shape[:2]
    face = False
    try:
        casc = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml"))
        g = cv2.cvtColor(cv2.resize(img, (w // 2, h // 2)), cv2.COLOR_BGR2GRAY)
        face = len(casc.detectMultiScale(g, 1.15, 6, minSize=(40, 40))) > 0
        if not face:
            prof = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades, "haarcascade_profileface.xml"))
            face = len(prof.detectMultiScale(g, 1.15, 6, minSize=(40, 40))) > 0 or \
                len(prof.detectMultiScale(cv2.flip(g, 1), 1.15, 6, minSize=(40, 40))) > 0
    except Exception:  # noqa: BLE001
        pass
    text = False
    ocr = _ocr()
    if ocr is not None:
        try:
            res, _ = ocr(frame_path, use_cls=False)
            area = sum(abs((b[0][2][0] - b[0][0][0]) * (b[0][2][1] - b[0][0][1])) for b in (res or []) if b[2] > 0.6)
            text = bool(res) and (len([b for b in res if b[2] > 0.6]) >= 2 or area > 0.01 * w * h)
        except Exception as exc:  # noqa: BLE001
            print("[ocr]", exc)
    return {"text": text, "face": face}


# ---------- per-module colour grade (3D LUT) ----------
def _hex(c):
    c = c.lstrip("#"); return np.array([int(c[i:i + 2], 16) / 255 for i in (0, 2, 4)])


def lut_for(palette, size=17):
    """Soft S-curve, slightly lower saturation, shadows tinted to the module colour, highlights kept clean."""
    path = os.path.join(tempfile.gettempdir(), f"lut_{palette['name']}.cube")
    if os.path.exists(path):
        return path
    shadow = _hex(palette["bg"].split("#", 1)[1][:6]) * 1.6
    accent = _hex(palette["a"])
    g = np.linspace(0, 1, size)
    lines = [f"TITLE \"{palette['name']}\"", f"LUT_3D_SIZE {size}"]
    for b in g:
        for gg in g:
            for r in g:
                c = np.array([r, gg, b])
                l = c @ np.array([0.299, 0.587, 0.114])
                c = l + (c - l) * 0.86                                   # saturation
                c = c + (c - 0.5) * 0.12 * (1 - np.abs(c - 0.5) * 2)       # gentle S-curve
                sw = (1 - l) ** 2.2 * 0.22
                c = c * (1 - sw) + shadow * sw                           # shadows toward module colour
                c = c + (accent - 0.5) * 0.03 * l                        # hint of accent in highlights
                lines.append(" ".join(f"{v:.5f}" for v in np.clip(c, 0, 1)))
    open(path, "w").write("\n".join(lines))
    return path
