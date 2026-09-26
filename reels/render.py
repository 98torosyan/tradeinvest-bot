"""Renders an HTML composition to MP4: headless Chromium screenshots every
frame (window.seek(t)), ffmpeg encodes them, optionally lays them over a
tinted background video, and mixes in background music."""
import glob
import os
import shutil
import subprocess
import tempfile

from playwright.sync_api import sync_playwright

FPS = int(os.environ.get("REEL_FPS", "30"))
MUSIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "music")


def music_tracks(kind):
    return sorted(glob.glob(os.path.join(MUSIC_DIR, kind, "*.mp3")) + glob.glob(os.path.join(MUSIC_DIR, kind, "*.wav")))


def _frames(html, work, transparent):
    page_path = os.path.join(work, "page.html")
    with open(page_path, "w", encoding="utf-8") as f:
        f.write(html)
    frames = os.path.join(work, "frames"); os.makedirs(frames)
    ext = "png" if transparent else "jpg"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        pg = browser.new_page(viewport={"width": 1080, "height": 1920})
        pg.goto(f"file://{page_path}")
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(400)
        duration = float(pg.evaluate("DURATION"))
        for i in range(int(round(duration * FPS))):
            pg.evaluate(f"seek({i / FPS})")
            path = os.path.join(frames, f"{i:05d}.{ext}")
            if transparent:
                pg.screenshot(path=path, type="png", omit_background=True)
            else:
                pg.screenshot(path=path, type="jpeg", quality=92)
        browser.close()
    return os.path.join(frames, f"%05d.{ext}"), duration


def render(html, out_mp4, music=None, background=None, tint="#07101F"):
    """background: optional path to a video placed (slowed, desaturated,
    darkened with the palette colour) behind the transparent frames."""
    work = tempfile.mkdtemp(prefix="reel_")
    pattern, duration = _frames(html, work, transparent=bool(background))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", pattern]
    filters, vmap, idx = [], "0:v", 1
    if background:
        cmd += ["-stream_loop", "-1", "-i", background]
        filters.append(
            f"[{idx}:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setpts=1.3*PTS,fps={FPS},"
            f"eq=saturation=0.55:brightness=-0.05,gblur=sigma=1.2,trim=0:{duration:.2f},setpts=PTS-STARTPTS[bg];"
            f"color=c={tint}@0.66:s=1080x1920:r={FPS}:d={duration:.2f}[tint];"
            f"[bg][tint]overlay=shortest=1[bgt];[bgt][0:v]overlay=shortest=1:format=auto[v]")
        vmap = "[v]"; idx += 1
    if music:
        cmd += ["-stream_loop", "-1", "-i", music]
        fade_out = max(0.0, duration - 2.0)
        filters.append(f"[{idx}:a]atrim=0:{duration:.2f},asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.6,"
                       f"afade=t=out:st={fade_out:.2f}:d=2,loudnorm=I=-16:TP=-1.5:LRA=11[a]")
    if filters:
        cmd += ["-filter_complex", ";".join(filters)]
    cmd += ["-map", vmap]
    if music:
        cmd += ["-map", "[a]", "-c:a", "aac", "-b:a", "192k"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
            "-t", f"{duration:.2f}", "-movflags", "+faststart", out_mp4]
    subprocess.run(cmd, check=True)
    shutil.rmtree(work, ignore_errors=True)
    return duration


def make_teaser(reel_mp4, overlay_html, out_mp4, seconds=12.0):
    """First seconds of a Reel + a 'watch the full video on the page' badge -> Story."""
    work = tempfile.mkdtemp(prefix="teaser_")
    page = os.path.join(work, "o.html"); png = os.path.join(work, "o.png")
    with open(page, "w", encoding="utf-8") as f:
        f.write(overlay_html)
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1920})
        pg.goto(f"file://{page}"); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(300)
        pg.screenshot(path=png, omit_background=True); b.close()
    has_audio = bool(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
                                     "-of", "csv=p=0", reel_mp4], capture_output=True, text=True).stdout.strip())
    fc = "[1:v]format=rgba,fade=t=in:st=1.0:d=0.5:alpha=1[o];[0:v][o]overlay=shortest=1[v]"
    maps = ["-map", "[v]"]
    if has_audio:
        fc += f";[0:a]afade=t=out:st={seconds - 1.5:.2f}:d=1.5[a]"
        maps += ["-map", "[a]", "-c:a", "aac", "-b:a", "160k"]
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", reel_mp4, "-loop", "1", "-i", png, "-filter_complex", fc,
                    *maps, "-t", f"{seconds:.2f}", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart", out_mp4], check=True)
    shutil.rmtree(work, ignore_errors=True)
