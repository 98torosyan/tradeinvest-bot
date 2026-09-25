"""Renders an HTML composition to MP4: headless Chromium screenshots every
frame (window.seek(t)), ffmpeg encodes them and mixes in background music."""
import glob
import os
import shutil
import subprocess
import tempfile

from playwright.sync_api import sync_playwright

FPS = int(os.environ.get("REEL_FPS", "30"))
MUSIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "music")


def music_tracks(kind):
    files = sorted(glob.glob(os.path.join(MUSIC_DIR, kind, "*.mp3")) + glob.glob(os.path.join(MUSIC_DIR, kind, "*.wav")))
    return files


def render(html, out_mp4, music=None):
    work = tempfile.mkdtemp(prefix="reel_")
    page_path = os.path.join(work, "page.html")
    with open(page_path, "w", encoding="utf-8") as f:
        f.write(html)
    frames = os.path.join(work, "frames"); os.makedirs(frames)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        pg = browser.new_page(viewport={"width": 1080, "height": 1920})
        pg.goto(f"file://{page_path}")
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(400)
        duration = float(pg.evaluate("DURATION"))
        n = int(round(duration * FPS))
        for i in range(n):
            pg.evaluate(f"seek({i / FPS})")
            pg.screenshot(path=os.path.join(frames, f"{i:05d}.jpg"), type="jpeg", quality=92)
        browser.close()
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(frames, "%05d.jpg")]
    if music:
        fade_out = max(0.0, duration - 2.0)
        cmd += ["-stream_loop", "-1", "-i", music, "-filter_complex",
                f"[1:a]atrim=0:{duration:.2f},asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.6,afade=t=out:st={fade_out:.2f}:d=2,"
                f"loudnorm=I=-16:TP=-1.5:LRA=11[a]", "-map", "0:v", "-map", "[a]", "-c:a", "aac", "-b:a", "192k"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
            "-t", f"{duration:.2f}", "-movflags", "+faststart", out_mp4]
    subprocess.run(cmd, check=True)
    shutil.rmtree(work, ignore_errors=True)
    return duration
